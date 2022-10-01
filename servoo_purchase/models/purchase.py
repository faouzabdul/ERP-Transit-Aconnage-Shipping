# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import fields, models, api, _


class Purchase(models.Model):
    _inherit = 'purchase.order'

    need_id = fields.Many2one('servoo.purchase.need', 'Purchase Need', copy=False)
    need_name = fields.Char(related='need_id.name', readonly=True)
    need_description = fields.Text(related='need_id.description', readonly=True)
    need_date = fields.Datetime(related='need_id.date', readonly=True)
    need_employee_id = fields.Many2one(related='need_id.employee_id', readonly=True)
    need_department_id = fields.Many2one(related='need_id.department_id', readonly=True)

    applicant_service_agent_id = fields.Many2one('res.users', 'Applicant Service Agent')
    applicant_service_date = fields.Datetime('Applicant service signature date')
    supply_department_agent_id = fields.Many2one('res.users', 'Supply Department Agent')
    supply_department_date = fields.Datetime('Supply department signature date')
    accounting_department_agent_id = fields.Many2one('res.users', 'Accounting Department Agent')
    accounting_department_date = fields.Datetime('Accounting department signature date')
    management_control_agent_id = fields.Many2one('res.users', 'Management Control Agent')
    management_control_date = fields.Datetime('Management control signature date')
    applicant_direction_agent_id = fields.Many2one('res.users', 'Applicant Management Agent')
    applicant_direction_date = fields.Datetime('Applicant management signature date')
    payment_method = fields.Selection([
        ('check', 'Check'),
        ('bank_transfer', 'Bank transfer'),
        ('cash', 'Cash')
    ], string='Payment method', default='check')

    state = fields.Selection(selection_add=[
        ('submitted', 'Submitted'),
        ('approved_applicant', 'Approved by Applicant Service'),
        ('approved_supply', 'Approved by supply'),
        ('approved_accounting', 'Approved by accounting'),
        ('approved_applicant_direction', 'Approved by applicant direction'),
        ('approved_management_control', 'Approved by management control')
    ])

    def print_quotation(self):
        return self.env.ref('purchase.report_purchase_quotation').report_action(self)

    def button_submit(self):
        self.write({'state': 'submitted'})

    def button_approve_applicant(self):
        self.sudo().write({'state': 'approved_applicant', 'applicant_service_agent_id': self.env.user.id, 'applicant_service_date': fields.Datetime.now()})

    def button_approve_supply(self):
        self.sudo().write({'state': 'approved_supply', 'supply_department_agent_id': self.env.user.id, 'supply_department_date': fields.Datetime.now()})

    def button_approve_accounting(self):
        self.sudo().write({'state': 'approved_accounting', 'accounting_department_agent_id': self.env.user.id, 'accounting_department_date': fields.Datetime.now()})

    def button_approve_applicant_direction(self):
        self.sudo().write({'state': 'approved_applicant_direction', 'applicant_direction_agent_id': self.env.user.id, 'applicant_direction_date': fields.Datetime.now()})

    def button_approve_control(self):
        self.sudo().write({'state': 'approved_management_control', 'management_control_agent_id': self.env.user.id, 'management_control_date': fields.Datetime.now()})
        self.sudo().button_approve()

