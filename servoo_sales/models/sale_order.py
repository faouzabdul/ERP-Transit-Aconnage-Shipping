# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
