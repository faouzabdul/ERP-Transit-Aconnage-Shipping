# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
# import logging
#
# _logger = logging.getLogger(__name__)

class WizardOutturnReport(models.TransientModel):
    _name = 'servoo.stevedoring.outturn.report.wizard'
    _description = "Outturn Report"

    stevedoring_file_id = fields.Many2one('servoo.stevedoring.file', 'Stevedoring File', default=lambda self: self.env.context.get('active_id', None))
    consignee_id = fields.Many2one('res.partner', 'Client')
    date_debut = fields.Datetime('Date of commence')
    date_end = fields.Datetime('Date of complete')
    date = fields.Date('Date', default=lambda self: fields.datetime.now())
    vessel_id = fields.Many2one('res.transport.means', related='stevedoring_file_id.vessel_id')
    loading_port = fields.Many2one('res.locode', related='stevedoring_file_id.loading_port')
    discharge_port = fields.Many2one('res.locode', related='stevedoring_file_id.discharge_port')
    voyage_number = fields.Char(related='stevedoring_file_id.voyage_number')
    line_ids = fields.One2many('servoo.stevedoring.outturn.report.line.wizard', 'outturn_id', string='Lines',
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
            'line_ids': '',
            'vessel_id': self.vessel_id.id,
            'voyage_number': self.voyage_number,
            'loading_port': self.loading_port.id,
            'discharge_port': self.discharge_port.id
        }
        line_vals = []
        for line in self.line_ids:
            line_dict = {
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
                    'bl_line_ids': ''
                }
            line_vals.append(
                (0, 0, line_dict)
            )
            bl_line_vals = []
            for bl in line.bl_line_ids:
                bl_line_vals.append(
                    (0, 0, {
                        'good_description': bl.good_description,
                        'manifested_quantity': bl.manifested_quantity,
                        'shortage_quantity': bl.shortage_quantity,
                        'excess_quantity': bl.excess_quantity,
                        'delivery_quantity': bl.delivery_quantity,
                        'manifested_weight': bl.manifested_weight,
                        'shortage_weight': bl.shortage_weight,
                        'excess_weight': bl.excess_weight,
                        'delivery_weight': bl.delivery_weight,
                        'unit_id': bl.unit_id.id,
                    })
                )
                line_dict['bl_line_ids'] = bl_line_vals
        vals['line_ids'] = line_vals
        # _logger.info("vals : %s" % vals)
        return self.env['servoo.stevedoring.outturn.report'].create(vals)


class OutturnReportLine(models.TransientModel):
    _name = 'servoo.stevedoring.outturn.report.line.wizard'
    _description = 'Outturn Report Line'

    outturn_id = fields.Many2one('servoo.stevedoring.outturn.report.wizard', 'Outturn Report')
    bl_id = fields.Many2one('servoo.shipping.bl', 'Bill of lading', required=True)
    bl_line_ids = fields.One2many('servoo.stevedoring.outturn.report.bl.line.wizard', 'line_id')
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


class OutturnReportBlLine(models.TransientModel):
    _name = 'servoo.stevedoring.outturn.report.bl.line.wizard'
    _description = 'Outturn report bl line'

    line_id = fields.Many2one('servoo.stevedoring.outturn.report.line.wizard', 'Outturn Line')
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

class WizardShippingOutturnReport(models.TransientModel):
    _name = 'servoo.shipping.outturn.report.wizard'
    _description = "Outturn Report"

    shipping_file_id = fields.Many2one('servoo.shipping.file', 'Shipping File', default=lambda self: self.env.context.get('active_id', None))
    consignee_id = fields.Many2one('res.partner', 'Client')
    date_debut = fields.Datetime('Date of commence')
    date_end = fields.Datetime('Date of complete')
    date = fields.Date('Date', default=lambda self: fields.datetime.now())
    vessel_id = fields.Many2one('res.transport.means', related='shipping_file_id.vessel')
    loading_port = fields.Many2one('res.locode', 'Loading Port')
    discharge_port = fields.Many2one('res.locode', 'Discharging Port')
    voyage_number = fields.Char(related='shipping_file_id.voyage_number')
    line_ids = fields.One2many('servoo.shipping.outturn.report.line.wizard', 'outturn_id', string='Lines',
                               auto_join=True, copy=True)

    @api.depends('excess', 'shortage', 'quantity')
    def _compute_delivery(self):
        for report in self:
            report.delivery = report.quantity - report.shortage + report.excess

    def action_validate(self):
        vals = {
            'name': _('New'),
            'date': self.date,
            'shipping_file_id': self.shipping_file_id.id,
            'date_debut': self.date_debut,
            'date_end': self.date_end,
            'consignee_id': self.consignee_id.id,
            'line_ids': '',
            'vessel_id': self.vessel_id.id,
            'voyage_number': self.voyage_number,
            'loading_port': self.loading_port.id,
            'discharge_port': self.discharge_port.id
        }
        line_vals = []
        for line in self.line_ids:
            line_dict = {
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
                    'bl_line_ids': ''
                }
            line_vals.append(
                (0, 0, line_dict)
            )
            bl_line_vals = []
            for bl in line.bl_line_ids:
                bl_line_vals.append(
                    (0, 0, {
                        'good_description': bl.good_description,
                        'manifested_quantity': bl.manifested_quantity,
                        'shortage_quantity': bl.shortage_quantity,
                        'excess_quantity': bl.excess_quantity,
                        'delivery_quantity': bl.delivery_quantity,
                        'manifested_weight': bl.manifested_weight,
                        'shortage_weight': bl.shortage_weight,
                        'excess_weight': bl.excess_weight,
                        'delivery_weight': bl.delivery_weight,
                        'unit_id': bl.unit_id.id,
                    })
                )
                line_dict['bl_line_ids'] = bl_line_vals
        vals['line_ids'] = line_vals
        return self.env['servoo.stevedoring.outturn.report'].create(vals)

class ShippingOutturnReportLine(models.TransientModel):
    _name = 'servoo.shipping.outturn.report.line.wizard'
    _description = 'Outturn Report Line'

    outturn_id = fields.Many2one('servoo.shipping.outturn.report.wizard', 'Outturn Report')
    bl_id = fields.Many2one('servoo.shipping.bl', 'Bill of lading', required=True)
    bl_line_ids = fields.One2many('servoo.shipping.outturn.report.bl.line.wizard', 'line_id')
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

class ShippingOutturnReportBlLine(models.TransientModel):
    _name = 'servoo.shipping.outturn.report.bl.line.wizard'
    _description = 'Outturn report bl line'

    line_id = fields.Many2one('servoo.shipping.outturn.report.line.wizard', 'Outturn Line')
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
