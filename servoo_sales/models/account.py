# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from . import utils


class AccountMode(models.Model):
    _inherit = 'account.move'

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
    amount_total_signed_letter = fields.Char('Total Signed letter', compute='_compute_display_amount_letter',
                                               store=False)
    amount_total_in_currency_signed_letter = fields.Char('Total in Currency Signed letter', compute='_compute_display_amount_letter',
                                               store=False)

    other_currency_id = fields.Many2one('res.currency', 'Other Currency')
    amount_other_currency = fields.Float(string='Total Currency', store=True, digits=(6, 3),
                                         compute='_compute_display_amount_letter')

    @api.depends('amount_total', 'currency_id')
    def _compute_display_amount_letter(self):
        for move in self:
            move.amount_total_signed_letter = utils.translate(move.amount_total_signed).upper()
            move.amount_total_in_currency_signed_letter = utils.translate(move.amount_total_in_currency_signed).upper()
            currency_code = 'XAF'
            if move.currency_id.name == 'XAF':
                currency_code = 'EUR'
            other_currency = self.env['res.currency'].search([('name', '=', currency_code)])
            rate = other_currency.rate if currency_code == 'EUR' else other_currency.inverse_rate
            move.other_currency_id = other_currency and other_currency.id
            move.amount_other_currency = move.amount_total_signed * rate
