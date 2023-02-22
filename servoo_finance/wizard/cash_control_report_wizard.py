# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCashControlReportCreate(models.TransientModel):
    _name ='account.cash.control.report.create.wizard'
    _description = 'Create Cash control'

    @api.model
    def _get_cash_voucher(self):
        cash_vouchers = self.env['servoo.cash.voucher'].search([
            ('journal_id', '=', self.journal_id.id),
            ('cashier_approval_date', '=', self.date),
            ('cashier_approval_agent_id', '=', self.env.user.id)
        ])
        return [(6, 0, [cv.id for cv in cash_vouchers])]

    cash_statement_id = fields.Many2one('account.bank.statement', 'Cash Statement', default=lambda self: self.env.context.get('active_id', None))
    name = fields.Char('Reference')
    date = fields.Date('Date', default=datetime.now())
    journal_id = fields.Many2one(related='cash_statement_id.journal_id')
    currency_id = fields.Many2one('res.currency', related='journal_id.currency_id')
    cashbox_end_id = fields.Many2one(related='cash_statement_id.cashbox_end_id', string="Ending Cashbox")
    cashbox_lines_ids = fields.One2many(related='cashbox_end_id.cashbox_lines_ids', readonly=False)
    balance_start = fields.Monetary(related='cash_statement_id.balance_start')
    balance_end_real = fields.Monetary(related='cash_statement_id.balance_end_real')
    cash_voucher_ids = fields.Many2many('servoo.cash.voucher','wizard_cash_control_voucher_rel', string='Cash Vouchers', default=_get_cash_voucher)
    cash_voucher_count = fields.Integer(compute="_get_cash_vouchers", string='Cash voucher count')
    cash_voucher_amount = fields.Float(compute="_compute_cash_voucher_amount", string='Cash voucher amount')
    theoretical_balance = fields.Float(compute="_compute_theoretical_balance", string='Theoretical Balance')
    cashier_agent_id = fields.Many2one('res.users', 'Service Approval Agent', default=lambda self: self.env.user.id)
    cashier_date = fields.Datetime('Service Approval date', default=datetime.now())
    cashier_cni = fields.Char('Cashier CNI')
    cashier_note = fields.Text('Cashier Notes')

    @api.onchange('date')
    def onchange_date(self):
        cash_vouchers = self.env['servoo.cash.voucher'].search([
            ('journal_id', '=', self.journal_id.id),
            ('cashier_approval_date', '=', self.date),
            ('cashier_approval_agent_id', '=', self.env.user.id)
        ])
        amount = 0.0
        voucher_ids=[]
        for cv in cash_vouchers:
            amount += cv.amount
            voucher_ids.append(cv.id)
        self.cash_voucher_ids = [(6, 0, voucher_ids)]
        self.cash_voucher_count = len(cash_vouchers)
        self.cash_voucher_amount = amount
        self.theoretical_balance = self.balance_start - amount


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

    def create_report(self):
        vals = {
            # 'name': self.name,
            'date': self.date,
            'cash_statement_id' : self.cash_statement_id.id,
            'cashier_agent_id' : self.env.user.id,
            'cashier_date': self.cashier_date,
            'cashier_cni': self.cashier_cni,
            'cashier_note': self.cashier_note,
            'cash_voucher_ids' : [(6, 0, [cv.id for cv in self.cash_voucher_ids])]
        }
        cash_control = self.env['account.cash.control.report'].create(vals)
        group_controller_approval = self.env.ref("servoo_finance.cash_report_controller_group_user")
        users = group_controller_approval.users
        for user in users:
            cash_control.activity_schedule(
                "servoo_finance.mail_cash_control_report_feedback", user_id=user.id,
                summary=_("New cash report %s needs to be controlled" % self.name)
            )
        return



class WizardCashControlReportApprove(models.TransientModel):
    _name = 'account.cash.control.report.approve.wizard'
    _description = 'Approve Cash control wizard'

    cash_control_report_id = fields.Many2one('account.cash.control.report', 'Cash control reporty',
                                        default=lambda self: self.env.context.get('active_id', None))
    controller_agent_id = fields.Many2one('res.users', 'Controller Agent', default=lambda self: self.env.user.id)
    controller_date = fields.Datetime('Control date', default=datetime.now())
    controller_cni = fields.Char('Controller CNI')
    controller_note = fields.Text('Controller Notes')

    def action_approve(self):
        self.cash_control_report_id.activity_feedback(["servoo_finance.mail_cash_control_report_feedback"])
        vals = {
            'state' : 'controlled',
            'controller_agent_id': self.env.user.id,
            'controller_date': self.controller_date,
            'controller_cni': self.controller_cni,
            'controller_note': self.controller_note
        }
        self.cash_control_report_id.write(vals)