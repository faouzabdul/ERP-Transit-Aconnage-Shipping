# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import is_html_empty
import logging

_logger = logging.getLogger(__name__)


class ShippingPda(models.Model):
    _inherit = 'servoo.shipping.pda'

    @api.model
    def default_get(self, fields_list):
        default_vals = super(ShippingPda, self).default_get(fields_list)
        if "shipping_pda_template_id" in fields_list and not default_vals.get("shipping_pda_template_id"):
            company_id = default_vals.get('company_id', False)
            company = self.env["res.company"].browse(company_id) if company_id else self.env.company
            # default_vals['shipping_pda_template_id'] = company.shipping_pda_template_id.id
        return default_vals

    shipping_pda_template_id = fields.Many2one(
        'servoo.shipping.pda.template', 'PDA Template',
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if self.shipping_pda_template_id and self.shipping_pda_template_id.number_of_days > 0:
            default = dict(default or {})
            default['validity_date'] = fields.Date.context_today(self) + timedelta(self.shipping_pda_template_id.number_of_days)
        return super(ShippingPda, self).copy(default=default)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(ShippingPda, self).onchange_partner_id()
        template = self.shipping_pda_template_id.with_context(lang=self.partner_id.lang)
        self.note = template.note if not is_html_empty(template.note) else self.note

    def _compute_line_data_for_template_change(self, line):
        return {
            'sequence': line.sequence,
            'display_type': line.display_type,
            'name': line.name,
            'state': 'draft',
        }

    def update_prices(self):
        self.ensure_one()
        res = super().update_prices()
        return res

    @api.onchange('cbm_vessel', 'number_of_days', 'grt', 'tonnage_of_goods')
    def onchange_variables(self):
        localdict = self.init_dicts()
        self._get_template_lines(self.shipping_pda_template_id.id, localdict)

    def _sum_rule_amount(self, localdict, line, amount):
        _logger.info('line.code : %s = %s' % (line.code, amount))
        localdict['rules'].dict[line.code] = line.code in localdict['rules'].dict and localdict['rules'].dict[line.code] + amount or amount
        return localdict

    def init_dicts(self):
        class BrowsableObject(object):
            def __init__(self, dict, env):
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        rules_dict = {}
        rules = BrowsableObject(rules_dict, self.env)
        var_dict = {
            'CBM': self.cbm_vessel,
            'DAY': self.number_of_days,
            'GRT': self.grt,
            'TONNAGE': self.tonnage_of_goods,
            'rules': rules
        }
        return dict(var_dict)

    def _get_template_lines(self, pda_template_id, localdict):
        shipping_pda_lines = [(5, 0, 0)]
        template = self.env['servoo.shipping.pda.template'].browse(pda_template_id)
        for line in template.shipping_pda_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            if line.product_id:
                amount, qty = line._compute_rule(localdict)
                if line.code:
                    total_rule = amount * qty
                    localdict[line.code] = total_rule
                    localdict = self._sum_rule_amount(localdict, line, total_rule)
                    # localdict['rules'].dict[line.code] = amount
                price = amount
                # price = line.unit_price
                discount = 0
                data.update({
                    'price_unit': price,
                    'discount': discount,
                    # 'product_uom_qty': line.product_uom_qty,
                    'product_uom_qty': qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                })

            shipping_pda_lines.append((0, 0, data))
            # _logger.info('localdict[rules] : %s' % localdict['rules'])
        self.shipping_pda_line = shipping_pda_lines
        self.shipping_pda_line._compute_tax_id()

    @api.onchange('shipping_pda_template_id')
    def onchange_shipping_pda_template_id(self):
        template = self.shipping_pda_template_id.with_context(lang=self.partner_id.lang)
        if template:
            self.number_of_days = template.number_of_days
            self.grt = template.grt
            self.cbm_vessel = template.cbm_vessel
            self.tonnage_of_goods = template.tonnage
            self.currency_id = template.currency_id.id
        localdict = self.init_dicts()
        self._get_template_lines(self.shipping_pda_template_id.id, localdict)
        if not is_html_empty(template.note):
            self.note = template.note

    # def action_confirm(self):
    #     res = super(ShippingPda, self).action_confirm()
    #     if self.env.su:
    #         self = self.with_user(SUPERUSER_ID)
    #
    #     for order in self:
    #         if order.shipping_pda_template_id and order.shipping_pda_template_id.mail_template_id:
    #             order.shipping_pda_template_id.mail_template_id.send_mail(order.id)
    #     return res

    def get_access_action(self, access_uid=None):
        """ Instead of the classic form view, redirect to the online quote if it exists. """
        self.ensure_one()
        user = access_uid and self.env['res.users'].sudo().browse(access_uid) or self.env.user

        if not self.shipping_pda_template_id or (not user.share and not self.env.context.get('force_website')):
            return super(ShippingPda, self).get_access_action(access_uid)
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_portal_url(),
            'target': 'self',
            'res_id': self.id,
        }


class ShippingPdaLine(models.Model):
    _inherit = "servoo.shipping.pda.line"
    _description = "Shipping PDA Line"

    # Take the description on the order template if the product is present in it
    @api.onchange('product_id')
    def product_id_change(self):
        domain = super(ShippingPdaLine, self).product_id_change()
        if self.product_id and self.shipping_pda_id.shipping_pda_template_id:
            for line in self.shipping_pda_id.shipping_pda_template_id.shipping_pda_template_line_ids:
                if line.product_id == self.product_id:
                    self.name = line.with_context(lang=self.shipping_pda_id.partner_id.lang).name + self._get_shipping_pda_line_multiline_description_variants()
                    break
        return domain
