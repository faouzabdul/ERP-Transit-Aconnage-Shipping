# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class FleetFuelTank(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'fleet.fuel.tank'
    _description = 'Fuel Tank'

    def compute_fuel_level(self):
        for tank in self:
            tank.fuel_level = 0.0
            if tank.capacity > 0:
                tank.fuel_level = tank.liter / tank.capacity

    name = fields.Char('Name', required=True, tracking=True)
    location = fields.Char('Location', tracking=True)
    clean_date = fields.Date('Last Clean Date', tracking=True)
    capacity = fields.Float(tracking=True)
    liter = fields.Float(tracking=True)
    average_price = fields.Float()

    last_fill_date = fields.Date('Last Filling Date', tracking=True)
    last_add_fuel_date = fields.Date('Last Added Fuel Date', tracking=True)
    filling_ids = fields.One2many('fleet.fuel.tank.filling', 'tank_id', 'Filling history', tracking=True)

    fuel_type = fields.Selection([
        ('diesel', 'Diesel'),
        ('essence', 'Essence')
    ], string='Fuel type')

    fuel_level = fields.Float(string='Fuel level', compute=compute_fuel_level, store=False, readonly=True)

    @api.constrains('capacity')
    def _ckeck_capacity(self):
        for record in self:
            if record.capacity < 0:
                raise ValidationError(_("Tank capacity must not be negative"))


class FleetFuelTankFilling(models.Model):
    _name = 'fleet.fuel.tank.filling'
    _description = 'History of fuel tank filling'

    date = fields.Date('Date')
    liter = fields.Float('Liters')
    price_per_liter = fields.Float()
    name = fields.Char('External Reference')
    tank_id = fields.Many2one('fleet.fuel.tank', 'Fuel Tank')





