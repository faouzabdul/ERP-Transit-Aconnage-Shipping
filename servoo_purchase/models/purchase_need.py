# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)


class PurchaseNeed(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.purchase.need'
    _description = 'Purchase need'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    description = fields.Text('Description')
    date = fields.Datetime('Date', default=datetime.now())
    employee_id = fields.Many2one('hr.employee', 'Requesting employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(related='employee_id.department_id', related_sudo=False)
    employee_parent_id = fields.Many2one(related='employee_id.parent_id', readonly=False, related_sudo=False)
    note = fields.Text('Notes', index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('validated', 'Validated'),
        ('approved', 'Approved'),
        ('canceled', 'Canceled'),
        ('done', 'Done')
    ], string='State', index=True, default='draft')
    user_id = fields.Many2one('res.users', 'User')
    our_needs = fields.Boolean('Our Needs', compute='_compute_our_needs',readonly=True, search='_search_our_needs')

    def _compute_our_needs(self):
        for need in self:
            need.our_needs = need.department_id and need.department_id.id != self.env.user.employee_id.department_id.id
            _logger.info("Besoin %s : %s" % (need.name, need.our_needs))

    def _search_our_needs(self, operator, value):
        if operator not in ['=', '!=']:
            raise ValueError(_('This operator is not supported'))
        if not isinstance(value, bool):
            raise ValueError(_('Value should be True or False (not %s)'), value)
        domain = [('department_id', '=', self.env.user.employee_id.department_id.id)]
        need_ids = self.env['servoo.purchase.need']._search(domain)
        return [('id', 'in', need_ids)]

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.purchase.need') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.purchase.need') or _('New')
        return super().create(vals)

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_submit(self):
        users = self.env['res.users'].search([('employee_id', '=', self.employee_parent_id.id)])
        for user in users:
            self.activity_schedule(
                "servoo_purchase.mail_purchase_need_feedback", user_id=user.id,
                summary=_("New purchase need %s needs to be validate" % self.name)
            )
        return self.write({'state': 'submitted'})

    def action_validate(self):
        if self.employee_parent_id and self.employee_parent_id.id != self.env.user.employee_id.id:
            raise UserError(_("You are not the validator of this purchase need."))
        self.activity_feedback(["servoo_purchase.mail_purchase_need_feedback"])
        group_approver = self.env.ref("servoo_purchase.purchase_need_approver_group_user")
        users = group_approver.users
        for user in users:
            self.activity_schedule(
                "servoo_purchase.mail_purchase_need_feedback", user_id=user.id,
                summary=_("New purchase need %s needs to be approve" % self.name)
            )
        return self.write({'state': 'validated'})

    def action_super_validate(self):
        return self.write({'state': 'validated'})

    def action_approve(self):
        self.activity_feedback(["servoo_purchase.mail_purchase_need_feedback"])
        return self.write({'state': 'approved'})

    def action_done(self):
        return self.write({'state': 'done'})
