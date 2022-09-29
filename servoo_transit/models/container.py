# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class TransitOrderContainer(models.Model):
    _name = 'servoo.transit.container'

    container_id = fields.Many2one('res.container', 'Container')
    size_type_id = fields.Many2one('res.container.size.type', related='container_id.size_type_id', string='Size', readonly=True)
    volume = fields.Float('Volume (m3)', digits=(12, 3))
    weight = fields.Float('Weight (kg)', digits=(12, 3))
    vgm = fields.Float('VGM (kg)', digits=(12, 3))
    package_count = fields.Float('Package count', digits=(6, 2))
    seal_1 = fields.Char('Seal 1')
    seal_2 = fields.Char('Seal 2')
    seal_3 = fields.Char('Seal 3')
    order_id = fields.Many2one('servoo.transit.order', 'Transit Order')

