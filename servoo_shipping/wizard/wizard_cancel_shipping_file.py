# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCancelShippingFile(models.TransientModel):
    _name = 'servoo.shipping.file.cancel.wizard'
    _description = 'Wizard for cancel shipping file'

    shipping_file_id = fields.Many2one('servoo.shipping.file', 'shipping File',
                                      default=lambda self: self.env.context.get('active_id', None))
    observation = fields.Text('Observation', required=True)

    def action_validate(self):
        vals = {
            'state': 'cancel',
            'cancel_note': self.observation
        }
        self.shipping_file_id.update(vals)