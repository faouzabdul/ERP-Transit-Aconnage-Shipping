# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardPaymentRequest(models.TransientModel):
    _name = 'servoo.payment.request.wizard'
    _description = "Payment Request workflow"

    @api.model
    def _get_default_partner(self):
        payment_request = \
        self.env['servoo.payment.request'].search([('id', '=', self.env.context.get('active_id', None))])[0]
        return payment_request.partner_id.id

    @api.model
    def _get_default_state(self):
        payment_request = \
            self.env['servoo.payment.request'].search([('id', '=', self.env.context.get('active_id', None))])[0]
        return payment_request.state

    @api.model
    def _get_default_amount(self):
        payment_request = \
            self.env['servoo.payment.request'].search([('id', '=', self.env.context.get('active_id', None))])[0]
        return payment_request.amount_total

    payment_request_id = fields.Many2one('servoo.payment.request', 'Payment Request', default=lambda self: self.env.context.get('active_id', None))
    state = fields.Selection(related='payment_request_id.state', store=True, readonly=True)
    # state = fields.Char('state', default=_get_default_state)
    observation = fields.Text('Notes')
    date = fields.Datetime('Date', default=lambda self: fields.datetime.now(), required=True)
    # account payment information
    partner_id = fields.Many2one('res.partner', string="Supplier", default=_get_default_partner)
    amount = fields.Float(string="Amount", default=_get_default_amount)
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 domain="[('type', 'in', ('bank','cash'))]",)
    payment_label = fields.Char('Label')
    bank_statement_id = fields.Many2one('account.bank.statement', 'Bank Statement')
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
    ], string='Payment Mode', default='cash')


    def action_validate(self):
        dp = self.get_department(self.sudo().env.user.employee_id.department_id)
        self.payment_request_id.activity_feedback(["servoo_finance.mail_finance_feedback"])
        vals = {}
        if self.payment_request_id.state == 'service_approval':
            if self.sudo().payment_request_id.department_id.id not in dp:
                raise UserError(_("you cannot approve a request from another department or branch"))
            group_direction_approval = self.env.ref("servoo_finance.applicant_direction_approval_group_user")
            users = group_direction_approval.users
            for user in users:
                if user.sudo().employee_id.department_id.id in dp:
                    self.payment_request_id.activity_schedule(
                        "servoo_finance.mail_finance_feedback", user_id=user.id,
                        summary=_("New payment request %s needs the applicant direction approval" % self.payment_request_id.name)
                    )
            vals = {
                'service_approval_agent_id': self.env.user.id,
                'service_approval_date': self.date,
                'state': 'direction_approval',
                'workflow_observation': self.observation
            }
        elif self.payment_request_id.state == 'direction_approval':
            vals = {
                'direction_approval_agent_id': self.env.user.id,
                'direction_approval_date': self.date,
                'state': 'accounting_approval',
                'workflow_observation': self.observation
            }
            group_accounting_approval = self.env.ref("servoo_finance.accounting_approval_group_user")
            users = group_accounting_approval.users
            for user in users:
                self.payment_request_id.activity_schedule(
                    "servoo_finance.mail_finance_feedback", user_id=user.id,
                    summary=_("New payment request %s needs the accounting approval" % self.payment_request_id.name)
                )
        elif self.payment_request_id.state == 'accounting_approval':
            vals = {
                'accounting_approval_agent_id': self.env.user.id,
                'accounting_approval_date': self.date,
                'state': 'management_control_approval',
                'workflow_observation': self.observation
            }
            group_management_control_approval = self.env.ref("servoo_finance.management_control_approval_group_user")
            users = group_management_control_approval.users
            for user in users:
                self.payment_request_id.activity_schedule(
                    "servoo_finance.mail_finance_feedback", user_id=user.id,
                    summary=_("New payment request %s needs the management control approval" % self.payment_request_id.name)
                )
        elif self.payment_request_id.state == 'management_control_approval':
            vals = {
                'management_control_approval_agent_id': self.env.user.id,
                'management_control_approval_date': self.date,
                'state': 'finance_approval',
                'workflow_observation': self.observation
            }
            group_finance_approval = self.env.ref("servoo_finance.finance_approval_group_user")
            users = group_finance_approval.users
            for user in users:
                self.payment_request_id.activity_schedule(
                    "servoo_finance.mail_finance_feedback", user_id=user.id,
                    summary=_("New payment request %s needs the finance approval" % self.payment_request_id.name)
                )
        elif self.payment_request_id.state == 'finance_approval':
            vals = {
                'finance_approval_agent_id': self.env.user.id,
                'finance_approval_date': self.date,
                'state': 'done',
                'workflow_observation': self.observation
            }
            # register payment
            payment_vals = {
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'partner_id': self.partner_id.id,
                'amount': self.amount,
                'date': self.date,
                'journal_id': self.journal_id.id,
                'ref': self.payment_request_id.file_reference,
                'bank_statement_id': self.bank_statement_id.id,
                'receiver': self.receiver,
                'payment_label': self.payment_label,
            }
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            # create entry in bank statement
            # bank_statement_line_vals = {
            #     'date': self.date,
            #     # 'date': datetime.now(),
            #     'payment_ref': _('Payment request %s' % self.payment_request_id.name),
            #     'partner_id': self.partner_id.id,
            #     'amount': -1 * self.amount,
            #     'journal_id': self.journal_id.id,
            #     'narration': self.observation,
            #     'statement_id': self.bank_statement_id.id,
            #     'move_id': payment.move_id.id
            # }
            # self.env['account.bank.statement.line'].create(bank_statement_line_vals)
            vals['account_payment_id'] = payment.id
        return self.payment_request_id.update(vals)

    def action_reject(self):
        vals = {
            'state': 'draft',
            'workflow_observation': self.observation
        }
        self.payment_request_id.activity_feedback(["servoo_finance.mail_finance_feedback"])
        return self.payment_request_id.update(vals)

    def get_child_department(self, dept, result):
        if not dept:
            return
        result.append(dept.id)
        for child in dept.child_ids:
            self.get_child_department(child, result)

    def get_department(self, dept):
        result = []
        self.get_child_department(dept, result)
        return result

