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
    weight = fields.Float('Weight (Kg)', digits=(12, 3))
    custom_declaration_reference = fields.Char('Custom Declaration Reference')
    custom_declaration_date = fields.Date('Custom Declaration Date')
    assessed_value = fields.Float('Assessed Value', digits=(12, 3), help='Valeur imposable')
    object = fields.Text('Object')
    number_of_packages = fields.Char('Number of packages/TC')
    amount_total_signed_letter = fields.Char('Total Signed letter', compute='_compute_display_amount_letter',
                                               store=False)
    amount_total_in_currency_signed_letter = fields.Char('Total in Currency Signed letter', compute='_compute_display_amount_letter',
                                               store=False)

    @api.depends('amount_total')
    def _compute_display_amount_letter(self):
        for move in self:
            move.amount_total_signed_letter = utils.translate(move.amount_total_signed).upper()
            move.amount_total_in_currency_signed_letter = utils.translate(move.amount_total_in_currency_signed).upper()
