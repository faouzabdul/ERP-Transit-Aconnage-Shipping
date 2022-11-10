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
    consumption_count = fields.Integer(compute="_get_consumption", string='Fuel consumptions')

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

    def _get_consumption(self):
        log_fuel = self.env['fleet.vehicle.log.fuel']
        for record in self:
            record.consumption_count = log_fuel.search_count([('tank_id', '=', record.id)])

    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current operation """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_tank_id=self.id, group_by=False),
                domain=[('tank_id', '=', self.id)]
            )
            return res
        return False


class FleetFuelTankFilling(models.Model):
    _name = 'fleet.fuel.tank.filling'
    _description = 'History of fuel tank filling'

    date = fields.Date('Date')
    liter = fields.Float('Liters')
    price_per_liter = fields.Float()
    name = fields.Char('External Reference')
    tank_id = fields.Many2one('fleet.fuel.tank', 'Fuel Tank')
    create_uid = fields.Many2one('res.users', 'Create By')





