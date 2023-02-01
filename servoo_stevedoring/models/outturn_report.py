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
    create_uid = fields.Many2one('res.users', string='Created by', index=True, readonly=True)
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
    bl_line_ids = fields.One2many('servoo.stevedoring.outturn.report.bl.line', 'line_id')
    manifested_quantity = fields.Float('Quantity Manifested', digits=(6, 3), compute='_compute_quantity')
    shortage_quantity = fields.Float('Quantity Shortage', digits=(6, 3), compute='_compute_quantity')
    excess_quantity = fields.Float('Quantity Excess', digits=(6, 3), compute='_compute_quantity')
    delivery_quantity = fields.Float('Quantity Delivery', digits=(6, 3), compute='_compute_quantity')
    unit_id = fields.Many2one('res.unit', 'Unit')
    manifested_weight = fields.Float('Tonnage Manifested', digits=(6, 3), compute='_compute_quantity')
    shortage_weight = fields.Float('Tonnage Shortage', digits=(6, 3), compute='_compute_quantity')
    excess_weight = fields.Float('Tonnage Excess', digits=(6, 3), compute='_compute_quantity')
    delivery_weight = fields.Float('Tonnage Delivery', digits=(6, 3), compute='_compute_quantity')
    note = fields.Text('Notes')

    @api.onchange('bl_line_ids')
    def _compute_quantity(self):
        manifested_quantity = shortage_quantity = excess_quantity = delivery_quantity = 0.0
        manifested_weight = shortage_weight = excess_weight = delivery_weight = 0.0
        for line in self.bl_line_ids:
            manifested_quantity += line.manifested_quantity
            shortage_quantity += line.shortage_quantity
            excess_quantity += line.excess_quantity
            delivery_quantity += line.delivery_quantity
            manifested_weight += line.manifested_weight
            shortage_weight += line.shortage_weight
            excess_weight += line.excess_weight
            delivery_weight += line.delivery_weight
        self.delivery_weight = delivery_weight
        self.excess_weight = excess_weight
        self.shortage_weight = shortage_weight
        self.manifested_weight = manifested_weight
        self.delivery_quantity = delivery_quantity
        self.excess_quantity = excess_quantity
        self.shortage_quantity = shortage_quantity
        self.manifested_quantity = manifested_quantity

    @api.onchange('bl_id')
    def onchange_bl_id(self):
        lines = [(5, 0, 0)]
        for good in self.bl_id.good_ids:
            lines.append((0, 0, {
                'good_description': good.name,
                'manifested_quantity': good.quantity,
                'unit_id': good.unit_id.id,
                'manifested_weight': good.gross_weight if good.gross_weight else good.net_weight
            }))
        self.bl_line_ids = lines


class OutturnReportBlLine(models.Model):
    _name = 'servoo.stevedoring.outturn.report.bl.line'
    _description = 'Outturn report bl line'

    line_id = fields.Many2one('servoo.stevedoring.outturn.report.line', 'Outturn Line')
    good_description = fields.Char('Good description')
    manifested_quantity = fields.Float('Quantity Manifested', digits=(6, 3))
    shortage_quantity = fields.Float('Quantity Shortage', digits=(6, 3))
    excess_quantity = fields.Float('Quantity Excess', digits=(6, 3))
    delivery_quantity = fields.Float('Quantity Delivery', digits=(6, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')
    manifested_weight = fields.Float('Tonnage Manifested', digits=(6, 3))
    shortage_weight = fields.Float('Tonnage Shortage', digits=(6, 3))
    excess_weight = fields.Float('Tonnage Excess', digits=(6, 3))
    delivery_weight = fields.Float('Tonnage Delivery', digits=(6, 3))


