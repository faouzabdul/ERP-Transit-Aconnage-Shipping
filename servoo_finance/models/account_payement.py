# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bank_statement_id = fields.Many2one('account.bank.statement', 'Bank Statement')
    account_bank_statement_line_id = fields.Many2one('account.bank.statement.line', 'Bank statement line',
                                                     readonly=True)
    receiver = fields.Selection([
        ('pad', 'PAD'),
        ('other', 'Other'),
        ('apm', 'APM')
    ], string='Receiver')
    apm_invoice_number = fields.Char('APM Invoice Number', compute="_get_apm_invoice_number", strore=False)
    payment_mode = fields.Selection([
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('bank_draft', 'Bank Draft')
    ], string='Payment Mode', default='cash')


    def _get_apm_invoice_number(self):
        account_move = self.env['account.move']
        for record in self:
            if record.ref:
                move = account_move.search([('name', '=', record.ref)])
                if move and move.apm_reference:
                    record.apm_invoice_number = move.apm_reference
                else:
                    record.apm_invoice_number=''
            else:
                record.apm_invoice_number = ''

    @api.model
    def create(self, vals):
        payment = super(AccountPayment, self).create(vals)
        if vals['bank_statement_id']:
            bank_statement_line_vals = {
                'date': payment.date,
                'payment_ref': payment.ref,
                'narration': payment.payment_reference,
                'partner_id': payment.partner_id.id,
                'amount': (-1 * payment.amount) if payment.payment_type == 'outbound' else payment.amount,
                'journal_id': payment.journal_id.id,
                'statement_id': vals['bank_statement_id'],
                'receiver': vals['receiver']
                # 'move_id': payment.move_id.id
            }
            payment.account_bank_statement_line_id = self.env['account.bank.statement.line'].create(bank_statement_line_vals)
        return payment

    def action_post(self):
        super(AccountPayment, self).action_post()
        if self.account_bank_statement_line_id:
            self.account_bank_statement_line_id.move_id = self.move_id.id
