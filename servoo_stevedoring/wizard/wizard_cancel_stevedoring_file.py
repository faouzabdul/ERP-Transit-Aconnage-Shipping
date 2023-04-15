# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCancelStevedoringFile(models.TransientModel):
    _name = 'servoo.stevedoring.file.cancel.wizard'
    _description = 'Wizard for cancel stevedoring file'

    stevedoring_file_id = fields.Many2one('servoo.stevedoring.file', 'Stevedoring File',
                                      default=lambda self: self.env.context.get('active_id', None))
    observation = fields.Text('Observation', required=True)

    def action_validate(self):
        vals = {
            'state': 'cancel',
            'cancel_note': self.observation
        }
        self.stevedoring_file_id.update(vals)