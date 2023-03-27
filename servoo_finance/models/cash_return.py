# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class CashReturn(models.Model):
    _name = 'servoo.cash.return'
    _description = 'Cash Return'

    name = fields.Char('Reference')
    date = fields.Datetime('Date')
    cash_voucher_id = fields.Many2one('servoo.cash.voucher', 'Cash Voucher')
    journal_id = fields.Many2one('account.journal', string='Cash Journal', readonly=True,
                                 domain=[('type', '=', 'cash')])
    amount = fields.Float('Amount')
    account_bank_statement_line_id = fields.Many2one('account.bank.statement.line', 'Bank statement line',
                                                     readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.cash.return') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.cash.return') or _('New')
        return super().create(vals)
