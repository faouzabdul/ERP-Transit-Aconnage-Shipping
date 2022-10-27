# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class ShippingGood(models.Model):
    _name = 'servoo.shipping.dangerous.good'
    _description = 'Dangerous Good'

    stowage = fields.Char('Stowage Position')
    reference_number = fields.Char('Reference Number')
    name = fields.Char("Marks & Numbers")
    un_number = fields.Char('UN Number')
    technical_specification = fields.Char('Technical Specification')
    class_name = fields.Char('Class')
    packing_group = fields.Char('Packing Group')
    additional_information = fields.Char('Additional Information')
    ems = fields.Char('EmS')
    volume = fields.Float('Volume (m3)', digits=(12, 3))
    gross_weight = fields.Float('Gross Weight (kg)', digits=(12, 3))
    quantity = fields.Float('Quantity', digits=(12, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')
    file_id = fields.Many2one('servoo.shipping.file', 'shipping Order')


