# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from . import utils
import logging
from odoo.exceptions import UserError, ValidationError
from odoo.tools import is_html_empty
import json

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
                                      store=True)
    other_currency_id = fields.Many2one('res.currency', 'Other Currency')
    amount_other_currency = fields.Float(string='Total Currency', store=True, digits=(6, 3),
                                         compute='_compute_display_amount_letter')
    agency_name = fields.Selection([
        ('Douala', 'Douala'),
        ('Kribi', 'Kribi'),
        ('Tchad', 'Tchad'),
    ], string='Agency', default='Douala')
    handling = fields.Float('Rate')
    include_tax_for_handling = fields.Boolean('Include Taxes')
    quantity = fields.Float('Quantity')
    handling_rate_id = fields.Many2one('servoo.handling.rate', 'Good Type')
    rate_type = fields.Selection(related='handling_rate_id.rate_type', string='Rate Type')

    handling2 = fields.Float('Rate 2')
    include_tax_for_handling2 = fields.Boolean('Include Taxes 2')
    quantity2 = fields.Float('Quantity 2')
    handling_rate_2_id = fields.Many2one('servoo.handling.rate', 'Good Type 2')
    rate_type_2 = fields.Selection(related='handling_rate_2_id.rate_type', string='Rate Type 2')

    handling3 = fields.Float('Rate 3')
    include_tax_for_handling3 = fields.Boolean('Include Taxes 3')
    quantity3 = fields.Float('Quantity 3')
    handling_rate_3_id = fields.Many2one('servoo.handling.rate', 'Good Type 3')
    rate_type_3 = fields.Selection(related='handling_rate_3_id.rate_type', string='Rate Type 3')

    distribute_ht_amount = fields.Boolean('Distribute HT Amount')

    @api.onchange('distribute_ht_amount', 'amount_untaxed')
    def onchange_distribute_ht_amount(self):
        narration = ''
        if self.distribute_ht_amount:
            part = self.amount_untaxed / 2
            narration = """50%% APM SA: %s %s<br />
                50%% PAK: %s %s
                """ % (part, self.currency_id.symbol, part, self.currency_id.symbol)
        self.note = narration


    @api.depends('amount_total', 'currency_id')
    def _compute_display_amount_letter(self):
        for order in self:
            order.amount_total_letter = utils.translate(order.amount_total, currency=order.currency_id.name).upper()
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
                    'object': order.object,
                    'agency_name': order.agency_name,
                })
                # move._apply_added_lines()

    def _compute_line_data_for_template_change(self, line):
        return {
            'sequence': line.sequence,
            'display_type': line.display_type,
            'name': line.name,
            'state': 'draft',
        }

    def _sum_rule_amount(self, localdict, line, amount):
        # _logger.info('line.code : %s = %s' % (line.code, amount))
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
            'ROYALTY': self.handling,
            'ROYALTY2': self.handling2,
            'ROYALTY3': self.handling3,
            'QUANTITY': self.quantity,
            'QUANTITY2': self.quantity2,
            'QUANTITY3': self.quantity3,
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

    @api.onchange('weight', 'volume', 'handling', 'quantity','handling2', 'quantity2','handling3', 'quantity3')
    def onchange_variables(self):
        localdict = self.init_dicts()
        self._get_template_lines(self.sale_order_template_id.id, localdict)

    @api.onchange('handling_rate_id')
    def onchange_hanlding_rate(self):
        self.handling = self.handling_rate_id.rate

    @api.onchange('handling_rate_2_id')
    def onchange_hanlding_rate2(self):
        self.handling2 = self.handling_rate_2_id.rate

    @api.onchange('handling_rate_3_id')
    def onchange_hanlding_rate3(self):
        self.handling3 = self.handling_rate_3_id.rate

    @api.onchange('include_tax_for_handling')
    def onchange_include_tax(self):
        if self.handling == 0.0:
            return
        rate = self.handling
        if self.include_tax_for_handling:
            rate += rate * 0.1925
        else:
            rate = self.handling_rate_id.rate
        self.handling = rate

    @api.onchange('include_tax_for_handling2')
    def onchange_include_tax2(self):
        if self.handling2 == 0.0:
            return
        rate = self.handling2
        if self.include_tax_for_handling2:
            rate += rate * 0.1925
        else:
            rate = self.handling_rate_2_id.rate
        self.handling2 = rate

    @api.onchange('include_tax_for_handling3')
    def onchange_include_tax3(self):
        if self.handling3 == 0.0:
            return
        rate = self.handling3
        if self.include_tax_for_handling3:
            rate += rate * 0.1925
        else:
            rate = self.handling_rate_3_id.rate
        self.handling3 = rate

    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()
        if self.origin:
            vals['invoice_origin'] = self.origin
        return vals

    @api.depends('order_line.tax_id', 'order_line.price_unit', 'amount_total', 'amount_untaxed', 'order_line.no_days')
    def _compute_tax_totals_json(self):
        def compute_taxes(order_line):
            price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
            qty = order_line.product_uom_qty * order_line.no_days if order_line.no_days and order_line.no_days > 0 else order_line.product_uom_qty
            order = order_line.order_id
            return order_line.tax_id._origin.compute_all(price, order.currency_id, qty,
                                                         product=order_line.product_id,
                                                         partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line,
                                                                                         compute_taxes)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total,
                                                      order.amount_untaxed, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    no_days = fields.Integer('Days', help='Number of days')

    def _prepare_invoice_line(self, **optional_values):
        """
                Prepare the dict of values to create the new invoice line for a sales order line.

                :param qty: float quantity to invoice
                :param optional_values: any parameter that should be added to the returned invoice line
                """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
            'no_days': self.no_days,
        }
        if self.order_id.analytic_account_id:
            res['analytic_account_id'] = self.order_id.analytic_account_id.id
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res

    @api.onchange('no_days')
    def _onchange_nodays(self):
        # _logger.info('no_days %s' % self.no_days)
        self._compute_amount()

    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            qty = line.product_uom_qty * line.no_days if line.no_days and line.no_days > 0 else line.product_uom_qty
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            no_days = line.no_days if line.no_days and line.no_days > 0 else 1.0
            line.update({
                'price_tax': sum(t.get('amount', 0.0) * no_days for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])


