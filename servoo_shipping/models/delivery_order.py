# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class DeliveryOrder(models.Model):
    _name = 'servoo.shipping.delivery.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Delivery Order'
    _order = 'id desc'

    name = fields.Char('Name', required=True, tracking=1, default=lambda self: _('New'), copy=False)
    date = fields.Date('Date', default=lambda self: fields.datetime.now())
    validity_date = fields.Date('Validity Date', default=lambda self: fields.datetime.now() + timedelta(days=3))
    bl_id = fields.Many2one('servoo.shipping.bl', 'Bill of lading', required=True)
    custom_declaration_reference = fields.Char('Custom Declaration', required=True)
    custom_declaration_date = fields.Date('Custom Declaration Date', required=True)
    consignee_id = fields.Many2one('res.partner', related='bl_id.consignee_id')
    shipper_id = fields.Many2one('res.partner', related='bl_id.shipper_id')
    warehouse = fields.Char('Warehouse')
    loading_port = fields.Many2one('res.locode', related='bl_id.loading_port')
    discharge_port = fields.Many2one('res.locode', related='bl_id.discharge_port')
    vessel_id = fields.Many2one('res.transport.means', related='bl_id.vessel_id')
    goods_description = fields.Text('Description', compute='_compute_goods_description', store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.shipping.bl') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.shipping.delivery.order') or _('New')
        return super().create(vals)

    @api.depends('bl_id')
    def _compute_goods_description(self):
        for order in self:
            description = ""
            if order.bl_id:
                for good in order.bl_id.good_ids:
                    description += good.name
                    if good.quantity > 0.0 and good.unit_id:
                        description += ' ' + _('Qty: ') + str(good.quantity) + ' ' + str(good.unit_id.name)
                    if good.gross_weight and good.gross_weight > 0.0:
                        description += ' ' + _('Gross weight (kg): ') + str(good.gross_weight)
                    description += '\n'
            order.goods_description = description


