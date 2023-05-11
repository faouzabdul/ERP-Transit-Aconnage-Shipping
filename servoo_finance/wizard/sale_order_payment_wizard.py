# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
import logging
from odoo.exceptions import UserError, ValidationError


class WizardSaleOrderPayment(models.TransientModel):
    _name = 'sale.order.payment.wizard'
    _description = 'Sale order payment wizard'

    @api.model
    def _get_amount(self):
        order = self.env['sale.order'].search([('id', '=', self.env.context.get('active_id', None))])[0]
        if order.currency_id.name == 'XAF':
            return order.amount_total
        else:
            return order.amount_other_currency


    order_id = fields.Many2one('sale.order', 'Sale Order', default=lambda self: self.env.context.get('active_id', None))
    journal_id = fields.Many2one('account.journal', store=True, readonly=False,
                                 domain="[('type', 'in', ('bank', 'cash'))]")
    payment_date = fields.Date(string="Payment Date", required=True,
                               default=fields.Date.context_today)
    amount = fields.Monetary(currency_field='currency_id', default=_get_amount)
    communication = fields.Char(string="Memo")

    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
                                  compute='_compute_currency_id',
                                  help="The payment's currency.")
    source_currency_id = fields.Many2one('res.currency',
                                         string='Source Currency', store=True, copy=False,
                                         compute='_compute_from_lines',
                                         help="The payment's currency.")
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
                                             readonly=False, store=True,
                                             compute='_compute_payment_method_line_id',
                                             domain="[('id', 'in', available_payment_method_line_ids)]")

    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')
    hide_payment_method_line = fields.Boolean(
        compute='_compute_payment_method_line_fields',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    bank_statement_id = fields.Many2one('account.bank.statement', 'Bank Statement')
    receiver = fields.Selection([
        ('pad', 'PAD'),
        ('other', 'Other'),
        ('apm', 'APM')
    ], string='Receiver')
    payment_mode = fields.Selection([
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('bank_draft', 'Bank Draft')
    ], string='Payment Mode')


    @api.depends('journal_id')
    def _compute_currency_id(self):
        for pay in self:
            pay.currency_id = pay.journal_id.currency_id or pay.journal_id.company_id.currency_id

    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
        '''
        for pay in self:
            available_payment_method_lines = pay.available_payment_method_line_ids
            # Select the first available one by default.
            if pay.payment_method_line_id in available_payment_method_lines:
                pay.payment_method_line_id = pay.payment_method_line_id
            elif available_payment_method_lines:
                pay.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                pay.payment_method_line_id = False

    @api.depends('journal_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines('inbound')
            to_exclude = []
            if to_exclude:
                pay.available_payment_method_line_ids = pay.available_payment_method_line_ids.filtered(
                    lambda x: x.code not in to_exclude)
            if pay.payment_method_line_id.id not in pay.available_payment_method_line_ids.ids:
                # In some cases, we could be linked to a payment method line that has been unlinked from the journal.
                # In such cases, we want to show it on the payment.
                pay.hide_payment_method_line = False
            else:
                pay.hide_payment_method_line = len(
                    pay.available_payment_method_line_ids) == 1 and pay.available_payment_method_line_ids.code == 'manual'

    def action_create_payments(self):
        vals = {
            'payment_state' : 'paid'
        }
        amount = self.order_id.amount_total
        paid_amount = self.order_id.paid_amount
        if self.currency_id.id != self.order_id.currency_id.id:
            amount = self.order_id.amount_other_currency
        if (paid_amount + self.amount) < amount:
            vals['payment_state'] = 'partial'
        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.order_id.partner_id.id,
            'amount': self.amount,
            'date': self.payment_date,
            'journal_id': self.journal_id.id,
            'payment_reference': self.communication,
            'ref': self.order_id.name,
            'payment_method_line_id': self.payment_method_line_id.id,
            'bank_statement_id': self.bank_statement_id.id,
            'payment_mode': self.payment_mode,
            'receiver': self.receiver
        }
        vals['paid_amount'] = paid_amount + self.amount
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()
        return self.order_id.update(vals)



