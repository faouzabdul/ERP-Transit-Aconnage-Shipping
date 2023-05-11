# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    bank_statement_id = fields.Many2one('account.bank.statement', 'Bank Statement')
    account_bank_statement_line_id = fields.Many2one('account.bank.statement.line', 'Bank statement line',
                                                     readonly=True)
    receiver = fields.Selection([
        ('pad', 'PAD'),
        ('other', 'Other'),
        ('apm', 'APM')
    ], string='Receiver')
    payment_mode = fields.Selection([
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('bank_draft', 'Bank Draft')
    ], string='Payment Mode')

    def _create_payment_vals_from_wizard(self):
        vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        vals['bank_statement_id'] = self.bank_statement_id.id
        vals['payment_mode'] = self.payment_mode
        vals['receiver'] = self.receiver
        return vals

