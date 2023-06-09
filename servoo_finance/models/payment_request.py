# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class PaymentRequest(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.payment.request'
    _description = 'Payment request'
    _order = 'id desc'

    name = fields.Char('Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', 'Partner')
    date = fields.Datetime('Date', default=lambda self: fields.datetime.now())
    employee_id = fields.Many2one('hr.employee', 'Requesting employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(related='employee_id.department_id', related_sudo=False)
    employee_parent_id = fields.Many2one(related='employee_id.parent_id', readonly=False, related_sudo=False)
    our_requests = fields.Boolean('Our payment requests', compute='_compute_our_requests', readonly=True, search='_search_our_requests')
    amount_total = fields.Float(string='Total', store=True, compute='_amount_all', tracking=1)
    file_reference = fields.Char('File Reference')
    file_client_id = fields.Many2one('res.partner', 'Client')
    object = fields.Text('Object')
    request_line = fields.One2many('servoo.payment.request.line', 'payment_request_id', 'Request Lines')
    create_uid = fields.Many2one('res.users', string='Created by', index=True, readonly=True)
    document_ids = fields.One2many('servoo.payment.request.document', 'payment_request_id', 'Documents', tracking=1)
    account_payment_id = fields.Many2one('account.payment', 'Payment')

    workflow_observation = fields.Text('Observation', tracking=3)

    service_approval_agent_id = fields.Many2one('res.users', 'Service Approval Agent', tracking=2, copy=False)
    service_approval_date = fields.Datetime('Service Approval date', tracking=2, copy=False)

    direction_approval_agent_id = fields.Many2one('res.users', 'Direction Approval Agent', tracking=2, copy=False)
    direction_approval_date = fields.Datetime('Direction approval date', tracking=2, copy=False)

    accounting_approval_agent_id = fields.Many2one('res.users', 'Accounting approval Agent', tracking=4, copy=False)
    accounting_approval_date = fields.Datetime('Accounting approval date', tracking=4, copy=False)

    management_control_approval_agent_id = fields.Many2one('res.users', 'Management control approval agent', tracking=5, copy=False)
    management_control_approval_date = fields.Datetime('Management control approval date', tracking=5, copy=False)

    finance_approval_agent_id = fields.Many2one('res.users', 'Finance approval agent', tracking=3, copy=False)
    finance_approval_date = fields.Datetime('Finance approval date', tracking=3, copy=False)

    payment_mode = fields.Selection([
        ('certified_check', 'Certified Check'),
        ('uncertified_check', 'Uncertified Check'),
        ('bank', 'Bank transfer')
    ], string='Payment Mode', required=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('service_approval', 'Service Approval'),
        ('direction_approval', 'Direction Approval'),
        ('accounting_approval', 'Accounting Approval'),
        ('management_control_approval', 'Management Control Approval'),
        ('finance_approval', 'Finance Approval'),
        ('done', 'Done')
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_submit(self):
        if not self.request_line:
            raise UserError(_("No imputation line define! Please add at least one imputation line"))
        group_service_approval = self.env.ref("servoo_finance.applicant_service_approval_group_user")
        users = group_service_approval.users
        for user in users:
            if user.sudo().employee_id.department_id.id == self.sudo().department_id.id:
                self.activity_schedule(
                    "servoo_finance.mail_finance_feedback", user_id=user.id,
                    summary=_("New payment request %s needs the applicant service approval" % self.name)
                )
        return self.write({'state': 'service_approval'})

    @api.depends('request_line.amount')
    def _amount_all(self):
        for request in self:
            amount_total = 0.0
            for line in request.request_line:
                amount_total += line.amount
            request.update({
                'amount_total': amount_total
            })

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

    def _compute_our_requests(self):
        for request in self:
            dp = self.get_department(self.sudo().env.user.employee_id.department_id)
            request.our_requests = request.department_id and request.department_id.id in dp

    def _search_our_requests(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        dp = self.get_department(self.env.user.employee_id.department_id)
        domain = [('department_id', 'in', dp)]
        request_ids = self.env['servoo.payment.request']._search(domain)
        return [('id', 'in', request_ids)]

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.payment.request') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.purchase.need') or _('New')
        return super().create(vals)


class PaymentRequestLine(models.Model):
    _name = 'servoo.payment.request.line'
    _description = 'Payement request line'

    product_id = fields.Many2one('product.product')
    file_reference = fields.Char('File Reference')
    description = fields.Char('Description', required=True)
    amount = fields.Float('Amount', required=True)
    payment_request_id = fields.Many2one('servoo.payment.request', 'Payment Request', required=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            line.description = line.product_id.name

class PaymentRequestDocument(models.Model):
    _name = 'servoo.payment.request.document'
    _description = 'Payment request Document'

    payment_request_id = fields.Many2one('servoo.payment.request', 'Payment Request')
    name = fields.Char('Reference')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'servoo_payment_request_document_attachment_rel',
        'document_id', 'attachment_id',
        string='Attachments')

    @api.model
    def create(self, vals):
        documents = super(PaymentRequestDocument, self).create(vals)
        for document in documents:
            if document.attachment_ids:
                document.attachment_ids.write({'res_model': self._name, 'res_id': document.id})
        return documents

    def write(self, vals):
        documents = super(PaymentRequestDocument, self).write(vals)
        for document in self:
            if document.attachment_ids:
                document.attachment_ids.write({'res_model': self._name, 'res_id': formality.id})
        return documents