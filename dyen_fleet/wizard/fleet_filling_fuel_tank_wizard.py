# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.exceptions import ValidationError


class FleetFillingFuelTank(models.TransientModel):
    _name = 'fleet.filling.fuel.tank.wizard'
    _description = "Filling fuel tank"

    date = fields.Date('Date', default=fields.Date.context_today, required=True)
    liter = fields.Float()
    name = fields.Char('External Reference')
    price_per_liter = fields.Float()
    tank_id = fields.Many2one(
        'fleet.fuel.tank', string='Fuel Tank', required=True,
        default=lambda self: self.env.context.get('active_id', None),
    )

    @api.constrains('liter')
    def _ckeck_filling_quantity(self):
        for record in self:
            if record.liter <= 0:
                raise ValidationError(_("Liter must be positive and non zero"))
            if record.liter + record.tank_id.liter > record.tank_id.capacity:
                raise ValidationError(_("You cannot add fuel beyond the tank's maximum capacity"))

    def action_filling_fuel_tank(self):
        if (self.liter + self.tank_id.liter) == self.tank_id.capacity:
            # self.tank_id.last_fill_date = datetime.now()
            self.tank_id.last_fill_date = self.date
        self.tank_id.liter += self.liter
        # self.tank_id.last_add_fuel_date = datetime.now()
        self.tank_id.last_add_fuel_date = self.date
        return self.env['fleet.fuel.tank.filling'].create({
            'date': self.date,
            'liter': self.liter,
            'name': self.name,
            'price_per_liter': self.price_per_liter,
            'tank_id': self.tank_id.id
        })

