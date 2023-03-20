# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardSupplierInvoice(models.TransientModel):
    _name = 'servoo.account.move.wizard'
    _description = "Supplier Invoice Wizard"

    account_move_id = fields.Many2one('account.move', 'Supplier Invoice',
                                         default=lambda self: self.env.context.get('active_id', None))
    # state = fields.Selection(related='account_move_id.sate')
    state = fields.Selection(related='account_move_id.state', store=True, readonly=True)
    department_id = fields.Many2one('hr.department', 'Department')
    invoice_payment_term_id = fields.Many2one('account.payment.term', related='account_move_id.invoice_payment_term_id', store=True, readonly=False)
    invoice_date_due = fields.Date(related='account_move_id.invoice_date_due', store=True, readonly=False)
    observation = fields.Text('Observation')

    def action_validate(self):
        state = ''
        vals = {'observation': self.observation}
        if self.account_move_id.state == 'direction_routing':
            vals['department_id'] = self.department_id.id
            state = 'department_approval'
        elif self.account_move_id.state == 'department_approval':
            state = 'direction_approval'
        elif self.account_move_id.state == 'direction_approval':
            state = 'accounting_approval'
        elif self.account_move_id.state == 'accounting_approval':
            state = 'management_control_approval'
            vals['invoice_payment_term_id'] = self.invoice_payment_term_id.id
            vals['invoice_date_due'] = self.invoice_date_due
            if not self.account_move_id.invoice_date:
                self.account_move_id.invoice_date = datetime.now()
            self.account_move_id.action_post()
            # vals['invoice_date'] = datetime.now()
        elif self.account_move_id.state == 'management_control_approval':
            state = 'posted'
        vals['state'] = state
        self.account_move_id.update(vals)
        # if self.account_move_id.state == 'accounting_approval':
        #     self.account_move_id.action_post()

    def action_send_to_accounting(self):
        self.account_move_id.update({'state': 'accounting_approval'})

