# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, models, fields, _
from datetime import datetime


class FormalityType(models.Model):
    _name = 'servoo.logistic.formality.type'
    _description = "Formality Type"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')


class Formality(models.Model):
    _name = 'servoo.logistic.formality'
    _description = "Formality"

    service_id = fields.Many2one('product.product', 'Service')
    name = fields.Char('Description')
    other_reference = fields.Char('Other reference')
    start_date = fields.Datetime('Start Date', default=lambda self: fields.datetime.now())
    end_date = fields.Datetime('End Date')
    amount = fields.Float('Amount', digits='Product Price')
    operation_id = fields.Many2one('servoo.logistic.operation', 'Operation', required=True, ondelete='cascade', index=True, copy=False)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'servoo_logistic_formality_attachment_rel',
        'formality_id', 'attachment_id',
        string='Attachments')
    administration_id = fields.Many2one('res.partner', 'Partner')
    agent_id = fields.Many2one('res.users', 'Agent')
    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', default='open')
    tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})

    @api.model
    def create(self, vals):
        formalities = super(Formality, self).create(vals)
        for formality in formalities:
            if formality.attachment_ids:
                formality.attachment_ids.write({'res_model': self._name, 'res_id': formality.id})
        return formalities

    def write(self, vals):
        formalities = super(Formality, self).write(vals)
        for formality in self:
            if formality.attachment_ids:
                formality.attachment_ids.write({'res_model': self._name, 'res_id': formality.id})
        return formalities

    def _compute_tax_id(self):
        for line in self:
            taxes = line.service_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_id = taxes

    @api.onchange('service_id')
    def onchange_service_id(self):
        """
        Trigger the change of amount when the service is modified
        """
        if self.service_id:
            self.amount = self.service_id.list_price
            self.name = self.service_id.name
        self._compute_tax_id()

    @api.onchange('end_date')
    def onchange_end_date(self):
        if self.end_date:
            self.action_done()
        else:
            self.action_open()

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_done(self):
        datas = {'state': 'done'}
        for item in self:
            if not item.end_date:
                datas['end_date'] = datetime.now()
        return self.write(datas)
    
    def action_open(self):
        return self.write({'state': 'open'})
