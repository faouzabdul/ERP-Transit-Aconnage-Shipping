# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from . import utils
import logging
from odoo.exceptions import UserError, ValidationError
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    transport_means_id = fields.Many2one('res.transport.means', string="Means of transportation")
    travel_date = fields.Date('Travel Date')
    loading_place_id = fields.Many2one('res.locode', string='Loading place')
    unloading_place_id = fields.Many2one('res.locode', string='Unloading place')
    transport_letter = fields.Char('N° BL / N° LTA', index=True)
    volume = fields.Float('Volume (m3)', digits=(12, 3))
    weight = fields.Float('Weight', digits=(12, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')
    custom_declaration_reference = fields.Char('Custom Declaration Reference')
    custom_declaration_date = fields.Date('Custom Declaration Date')
    assessed_value = fields.Float('Assessed Value', digits=(12, 3), help='Valeur imposable')
    object = fields.Text('Object')
    number_of_packages = fields.Char('Number of packages/TC')
    amount_total_letter = fields.Char('Total letter', compute='_compute_display_amount_letter',
                                      store=False)
    other_currency_id = fields.Many2one('res.currency', 'Other Currency')
    amount_other_currency = fields.Float(string='Total Currency', store=False, digits=(6, 3),
                                         compute='_compute_display_amount_letter')

    @api.depends('amount_total', 'currency_id')
    def _compute_display_amount_letter(self):
        for order in self:
            order.amount_total_letter = utils.translate(order.amount_total).upper()
            currency_code = 'XAF'
            if order.currency_id.name == 'XAF':
                currency_code = 'EUR'
            other_currency = self.env['res.currency'].search([('name', '=', currency_code)])
            rate = other_currency.rate if currency_code == 'EUR' else other_currency.inverse_rate
            order.other_currency_id = other_currency and other_currency.id
            order.amount_other_currency = order.amount_total * rate

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)
        for order in self:
            for move in moves:
                move.write({
                    'transport_means_id': order.transport_means_id.id,
                    'travel_date': order.travel_date,
                    'loading_place_id': order.loading_place_id.id,
                    'unloading_place_id': order.unloading_place_id.id,
                    'transport_letter': order.transport_letter,
                    'volume': order.volume,
                    'weight': order.weight,
                    'custom_declaration_reference': order.custom_declaration_reference,
                    'custom_declaration_date': order.custom_declaration_date,
                    'assessed_value': order.assessed_value,
                    'object': order.object
                })

    def _compute_line_data_for_template_change(self, line):
        return {
            'sequence': line.sequence,
            'display_type': line.display_type,
            'name': line.name,
            'state': 'draft',
        }

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
            'VOLUME': self.volume,
            'TONNAGE': self.weight,
            'rules': rules
        }
        return dict(var_dict)

    def _get_template_lines(self, template_id, localdict):
        order_lines = [(5, 0, 0)]
        template = self.env['sale.order.template'].browse(template_id)
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            if line.product_id:
                amount, qty = line._compute_rule(localdict)
                if line.code:
                    total_rule = amount * qty
                    localdict[line.code] = total_rule
                    localdict = self._sum_rule_amount(localdict, line, total_rule)
                price = amount
                discount = 0
                data.update({
                    'price_unit': price,
                    'discount': discount,
                    'product_uom_qty': qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                })
            order_lines.append((0, 0, data))
        self.order_line = order_lines
        self.order_line._compute_tax_id()

    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        # if template:
        #     self.volume = template.volume
        #     self.weight = template.weight
        localdict = self.init_dicts()
        self._get_template_lines(self.sale_order_template_id.id, localdict)
        if not is_html_empty(template.note):
            self.note = template.note

    @api.onchange('weight', 'volume')
    def onchange_variables(self):
        localdict = self.init_dicts()
        self._get_template_lines(self.sale_order_template_id.id, localdict)
