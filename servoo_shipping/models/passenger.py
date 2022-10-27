# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class Passenger(models.Model):
    _name = 'servoo.shipping.passenger'
    _description = 'Passenger List'

    passenger_id = fields.Many2one('servoo.shipping.person', 'Passenger', required=True)
    file_id = fields.Many2one('servoo.shipping.file', 'Shipping File', required=True)
    embarkation_port = fields.Many2one('res.locode', 'Port of embarkation')
    visa_number = fields.Char('Visa number', help="Visa number if appropriate")
    disembarkation_port = fields.Many2one('res.locode', 'Port of disembarkation')
    is_transit_passenger = fields.Boolean('Transit passenger or not')

