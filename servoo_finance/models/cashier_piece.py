# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from . import utils


class CashierPiece(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.cashier.piece'
    _description = 'Cashier piece'
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

    name = fields.Char('Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    date = fields.Datetime('Date', default=datetime.now())
    employee_id = fields.Many2one('hr.employee', 'Requesting employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(related='employee_id.department_id', related_sudo=False)
    employee_parent_id = fields.Many2one(related='employee_id.parent_id', readonly=False, related_sudo=False)
    our_pieces = fields.Boolean('Our cashier pieces', compute='_compute_our_pieces', readonly=True, search='_search_our_pieces')
    amount_total = fields.Float(string='Total', store=True, compute='_amount_all', tracking=1)
    amount_total_letter = fields.Char('Total Signed letter', compute='_compute_display_amount_letter',
                                             store=False)
    file_reference = fields.Char('File Reference')
    object = fields.Text('Object')
    piece_line = fields.One2many('servoo.cashier.piece.line', 'cashier_piece_id', 'Request Lines')
    document_ids = fields.One2many('servoo.cashier.piece.document', 'cashier_piece_id', 'Documents')
    create_uid = fields.Many2one('res.users', string='Created by', index=True, readonly=True)
    cash_voucher_id = fields.Many2one('servoo.cash.voucher', 'Cash Voucher')
    journal_id = fields.Many2one('account.journal', string='Cash Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, check_company=True,
                                 domain=[('type', '=', 'cash')],
                                 default=_get_default_journal)

    workflow_observation = fields.Text('Observation', tracking=3)

    service_approval_agent_id = fields.Many2one('res.users', 'Service Approval Agent', tracking=2, copy=False)
    service_approval_date = fields.Datetime('Service Approval date', tracking=2, copy=False)

    direction_approval_agent_id = fields.Many2one('res.users', 'Direction Approval Agent', tracking=2, copy=False)
    direction_approval_date = fields.Datetime('Direction approval date', tracking=2, copy=False)

    accounting_approval_agent_id = fields.Many2one('res.users', 'Accounting approval Agent', tracking=4, copy=False)
    accounting_approval_date = fields.Datetime('Accounting approval date', tracking=4, copy=False)

    management_control_approval_agent_id = fields.Many2one('res.users', 'Management control approval agent', tracking=5, copy=False)
    management_control_approval_date = fields.Datetime('Management control approval date', tracking=5, copy=False)

    cashier_approval_agent_id = fields.Many2one('res.users', 'Cashier approval agent', tracking=3, copy=False)
    cashier_approval_date = fields.Datetime('Cashier approval date', tracking=3, copy=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('service_approval', 'Service Approval'),
        ('direction_approval', 'Direction Approval'),
        ('cashier_approval', 'Cashier Approval'),
        ('management_control_approval', 'Management Control Approval'),
        ('accounting_approval', 'Accounting Approval'),
        ('done', 'Done')
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    @api.depends('amount_total')
    def _compute_display_amount_letter(self):
        for piece in self:
            piece.amount_total_letter = utils.translate(piece.amount_total).upper()

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_submit(self):
        if not self.piece_line:
            raise UserError(_("No imputation line define! Please add at least one imputation line"))
        group_service_approval = self.env.ref("servoo_finance.applicant_service_approval_group_user")
        users = group_service_approval.users
        for user in users:
            if user.employee_id.department_id.id == self.department_id.id:
                self.activity_schedule(
                    "servoo_finance.mail_cashier_piece_feedback", user_id=user.id,
                    summary=_("New cashier piece %s needs the applicant service approval" % self.name)
                )
        return self.write({'state': 'service_approval'})

    @api.depends('piece_line.amount')
    def _amount_all(self):
        for piece in self:
            amount_total = 0.0
            for line in piece.piece_line:
                amount_total += line.amount
            piece.update({
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

    def _compute_our_pieces(self):
        for piece in self:
            dp = self.get_department(self.env.user.employee_id.department_id)
            piece.our_pieces = piece.department_id and piece.department_id.id in dp

    def _search_our_pieces(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        dp = self.get_department(self.env.user.employee_id.department_id)
        domain = [('department_id', 'in', dp)]
        piece_ids = self.env['servoo.cashier.piece']._search(domain)
        return [('id', 'in', piece_ids)]

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.cashier.piece') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.purchase.need') or _('New')
        return super().create(vals)


class CashierPieceLine(models.Model):
    _name = 'servoo.cashier.piece.line'
    _description = 'Cashier piece line'

    product_id = fields.Many2one('product.product')
    description = fields.Char('Description', required=True)
    amount = fields.Float('Amount', required=True)
    cashier_piece_id = fields.Many2one('servoo.cashier.piece', 'Cashier Piece', required=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            line.description = line.product_id.name


class CashierPieceDocument(models.Model):
    _name = 'servoo.cashier.piece.document'
    _description = 'Cashier Document'

    cashier_piece_id = fields.Many2one('servoo.cashier.piece', 'Cashier Piece')
    name = fields.Char('Reference')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'servoo_cashier_piece_document_attachment_rel',
        'document_id', 'attachment_id',
        string='Attachments')
