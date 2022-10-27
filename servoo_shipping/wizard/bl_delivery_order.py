# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models


class BlDeliveryOrder(models.TransientModel):
    _name = 'servoo.shipping.bl.delivery.order'
    _description = "Delivery Order"

    date = fields.Date('Date')
    validity_date = fields.Date('Validity Date')
    bl_id = fields.Many2one('servoo.shipping.bl', 'Bill of lading', required=True,
                            default=lambda self: self.env.context.get('active_id', None))
    custom_declaration_reference = fields.Char('Custom Declaration', required=True)
    custom_declaration_date = fields.Date('Custom Declaration Date', required=True)
    warehouse = fields.Char('Warehouse')

    def action_validate(self):
        vals = {
            'name': 'New',
            'date': self.date,
            'validity_date': self.validity_date,
            'bl_id': self.bl_id.id,
            'custom_declaration_reference': self.custom_declaration_reference,
            'custom_declaration_date': self.custom_declaration_date,
            'warehouse': self.warehouse
        }
        self.bl_id.state = 'delivered'
        return self.env['servoo.shipping.delivery.order'].create(vals)
