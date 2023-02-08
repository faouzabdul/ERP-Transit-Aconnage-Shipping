# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from . import utils
from odoo.tools import is_html_empty


class AccountMode(models.Model):
    _inherit = 'account.move'

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
    amount_total_signed_letter = fields.Char('Total Signed letter', compute='_compute_display_amount_letter',
                                               store=True)
    amount_total_in_currency_signed_letter = fields.Char('Total in Currency Signed letter', compute='_compute_display_amount_letter',
                                               store=True)

    other_currency_id = fields.Many2one('res.currency', 'Other Currency')
    amount_other_currency = fields.Float(string='Total Currency', store=True, digits=(6, 3),
                                         compute='_compute_display_amount_letter')
    agency_name = fields.Selection([
        ('Douala', 'Douala'),
        ('Kribi', 'Kribi'),
        ('Tchad', 'Tchad'),
    ], string='Agency', default='Douala')
    # sale_order_template_id = fields.Many2one(
    #     'sale.order.template', 'Invoice Template',
    #     readonly=True, check_company=True,
    #     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    department_id = fields.Many2one('hr.department', 'Department')
    observation = fields.Text('Observation', tracking=2)
    state = fields.Selection(selection_add=[
        ('direction_routing', 'Submitted'),
        ('department_approval', 'Department Approval'),
        ('direction_approval', 'Direction Approval'),
        ('accounting_approval', 'Accounting Approval'),
        ('management_control_approval', 'Management Control Approval'),
        ('in_payment', 'In payment'),
    ], ondelete={
        'direction_routing': 'cascade',
        'department_approval': 'cascade',
        'direction_approval': 'cascade',
        'accounting_approval': 'cascade',
        'management_control_approval': 'cascade',
        'in_payment': 'cascade',
    })
    invoice_line_ids = fields.One2many(states={'draft': [('readonly', False)],
                                               'direction_routing': [('readonly', False)],
                                               'department_approval': [('readonly', False)],
                                               'direction_approval': [('readonly', False)],
                                               'accounting_approval': [('readonly', False)],
                                               'management_control_approval': [('readonly', False)],
                                               })

    @api.depends('amount_total', 'currency_id')
    def _compute_display_amount_letter(self):
        for move in self:
            move.amount_total_signed_letter = utils.translate(move.amount_total_signed if move.amount_total_signed > -1 else (-1*move.amount_total_signed)).upper()
            move.amount_total_in_currency_signed_letter = utils.translate(move.amount_total_in_currency_signed if move.amount_total_in_currency_signed > -1 else (-1 * move.amount_total_in_currency_signed)).upper()
            currency_code = 'XAF'
            if move.currency_id.name == 'XAF':
                currency_code = 'EUR'
            other_currency = self.env['res.currency'].search([('name', '=', currency_code)])
            rate = other_currency.rate if currency_code == 'EUR' else other_currency.inverse_rate
            move.other_currency_id = other_currency and other_currency.id
            move.amount_other_currency = (move.amount_total_signed if move.amount_total_signed > -1 else -1*move.amount_total_signed) * rate

    def action_submit(self):
        return self.write({'state': 'direction_routing'})

    # def _compute_line_data_for_template_change(self, line):
    #     return {
    #         'sequence': line.sequence,
    #         'display_type': line.display_type,
    #         'name': line.name,
    #     }
    #
    # def _sum_rule_amount(self, localdict, line, amount):
    #     localdict['rules'].dict[line.code] = line.code in localdict['rules'].dict and localdict['rules'].dict[line.code] + amount or amount
    #     return localdict
    #
    # def init_dicts(self):
    #     class BrowsableObject(object):
    #         def __init__(self, dict, env):
    #             self.dict = dict
    #             self.env = env
    #
    #         def __getattr__(self, attr):
    #             return attr in self.dict and self.dict.__getitem__(attr) or 0.0
    #
    #     rules_dict = {}
    #     rules = BrowsableObject(rules_dict, self.env)
    #     var_dict = {
    #         'VOLUME': self.volume,
    #         'TONNAGE': self.weight,
    #         'rules': rules
    #     }
    #     return dict(var_dict)
    #
    # def _get_template_lines(self, template_id, localdict):
    #     invoice_lines = [(5, 0, 0)]
    #     template = self.env['sale.order.template'].browse(template_id)
    #     for line in template.sale_order_template_line_ids:
    #         data = self._compute_line_data_for_template_change(line)
    #         localdict['result'] = None
    #         localdict['result_qty'] = 1.0
    #         if line.product_id:
    #             amount, qty = line._compute_rule(localdict)
    #             if line.code:
    #                 total_rule = amount * qty
    #                 localdict[line.code] = total_rule
    #                 localdict = self._sum_rule_amount(localdict, line, total_rule)
    #             price = amount
    #             discount = 0
    #             data.update({
    #                 'price_unit': price,
    #                 'discount': discount,
    #                 'quantity': qty,
    #                 'product_id': line.product_id.id,
    #                 'product_uom_id': line.product_uom_id.id,
    #             })
    #         invoice_lines.append((0, 0, data))
    #     self.invoice_line_ids = invoice_lines
    #
    # @api.onchange('sale_order_template_id')
    # def onchange_sale_order_template_id(self):
    #     template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
    #     localdict = self.init_dicts()
    #     self._get_template_lines(self.sale_order_template_id.id, localdict)
    #     if not is_html_empty(template.note):
    #         self.note = template.note
    #
    # @api.onchange('weight', 'volume')
    # def onchange_variables(self):
    #     localdict = self.init_dicts()
    #     self._get_template_lines(self.sale_order_template_id.id, localdict)
