# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _

class FleetCleaningFuelTank(models.TransientModel):
    _name = 'fleet.cleaning.fuel.tank.wizard'
    _description = 'Cleaning fuel tank'

    description = fields.Text('Description', required=True)
    tank_id = fields.Many2one(
        'fleet.fuel.tank', string='Fuel Tank', required=True,
        default=lambda self: self.env.context.get('active_id', None),
    )
    date = fields.Datetime('Date')
    old_fuel_level = fields.Float('Old fuel level', related='tank_id.liter')
    new_fuel_level = fields.Float('New fuel level', required=True)

    @api.constrains('new_fuel_level')
    def _ckeck_capacity(self):
        for record in self:
            if record.new_fuel_level < 0:
                raise ValidationError(_("Tank capacity must not be negative"))

    def action_cleaning_fuel_tank(self):
        self.env['fleet.fuel.tank.cleaning'].sudo().create({
            'date': self.date,
            'description': self.description,
            'new_fuel_level': self.new_fuel_level,
            'old_fuel_level': self.old_fuel_level,
            'tank_id': self.tank_id.id
        })
        self.sudo().tank_id.liter = self.new_fuel_level
        return True