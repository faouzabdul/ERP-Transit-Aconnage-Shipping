# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from . import utils
import logging


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_payment(self):
        payment = self.env['account.payment']
        for record in self:
            payments = payment.search([('ref', '=', record.name)])
            record.payment_ids = payments
            record.payment_count = len(payments)


    def _search_payment_ids(self, operator, value):
        if operator == 'in' and value:
            self.env.cr.execute("""
                SELECT array_agg(so.id)
                    FROM sale_order so
                    JOIN account_payment ap ON ap.ref = so.name
                WHERE
                    ap.payment_type = 'inbound' AND
                    ap.id = ANY(%s)
            """, (list(value),))
            so_ids = self.env.cr.fetchone()[0] or []
            return [('id', 'in', so_ids)]
        elif operator == '=' and not value:
            order_ids = self._search()
            return [('id', 'not in', order_ids)]
        return []

    paid_amount = fields.Float('Paid Amount', compute='_get_amount_paid')
    payment_count = fields.Integer(string='Payment Count', compute='_get_payment')
    payment_ids = fields.Many2many("account.payment", 'account_payment_sale_order_rel', string='Payments',
                                   compute="_get_payment", copy=False, search="_search_payment_ids")

    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
    ], string="Payment Status", store=True, default='not_paid',
        readonly=True, copy=False, tracking=True)


    def _get_amount_paid(self):
        for sale in self:
            amount = 0.0
            for payment in sale.payment_ids:
                amount += payment.amount
            sale.paid_amount = amount

    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current operation """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, group_by=False),
                domain=[('ref', '=', self.name)]
            )
            return res
        return False