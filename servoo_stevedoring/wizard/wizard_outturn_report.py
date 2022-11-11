# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime


class WizardOutturnReport(models.TransientModel):
    _name = 'servoo.stevedoring.outturn.report.wizard'
    _description = "Outturn Report"

    stevedoring_file_id = fields.Many2one('servoo.stevedoring.file', 'Stevedoring File', default=lambda self: self.env.context.get('active_id', None))
    consignee_id = fields.Many2one('res.partner', 'Client')
    date_debut = fields.Datetime('Date of commence')
    date_end = fields.Datetime('Date of complete')
    date = fields.Date('Date', default=datetime.now())
    vessel_id = fields.Many2one('res.transport.means', related='stevedoring_file_id.vessel_id')
    loading_port = fields.Many2one('res.locode', related='stevedoring_file_id.loading_port')
    discharge_port = fields.Many2one('res.locode', related='stevedoring_file_id.discharge_port')
    voyage_number = fields.Char(related='stevedoring_file_id.voyage_number')
    line_ids = fields.One2many('servoo.stevedoring.outturn.report.line', 'outturn_id', string='Lines',
                               auto_join=True, copy=True)

    @api.depends('excess', 'shortage', 'quantity')
    def _compute_delivery(self):
        for report in self:
            report.delivery = report.quantity - report.shortage + report.excess

    def action_validate(self):
        vals = {
            'name': _('New'),
            'date': self.date,
            'stevedoring_file_id': self.stevedoring_file_id.id,
            'date_debut': self.date_debut,
            'date_end': self.date_end,
            'consignee_id': self.consignee_id.id,
        }
        line_vals = []
        for line in self.line_ids:
            line_vals.append(
                (0, 0, {
                    'bl_id': line.bl_id.id,
                    'manifested_quantity': line.manifested_quantity,
                    'shortage_quantity': line.shortage_quantity,
                    'excess_quantity': line.excess_quantity,
                    'delivery_quantity': line.delivery_quantity,
                    'manifested_weight': line.manifested_weight,
                    'shortage_weight': line.shortage_weight,
                    'excess_weight': line.excess_weight,
                    'delivery_weight': line.delivery_weight,
                    'note': line.note,
                    'unit_id': line.unit_id.id,
                })
            )
        vals['line_ids'] = line_vals
        return self.env['servoo.stevedoring.outturn.report'].create(vals)


class OutturnReportLine(models.TransientModel):
    _name = 'servoo.stevedoring.outturn.report.line.wizard'
    _description = 'Outturn Report Line'

    outturn_id = fields.Many2one('servoo.stevedoring.outturn.report.wizard', 'Outturn Report')
    bl_id = fields.Many2one('servoo.shipping.bl', 'Bill of lading', required=True)
    manifested_quantity = fields.Float('Quantity Manifested', digits=(6, 3))
    shortage_quantity = fields.Float('Quantity Shortage', digits=(6, 3))
    excess_quantity = fields.Float('Quantity Excess', digits=(6, 3))
    delivery_quantity = fields.Float('Quantity Delivery', digits=(6, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')
    manifested_weight = fields.Float('Tonnage Manifested', digits=(6, 3))
    shortage_weight = fields.Float('Tonnage Shortage', digits=(6, 3))
    excess_weight = fields.Float('Tonnage Excess', digits=(6, 3))
    delivery_weight = fields.Float('Tonnage Delivery', digits=(6, 3))
    note = fields.Text('Notes')
