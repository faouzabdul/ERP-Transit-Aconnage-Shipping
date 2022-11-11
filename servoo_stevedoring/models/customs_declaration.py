# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _


class CustomsDeclaration(models.Model):
    _name = 'servoo.customs.declaration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customs Declaration'
    _order = 'id desc'

    name = fields.Char('Reference', required=True, index=True, copy=False)
    date = fields.Date('Date')
    charger_id = fields.Many2one('res.partner', 'Charger', index=True)
    loading_port = fields.Many2one('res.locode', 'Port of loading', index=True)
    unloading_port = fields.Many2one('res.locode', 'Port of discharge', index=True)
    stevedoring_file_id = fields.Many2one('servoo.stevedoring.file', 'Stevedoring File')
    good_ids = fields.One2many('servoo.shipping.good', 'customs_declaration_id', string='Goods',
                               auto_join=True, index=True, copy=True)
    vessel_id = fields.Many2one('res.transport.means', string="Vessel", index=True)
    voyage_number = fields.Char('Voyage Number')
    mate_receipt_count = fields.Integer(compute="_get_mate_receipt", string='Mate Receipt')

    def _get_mate_receipt(self):
        mate_receipt = self.env['servoo.stevedoring.mate.receipt']
        for record in self:
            record.mate_receipt_count = mate_receipt.search_count([('customs_declaration_id', '=', record.id)])
