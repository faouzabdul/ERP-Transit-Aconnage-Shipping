# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class OutturnReport(models.Model):
    _name = 'servoo.stevedoring.outturn.report'
    _description = 'Outturn Report'

    name = fields.Char('Name', required=True, index=True, default=lambda self: _('New'), copy=False)
    bl_id = fields.Many2one('servoo.shipping.bl', 'Bill of lading', required=True)
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
    create_uid = fields.Many2one('res.users')

    @api.depends('excess', 'shortage', 'quantity')
    def _compute_delivery(self):
        for report in self:
            report.delivery = report.quantity - report.shortage + report.excess

    @api.depends('bl_id')
    def _compute_quantity(self):
        for report in self:
            report.quantity = report.bl_id.cargo_weight

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.stevedoring.outturn.report') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.stevedoring.outturn.report') or _('New')
        return super().create(vals)
