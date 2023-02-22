# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class AccountCashboxLine(models.Model):
    _inherit = 'account.cashbox.line'

    @api.depends('coin_value', 'good_coin_number', 'bad_coin_number')
    def _sub_total_coin(self):
        """ Calculates Sub total"""
        for cashbox_line in self:
            cashbox_line.good_coin_subtotal = cashbox_line.coin_value * cashbox_line.good_coin_number
            cashbox_line.bad_coin_subtotal = cashbox_line.coin_value * cashbox_line.bad_coin_number

    # good_coin_number = fields.Integer('#Coins/Bills in good condition', default=lambda self: self.number)
    good_coin_number = fields.Integer(related='number', string='#Coins/Bills in good condition', readonly=False, store=True)
    good_coin_subtotal = fields.Float(compute='_sub_total_coin', string='Subtotal good coins', digits=0, readonly=True)
    bad_coin_number = fields.Integer('#Coins/Bills defective', default=0)
    bad_coin_subtotal = fields.Float(compute='_sub_total_coin', string='Subtotal bad coins', digits=0, readonly=True)

    @api.onchange('good_coin_number')
    def onchange_good_coin(self):
        self.bad_coin_number = self.number - self.good_coin_number

    @api.onchange('bad_coin_number')
    def onchange_bad_coin(self):
        self.good_coin_number = self.number - self.bad_coin_number

class AccountCashControlReport(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'account.cash.control.report'
    _description = 'Cash Control Report'

    name = fields.Char('Reference')
    date = fields.Date('Date')
    cash_statement_id = fields.Many2one('account.bank.statement', 'Cash Statement')
    journal_id = fields.Many2one(related='cash_statement_id.journal_id')
    currency_id = fields.Many2one('res.currency', related='journal_id.currency_id')
    cashbox_end_id = fields.Many2one(related='cash_statement_id.cashbox_end_id', string="Ending Cashbox")
    cashbox_lines_ids = fields.One2many(related='cashbox_end_id.cashbox_lines_ids')
    balance_start = fields.Monetary(related='cash_statement_id.balance_start')
    balance_end_real = fields.Monetary(related='cash_statement_id.balance_end_real')
    cash_voucher_ids = fields.Many2many('servoo.cash.voucher', 'account_cash_control_voucher_rel', string='Cash Vouchers')
    cash_voucher_count = fields.Integer(compute="_get_cash_vouchers", string='Cash voucher count')
    cash_voucher_amount = fields.Float(compute="_compute_cash_voucher_amount", string='Cash voucher amount')
    theoretical_balance = fields.Float(compute="_compute_theoretical_balance", string='Theoretical Balance')
    state = fields.Selection([
        ('edited', 'Edited'),
        ('controlled', 'Controlled')
    ], string='State', tracking=1, default='edited')
    cashier_agent_id = fields.Many2one('res.users', 'Cashier Agent', tracking=2, copy=False)
    cashier_date = fields.Datetime('Cashier date', tracking=2, copy=False)
    cashier_cni = fields.Char('Cashier CNI', tracking=2)
    cashier_note = fields.Text('Cashier Notes')

    controller_agent_id = fields.Many2one('res.users', 'Controller Agent', tracking=2, copy=False)
    controller_date = fields.Datetime('Control date', tracking=2, copy=False)
    controller_cni = fields.Char('Controller CNI')
    controller_note = fields.Text('Controller Notes')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.cash.voucher') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.cash.control.report') or _('New')
        return super().create(vals)


    def _get_cash_vouchers(self):
        for record in self:
            record.cash_voucher_count = len(record.cash_voucher_ids)

    def _compute_cash_voucher_amount(self):
        for record in self:
            amount = 0.0
            for cv in record.cash_voucher_ids:
                amount += cv.amount
            record.cash_voucher_amount = amount

    def _compute_theoretical_balance(self):
        for record in self:
            record.theoretical_balance = record.balance_start - record.cash_voucher_amount
