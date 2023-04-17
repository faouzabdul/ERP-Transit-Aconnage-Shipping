# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime
from datetime import date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class WizardCashierPiece(models.TransientModel):
    _name = 'servoo.cashier.piece.wizard'
    _description = "Cashier Piece workflow"

    cashier_piece_id = fields.Many2one('servoo.cashier.piece', 'Cashier Piece', default=lambda self: self.env.context.get('active_id', None))
    state = fields.Selection(related='cashier_piece_id.state', store=True, readonly=True)
    observation = fields.Text('Notes')
    date = fields.Date('Date', default=datetime.now(), required=True)

    def action_validate(self):
        dp = self.get_department(self.sudo().env.user.employee_id.department_id)
        self.cashier_piece_id.activity_feedback(["servoo_finance.mail_cashier_piece_feedback"])
        vals = {}
        if self.cashier_piece_id.state == 'service_approval':
            if self.sudo().cashier_piece_id.department_id.id not in dp:
                raise UserError(_("you cannot approve a piece from another department or branch"))
            group_direction_approval = self.env.ref("servoo_finance.applicant_direction_approval_group_user")
            users = group_direction_approval.users
            for user in users:
                if user.sudo().employee_id.department_id.id in dp:
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
            # Process the cash voucher if the cashier piece has one
            if self.cashier_piece_id.cash_voucher_id:
                self.cashier_piece_id.cash_voucher_id.amount_justified +=  self.cashier_piece_id.amount_total
            if self.cashier_piece_id.cash_voucher_id.amount_unjustified <= 0:
                self.cashier_piece_id.cash_voucher_id.state = 'done'
            # Create bank statement line
            # if not self.cashier_piece_id.cash_voucher_id:
            # get the active bank statement for the current journal and day
            bank_statement = self.env['account.bank.statement'].search([
                ('journal_id', '=', self.cashier_piece_id.journal_id.id),
                ('date', '=', datetime.now()),
                ('state', '=', 'open'),
            ])
            # raise UserError('bank_statement %s' % bank_statement)
            # if there is not statement, raise en exception
            if not bank_statement:
                raise UserError(_("No %s cash statement is open for the day of %s. You must first open a cash statement for this day") % (self.cashier_piece_id.journal_id.name, date.today()))
            # prepare bank statement line
            bank_statement_line_vals = {
                'date': datetime.now(),
                'payment_ref': _('Payment of the cash piece %s' % self.cashier_piece_id.name),
                'beneficiary': self.sudo().cashier_piece_id.employee_id.name,
                'amount': -1 * self.cashier_piece_id.amount_total,
                'journal_id': self.cashier_piece_id.journal_id.id,
                'narration': self.cashier_piece_id.object,
                'statement_id': max([st.id for st in bank_statement]),
            }
            bank_statement_line = self.env['account.bank.statement.line'].create(bank_statement_line_vals)
            self.cashier_piece_id.account_bank_statement_line_id = bank_statement_line.id
            group_management_control_approval = self.env.ref("servoo_finance.management_control_approval_group_user")
            users = group_management_control_approval.users
            for user in users:
                self.cashier_piece_id.activity_schedule(
                    "servoo_finance.mail_cashier_piece_feedback", user_id=user.id,
                    summary=_("New cashier piece %s needs the management control approval" % self.cashier_piece_id.name)
                )
        elif self.cashier_piece_id.state == 'management_control_approval':
            for line in self.cashier_piece_id.piece_line:
                if not line.analytic_account_id and (line.account_id and line.account_id.code[0] in ('6', '7')):
                    raise UserError(_("You must set analytic account for income and expenses"))
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
            # Check if all line have account code define
            for line in self.cashier_piece_id.piece_line:
                if not line.account_id:
                    raise UserError(_("You must set account for all lines"))
            # Check if income and expenses line has analytic account
            for line in self.cashier_piece_id.piece_line:
                if not line.analytic_account_id and (line.account_id and line.account_id.code[0] in ('6', '7')):
                    raise UserError(_("You must set analytic account for income and expenses"))
            # Create account move from cashier piece
            lines = []
            vals_debit = (0, 0, {
                'account_id': self.cashier_piece_id.journal_id.default_account_id.id,
                'name': self.cashier_piece_id.name,
                'debit': 0,
                'credit': self.cashier_piece_id.amount_total,
            })
            lines.append(vals_debit)
            for line in self.cashier_piece_id.piece_line:
                lines.append((0, 0, {
                    'account_id': line.account_id.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, [at.id for at in line.analytic_tag_ids])],
                    'partner_id': line.partner_id.id,
                    'name': line.description,
                    'debit': line.amount,
                    'credit': 0
                }))
            account_move_vals = {
                'journal_id': self.cashier_piece_id.journal_id.id,
                'date': datetime.now(),
                'line_ids': lines,
                'ref': self.cashier_piece_id.name
            }
            move = self.env['account.move'].create(account_move_vals)
            move.action_post()
            vals = {
                'accounting_approval_agent_id': self.env.user.id,
                'accounting_approval_date': self.date,
                'state': 'done',
                'workflow_observation': self.observation,
                'account_move_id': move.id
            }
            # if the cashier piece has a bank statement line, link the move to this
            if self.cashier_piece_id.account_bank_statement_line_id:
                self.cashier_piece_id.account_bank_statement_line_id.move_id = move.id
            # TODO
            # See what to do if the account bank statement line is already reconciled
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

