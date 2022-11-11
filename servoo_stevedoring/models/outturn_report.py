# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class OutturnReport(models.Model):
    _name = 'servoo.stevedoring.outturn.report'
    _description = 'Outturn Report'

    name = fields.Char('Name', required=True, index=True, default=lambda self: _('New'), copy=False)
    consignee_id = fields.Many2one('res.partner', 'Client')
    date_debut = fields.Datetime('Date of commence')
    date_end = fields.Datetime('Date of complete')
    date = fields.Date('Date', default=datetime.now())
    create_uid = fields.Many2one('res.users')
    line_ids = fields.One2many('servoo.stevedoring.outturn.report.line', 'outturn_id', string='Lines',
                               auto_join=True, copy=True)
    stevedoring_file_id = fields.Many2one('servoo.stevedoring.file', 'Stevedoring File')
    vessel_id = fields.Many2one('res.transport.means', related='stevedoring_file_id.vessel_id')
    loading_port = fields.Many2one('res.locode', related='stevedoring_file_id.loading_port')
    discharge_port = fields.Many2one('res.locode', related='stevedoring_file_id.discharge_port')
    voyage_number = fields.Char(related='stevedoring_file_id.voyage_number')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.stevedoring.outturn.report') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.stevedoring.outturn.report') or _('New')
        return super().create(vals)


class OutturnReportLine(models.Model):
    _name = 'servoo.stevedoring.outturn.report.line'
    _description = 'Outturn Report Line'

    outturn_id = fields.Many2one('servoo.stevedoring.outturn.report', 'Outturn Report')
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