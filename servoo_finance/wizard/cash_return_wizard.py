# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCashReturn(models.TransientModel):
    _name = 'servoo.cash.return.wizard'
    _description = 'Cash Return'

    date = fields.Datetime('Date', default=lambda self: fields.datetime.now())
    cash_voucher_id = fields.Many2one('servoo.cash.voucher', 'Cash Voucher', default=lambda self: self.env.context.get('active_id', None))
    journal_id = fields.Many2one(related='cash_voucher_id.journal_id')
    amount = fields.Float(related='cash_voucher_id.amount_unjustified')
    bank_statement_id = fields.Many2one('account.bank.statement', 'Bank Statement')


    def action_validate(self):
        vals = {
            'date': self.date,
            'cash_voucher_id': self.cash_voucher_id.id,
            'journal_id':  self.journal_id.id,
            'amount': self.amount
        }
        cash_return = self.env['servoo.cash.return'].create(vals)
        cash_voucher_justified_amount = self.amount + self.cash_voucher_id.amount_justified
        self.cash_voucher_id.update({'state': 'done', 'amount_justified': cash_voucher_justified_amount})
        # create bank statement line
        # bank_statement_line_vals = {
        #     'date': self.date,
        #     'payment_ref': _('Cash return for cash voucher %s') % self.cash_voucher_id.name,
        #     'amount':  self.amount,
        #     'journal_id': self.journal_id.id,
        #     'statement_id': self.bank_statement_id.id,
        #     'narration': self.cash_voucher_id.object,
        # }
        # bstl = self.env['account.bank.statement.line'].create(bank_statement_line_vals)
        # cash_return.account_bank_statement_line_id = bstl.id
        return



