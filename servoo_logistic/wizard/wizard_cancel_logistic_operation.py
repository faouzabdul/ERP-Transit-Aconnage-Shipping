# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCancelLogisticOperation(models.TransientModel):
    _name = 'servoo.logistic.operation.cancel.wizard'
    _description = 'Wizard for cancel logistic operation'

    logistic_operation_id = fields.Many2one('servoo.logistic.operation', 'Logistic operation',
                                      default=lambda self: self.env.context.get('active_id', None))
    observation = fields.Text('Observation', required=True)

    def action_validate(self):
        vals = {
            'state': 'cancel',
            'cancel_note': self.observation
        }
        self.logistic_operation_id.update(vals)