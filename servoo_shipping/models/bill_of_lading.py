# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _


class BillOfLading(models.Model):
    _name = 'servoo.shipping.bl'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Bill of lading'
    _order = 'id desc'

    name = fields.Char('Name', required=True, index=True, default=lambda self: _('New'), copy=False)
    date = fields.Date('Date')
    shipper_id = fields.Many2one('res.partner', 'Shipper', required=True, index=True)
    consignee_id = fields.Many2one('res.partner', 'Consignee', index=True)
    notify_id = fields.Many2one('res.partner', 'Notify address', index=True)
    shipping_file_id = fields.Many2one('servoo.shipping.file', 'Shipping file')
    vessel_id = fields.Many2one('res.transport.means', string="Vessel", index=True)
    loading_port = fields.Many2one('res.locode', 'Port of loading', index=True)
    discharge_port = fields.Many2one('res.locode', 'Port of discharge', index=True)
    voyage_number = fields.Char('Voyage Number')
    cargo_description = fields.Char('Cargo Description')
    state = fields.Selection([
        ('saved', 'Saved'),
        ('delivered', 'Delivered')
    ], default='saved', string='State', index=True)
    good_ids = fields.One2many('servoo.shipping.good', 'bl_id', string='Goods',
                               auto_join=True, index=True, copy=True)

    delivery_order_count = fields.Integer(compute="_get_delivery_orders", string='Delivery Orders')
    cargo_weight = fields.Float(string='Cargo weight', compute="_get_cargo_weight")

    def _get_delivery_orders(self):
        orders = self.env['servoo.shipping.delivery.order']
        for record in self:
            record.delivery_order_count = orders.search_count([('bl_id', '=', record.id)])

    def _get_cargo_weight(self):
        for bl in self:
            weight = 0.0
            for good in bl.good_ids:
                weight += good.gross_weight
            bl.cargo_weight = weight

    def name_get(self):
        result = []
        for bl in self:
            name = bl.name + (bl.vessel_id and (' - ' + bl.vessel_id.name) or '')
            result.append((bl.id, name))
        return result

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.shipping.bl') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.shipping.bl') or _('New')
        return super().create(vals)

    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current file """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_bl_id=self.id, group_by=False),
                domain=[('bl_id', '=', self.id)]
            )
            return res
        return False

