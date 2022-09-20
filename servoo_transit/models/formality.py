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
    name = fields.Char('Reference')
    other_reference = fields.Char('Other reference')
    start_date = fields.Datetime('Start Date', default=datetime.now())
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

    @api.onchange('service_id')
    def onchange_service_id(self):
        """
        Trigger the change of amount when the service is modified
        """
        if self.service_id:
            self.amount = self.service_id.list_price

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
