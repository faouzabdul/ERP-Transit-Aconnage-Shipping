# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO


from odoo import api, fields, models, _


class ShipStore(models.Model):
    _name = 'servoo.shipping.ship.store'
    _description = 'Ship Store'

    name = fields.Char('Location on board', required=True)
    use = fields.Char('Official use')
    file_id = fields.Many2one('servoo.shipping.file', 'Shipping File')
    good = fields.Char('Good description')
    quantity = fields.Float('Quantity', digits=(12, 3))
    gross_weight = fields.Float('Gross Weight (kg)', digits=(12, 3))
