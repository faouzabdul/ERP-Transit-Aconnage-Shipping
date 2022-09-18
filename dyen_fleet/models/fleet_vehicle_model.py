# # -*- coding: utf-8 -*-
# # Author: Marius YENKE MBEUYO
#
# from odoo import api, fields, models, _
#
#
# class FleetVehicleType(models.Model):
#     _name = 'fleet.vehicle.type'
#
#     name = fields.Char('Vehicle Type')
#
#
# class FleetVehicleModel(models.Model):
#     _inherit = 'fleet.vehicle.model'
#
#     vehicle_type = fields.Many2one('fleet.vehicle.type', 'Vehicle Type')
#
#
# class FleetVehicle(models.Model):
#     _inherit = 'fleet.vehicle'
#
#     vehicle_type = fields.Many2one(related='model_id.vehicle_type')
