# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCashVoucher(models.TransientModel):
    _name = 'servoo.cash.voucher.wizard'
    _description = "Payment Request workflow"

    @api.model
    def _get_default_journal(self):
        journal_types = ['cash']
        journal = self._search_default_journal(journal_types)
        return journal

    @api.model
    def _search_default_journal(self, journal_types):
        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]
        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain, limit=1)
        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)
        if not journal:
            company = self.env['res.company'].browse(company_id)
            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)
        return journal

    cash_voucher_id = fields.Many2one('servoo.cash.voucher', 'Payment Request', default=lambda self: self.env.context.get('active_id', None))
    state = fields.Selection(related='cash_voucher_id.state', store=True, readonly=True)
    observation = fields.Text('Notes')
    date = fields.Date('Date', default=datetime.now(), required=True)
    journal_id = fields.Many2one('account.journal', string='Cash Journal', check_company=True,
                                 domain=[('type', '=', 'cash')],
                                 default=_get_default_journal)

    def action_validate(self):
        dp = self.get_department(self.env.user.employee_id.department_id)
        self.cash_voucher_id.activity_feedback(["servoo_finance.mail_cash_voucher_feedback"])
        vals = {}
        if self.cash_voucher_id.state == 'service_approval':
            if self.cash_voucher_id.department_id.id not in dp:
                raise UserError(_("you cannot approve a request from another department or branch"))
            group_direction_approval = self.env.ref("servoo_finance.applicant_direction_approval_group_user")
            users = group_direction_approval.users
            for user in users:
                if user.employee_id.department_id.id in dp:
                    self.cash_voucher_id.activity_schedule(
                        "servoo_finance.mail_cash_voucher_feedback", user_id=user.id,
                        summary=_("New cash voucher %s needs the applicant direction approval" % self.cash_voucher_id.name)
                    )
            vals = {
                'service_approval_agent_id': self.env.user.id,
                'service_approval_date': self.date,
                'state': 'direction_approval',
                'workflow_observation': self.observation
            }
        elif self.cash_voucher_id.state == 'direction_approval':
            vals = {
                'direction_approval_agent_id': self.env.user.id,
                'direction_approval_date': self.date,
                'state': 'management_control_approval',
                'workflow_observation': self.observation
            }
            group_management_control = self.env.ref("servoo_finance.management_control_approval_group_user")
            users = group_management_control.users
            for user in users:
                self.cash_voucher_id.activity_schedule(
                    "servoo_finance.mail_cash_voucher_feedback", user_id=user.id,
                    summary=_("New cash voucher %s needs the management control approval" % self.cash_voucher_id.name)
                )
        elif self.cash_voucher_id.state == 'management_control_approval':
            vals = {
                'management_control_approval_agent_id': self.env.user.id,
                'management_control_approval_date': self.date,
                'state': 'cashier_approval',
                'workflow_observation': self.observation
            }
            group_cashier_approval = self.env.ref("servoo_finance.cashier_group_user")
            users = group_cashier_approval.users
            for user in users:
                self.cash_voucher_id.activity_schedule(
                    "servoo_finance.mail_cash_voucher_feedback", user_id=user.id,
                    summary=_("New cash voucher %s needs the cashier approval" % self.cash_voucher_id.name)
                )
        elif self.cash_voucher_id.state == 'cashier_approval':
            vals = {
                'cashier_approval_agent_id': self.env.user.id,
                'cashier_approval_date': self.date,
                'state': 'justification',
                'workflow_observation': self.observation
            }
            self.cash_voucher_id.journal_id = self.journal_id.id
        return self.cash_voucher_id.update(vals)

    def action_reject(self):
        vals = {
            'state': 'draft',
            'workflow_observation': self.observation
        }
        self.cash_voucher_id.activity_feedback(["servoo_finance.mail_cash_voucher_feedback"])
        return self.cash_voucher_id.update(vals)

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
