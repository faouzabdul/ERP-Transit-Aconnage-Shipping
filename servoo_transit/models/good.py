# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class TransitOrderGood(models.Model):
    _name = 'servoo.transit.good'

    name = fields.Char("Description")
    hscode_id = fields.Many2one('res.hs.code', 'SH Code')
    trade_name = fields.Char('Trade Name')
    line_number = fields.Integer('Line number')
    quantity = fields.Float('Quantity', digits=(6, 2))
    volume = fields.Float('Volume (m3)', digits=(12, 3))
    gross_weight = fields.Float('Gross Weight (kg)', digits=(12, 3))
    net_weight = fields.Float('Net Weight (kg)', digits=(12, 3))
    brand = fields.Char('Brand')
    fob_value_currency = fields.Float('FOB Value in currency', digits=(6, 3))
    order_id = fields.Many2one('servoo.transit.order', 'Transit Order')
    unit_id = fields.Many2one('res.unit', 'Unit')

