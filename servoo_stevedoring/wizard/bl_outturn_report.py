# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models
from datetime import datetime


class BlOutturnReport(models.TransientModel):
    _name = 'servoo.stevedoring.bl.outturn.report'
    _description = "Outturn Report"

    bl_id = fields.Many2one('servoo.shipping.bl', 'Bill of lading', default=lambda self: self.env.context.get('active_id', None))
    consignee_id = fields.Many2one('res.partner', related='bl_id.consignee_id')
    cargo_description = fields.Char(related='bl_id.cargo_description')
    loading_port = fields.Many2one('res.locode', related='bl_id.loading_port')
    discharge_port = fields.Many2one('res.locode', related='bl_id.discharge_port')
    vessel_id = fields.Many2one('res.transport.means', related='bl_id.vessel_id')
    quantity = fields.Float('Quantity', digits=(6, 3))
    shortage = fields.Float('Shortage', digits=(6, 3))
    excess = fields.Float('Excess', digits=(6, 3))
    delivery = fields.Float('Delivery', digits=(6, 3), readonly=True, compute='_compute_delivery')
    note = fields.Text('Notes')
    date_debut = fields.Datetime('Date of commence')
    date_end = fields.Datetime('Date of complete')
    date = fields.Date('Date', default=datetime.now())

    @api.depends('excess', 'shortage', 'quantity')
    def _compute_delivery(self):
        for report in self:
            report.delivery = report.quantity - report.shortage + report.excess

    def action_validate(self):
        vals = {
            'name': 'New',
            'date': self.date,
            'bl_id': self.bl_id.id,
            'date_debut': self.date_debut,
            'date_end': self.date_end,
            'note': self.note,
            'delivery': self.delivery,
            'quantity': self.quantity,
            'shortage': self.shortage,
            'excess': self.excess,
        }
        return self.env['servoo.stevedoring.outturn.report'].create(vals)
