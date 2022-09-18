# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class FleetVehicleLogFuel(models.Model):
    _name = 'fleet.vehicle.log.fuel'
    _description = 'Fuel log for vehicles'
    _inherits = {'fleet.vehicle.log.services': 'service_id'}

    @api.model
    def default_get(self, default_fields):
        res = super(FleetVehicleLogFuel, self).default_get(default_fields)
        res.update({
            'date': fields.Date.context_today(self),
            # 'cost_subtype_id': service and service.id or False,
            'service_type_id': self.env.ref('dyen_fleet.type_service_service_0', raise_if_not_found=False).id,
            'state': 'done'
        })
        return res

    liter = fields.Float()
    price_per_liter = fields.Float()
    purchaser_id = fields.Many2one('res.partner', 'Purchaser')
    inv_ref = fields.Char('Invoice Reference', size=64)
    vendor_id = fields.Many2one('res.partner', 'Vendor')
    notes = fields.Text()
    service_id = fields.Many2one('fleet.vehicle.log.services', 'Service', required=True, ondelete='cascade')
    # we need to keep this field as a related with store=True because the graph view doesn't support
    # (1) to address fields from inherited table
    # (2) fields that aren't stored in database
    amount = fields.Monetary(related='service_id.amount', string='Amount', store=True, readonly=False)
    tank_id = fields.Many2one('fleet.fuel.tank', 'Fuel Tank')

    @api.onchange('vehicle_id')
    def _onchange_vehicle(self):
        if self.vehicle_id:
            self.odometer_unit = self.vehicle_id.odometer_unit
            self.purchaser_id = self.vehicle_id.driver_id.id

    @api.onchange('liter', 'price_per_liter', 'amount')
    def _onchange_liter_price_amount(self):
        # need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        # make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        # liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        # of 3.0/2=1.5)
        # If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        # onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        # computation to 2 decimal
        liter = float(self.liter)
        price_per_liter = float(self.price_per_liter)
        amount = float(self.amount)
        if liter > 0 and price_per_liter > 0 and round(liter * price_per_liter, 2) != amount:
            self.amount = round(liter * price_per_liter, 2)
        elif amount > 0 and liter > 0 and round(amount / liter, 2) != price_per_liter:
            self.price_per_liter = round(amount / liter, 2)
        elif amount > 0 and price_per_liter > 0 and round(amount / price_per_liter, 2) != liter:
            self.liter = round(amount / price_per_liter, 2)

    @api.model
    def create(self, vals):
        tank = self.env['fleet.fuel.tank'].browse(vals.get('tank_id'))
        if tank.liter < vals.get("liter"):
            raise ValidationError(_("The amount of fuel in the tank cannot satisfy this request"))
        tank.liter -= vals.get("liter")
        return super(FleetVehicleLogFuel, self).create(vals)

    @api.constrains('liter')
    def _ckeck_liter(self):
        for record in self:
            if record.liter <= 0:
                raise ValidationError(_("Liter must be positive and non zero"))
