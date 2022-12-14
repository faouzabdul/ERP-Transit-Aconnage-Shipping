# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class CashVoucher(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.cash.voucher'
    _description = 'Cash Voucher'
    _order = 'id desc'

    name = fields.Char('Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    date = fields.Datetime('Date', default=datetime.now())
    employee_id = fields.Many2one('hr.employee', 'Requesting employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(related='employee_id.department_id', related_sudo=False)
    our_voucher = fields.Boolean('Our voucher', compute='_compute_our_vouchers', readonly=True,
                                  search='_search_our_vouchers')
    amount = fields.Float(string='Amount', tracking=1, digits=(6, 2))
    object = fields.Text('Object')
    create_uid = fields.Many2one('res.users', string='Created by', index=True, readonly=True)

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
        ('management_control_approval', 'Management Control Approval'),
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
            dp = self.get_department(self.env.user.employee_id.department_id)
            request.our_voucher = request.department_id and request.department_id.id in dp

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
            if user.employee_id.department_id.id == self.department_id.id:
                self.activity_schedule(
                    "servoo_finance.mail_cash_voucher_feedback", user_id=user.id,
                    summary=_("New cash voucher %s needs the applicant service approval" % self.name)
                )
        return self.write({'state': 'service_approval'})
