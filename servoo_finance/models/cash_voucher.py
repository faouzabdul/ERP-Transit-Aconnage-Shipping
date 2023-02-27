# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime
from datetime import timedelta


def date_by_adding_business_days(from_date, add_days):
    business_days_to_add = add_days
    current_date = from_date
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        if weekday >= 5: # sunday = 6
            continue
        business_days_to_add -= 1
    return current_date


def date_by_adding_days(from_date, add_days):
    current_date = from_date or datetime.now()
    return current_date + timedelta(add_days)


class CashVoucher(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.cash.voucher'
    _description = 'Cash Voucher'
    _order = 'id desc'

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

    @api.onchange('hinterland', 'date')
    def onchange_hinterland(self):
        delay = 7
        # for request in self:
        if self.hinterland:
            delay = 15
        self.justification_delay = delay
        self.justification_deadline = date_by_adding_days(self.date, delay)

    name = fields.Char('Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    date = fields.Datetime('Date', default=datetime.now())
    employee_id = fields.Many2one('hr.employee', 'Requesting employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(related='employee_id.department_id', related_sudo=False)
    our_voucher = fields.Boolean('Our voucher', compute='_compute_our_vouchers', readonly=True,
                                  search='_search_our_vouchers')
    amount = fields.Float(string='Amount', tracking=1, digits=(6, 3))
    amount_justified = fields.Float(string='Amount justified', digits=(6, 3), tracking=1, default=0.0)
    amount_unjustified = fields.Float(string='Amount unjustified', digits=(6, 3), compute='_compute_unjustified_amount')
    cashier_piece_total_amount = fields.Float('Total cashier piece', compute='_compute_total_cashier_piece')
    object = fields.Text('Object')
    create_uid = fields.Many2one('res.users', string='Created by', index=True, readonly=True)
    cashier_piece_ids = fields.One2many('servoo.cashier.piece', 'cash_voucher_id', 'Cashier Pieces')
    justification_delay = fields.Integer('Justification Delay (days)', default=7)
    hinterland = fields.Boolean('For hinterland operation ?')
    justification_deadline = fields.Date('Justification Deadline', default=onchange_hinterland)
    journal_id = fields.Many2one('account.journal', string='Cash Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, check_company=True,
                                 domain=[('type', '=', 'cash')],
                                 default=_get_default_journal, tracking=3)

    workflow_observation = fields.Text('Observation', tracking=3)

    service_approval_agent_id = fields.Many2one('res.users', 'Service Approval Agent', tracking=2, copy=False)
    service_approval_date = fields.Datetime('Service Approval date', tracking=2, copy=False)

    direction_approval_agent_id = fields.Many2one('res.users', 'Direction Approval Agent', tracking=2, copy=False)
    direction_approval_date = fields.Datetime('Direction approval date', tracking=2, copy=False)

    management_control_approval_agent_id = fields.Many2one('res.users', 'Management control approval agent', tracking=5,
                                                           copy=False)
    management_control_approval_date = fields.Datetime('Management control approval date', tracking=5, copy=False)

    cashier_approval_agent_id = fields.Many2one('res.users', 'Cashier approval agent', tracking=3, copy=False)
    cashier_approval_date = fields.Datetime('Cashier approval date', tracking=3, copy=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('service_approval', 'Service Approval'),
        ('direction_approval', 'Direction Approval'),
        # ('management_control_approval', 'Management Control Approval'),
        ('cashier_approval', 'Cashier Approval'),
        ('justification', 'Justification'),
        ('done', 'Done'),
        # ('justified', 'Justified'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

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

    def _compute_our_vouchers(self):
        for request in self:
            dp = self.get_department(self.sudo().env.user.employee_id.department_id)
            request.our_voucher = request.department_id and request.department_id.id in dp

    def _compute_unjustified_amount(self):
        for request in self:
            request.amount_unjustified = request.amount - request.amount_justified

    def _compute_total_cashier_piece(self):
        for voucher in self:
            amount = 0.0
            for piece in voucher.cashier_piece_ids:
                amount += piece.amount_total
            voucher.cashier_piece_total_amount = amount

    def _search_our_vouchers(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        dp = self.get_department(self.env.user.employee_id.department_id)
        domain = [('department_id', 'in', dp)]
        request_ids = self.env['servoo.cash.voucher']._search(domain)
        return [('id', 'in', request_ids)]

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.cash.voucher') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.cash.voucher') or _('New')
        return super().create(vals)

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_submit(self):
        group_service_approval = self.env.ref("servoo_finance.applicant_service_approval_group_user")
        users = group_service_approval.users
        for user in users:
            if user.sudo().employee_id.department_id.id == self.sudo().department_id.id:
                self.activity_schedule(
                    "servoo_finance.mail_cash_voucher_feedback", user_id=user.id,
                    summary=_("New cash voucher %s needs the applicant service approval" % self.name)
                )
        return self.write({'state': 'service_approval'})
