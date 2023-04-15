# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCancelTransitOrder(models.TransientModel):
    _name = 'servoo.transit.order.cancel.wizard'
    _description = 'Wizard for cancel transit order'

    transit_order_id = fields.Many2one('servoo.transit.order', 'Transit Order',
                                      default=lambda self: self.env.context.get('active_id', None))
    observation = fields.Text('Observation', required=True)

    def action_validate(self):
        vals = {
            'state': 'cancel',
            'cancel_note': self.observation
        }
        self.transit_order_id.update(vals)