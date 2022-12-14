# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class WizardCashierPiece(models.TransientModel):
    _name = 'servoo.cashier.piece.wizard'
    _description = "Cashier Piece workflow"

    cashier_piece_id = fields.Many2one('servoo.cashier.piece', 'Cashier Piece', default=lambda self: self.env.context.get('active_id', None))
    observation = fields.Text('Notes')
    date = fields.Date('Date', default=datetime.now(), required=True)

    def action_validate(self):
        dp = self.get_department(self.env.user.employee_id.department_id)
        self.cashier_piece_id.activity_feedback(["servoo_finance.mail_cashier_piece_feedback"])
        vals = {}
        if self.cashier_piece_id.state == 'service_approval':
            if self.cashier_piece_id.department_id.id not in dp:
                raise UserError(_("you cannot approve a piece from another department or branch"))
            group_direction_approval = self.env.ref("servoo_finance.applicant_direction_approval_group_user")
            users = group_direction_approval.users
            for user in users:
                if user.employee_id.department_id.id in dp:
                    self.cashier_piece_id.activity_schedule(
                        "servoo_finance.mail_cashier_piece_feedback", user_id=user.id,
                        summary=_("New cashier piece %s needs the applicant direction approval" % self.cashier_piece_id.name)
                    )
            vals = {
                'service_approval_agent_id': self.env.user.id,
                'service_approval_date': self.date,
                'state': 'direction_approval',
                'workflow_observation': self.observation
            }
        elif self.cashier_piece_id.state == 'direction_approval':
            vals = {
                'direction_approval_agent_id': self.env.user.id,
                'direction_approval_date': self.date,
                'state': 'cashier_approval',
                'workflow_observation': self.observation
            }
            group_cashier = self.env.ref("servoo_finance.cashier_group_user")
            users = group_cashier.users
            for user in users:
                self.cashier_piece_id.activity_schedule(
                    "servoo_finance.mail_cashier_piece_feedback", user_id=user.id,
                    summary=_("New cashier piece %s needs the cashier approval" % self.cashier_piece_id.name)
                )
        elif self.cashier_piece_id.state == 'cashier_approval':
            vals = {
                'cashier_approval_agent_id': self.env.user.id,
                'cashier_approval_date': self.date,
                'state': 'management_control_approval',
                'workflow_observation': self.observation
            }
            group_management_control_approval = self.env.ref("servoo_finance.management_control_approval_group_user")
            users = group_management_control_approval.users
            for user in users:
                self.cashier_piece_id.activity_schedule(
                    "servoo_finance.mail_cashier_piece_feedback", user_id=user.id,
                    summary=_("New cashier piece %s needs the management control approval" % self.cashier_piece_id.name)
                )
        elif self.cashier_piece_id.state == 'management_control_approval':
            vals = {
                'management_control_approval_agent_id': self.env.user.id,
                'management_control_approval_date': self.date,
                'state': 'accounting_approval',
                'workflow_observation': self.observation
            }
            group_accounting_approval = self.env.ref("servoo_finance.accounting_approval_group_user")
            users = group_accounting_approval.users
            for user in users:
                self.cashier_piece_id.activity_schedule(
                    "servoo_finance.mail_cashier_piece_feedback", user_id=user.id,
                    summary=_("New cashier piece %s needs the accounting approval" % self.cashier_piece_id.name)
                )
        elif self.cashier_piece_id.state == 'accounting_approval':
            vals = {
                'accounting_approval_agent_id': self.env.user.id,
                'accounting_approval_date': self.date,
                'state': 'done',
                'workflow_observation': self.observation
            }
            if self.cashier_piece_id.cash_voucher_id.state == 'justification':
                self.cashier_piece_id.cash_voucher_id.state = 'done'
        return self.cashier_piece_id.update(vals)

    def action_reject(self):
        vals = {
            'state': 'draft',
            'workflow_observation': self.observation
        }
        self.cashier_piece_id.activity_feedback(["servoo_finance.mail_cashier_piece_feedback"])
        return self.cashier_piece_id.update(vals)

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

