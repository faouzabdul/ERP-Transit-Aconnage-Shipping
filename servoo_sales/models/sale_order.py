# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from . import utils


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    transport_means_id = fields.Many2one('res.transport.means', string="Mean of transportation")
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
    amount_other_currency = fields.Float(string='Total Currency', store=True, digits=(6, 3),
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
