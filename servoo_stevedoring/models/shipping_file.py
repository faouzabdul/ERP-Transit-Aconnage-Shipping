# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _


class ShippingFile(models.Model):
    _inherit = 'servoo.shipping.file'

    stevedoring_file_count = fields.Integer(compute="_get_stevedoring_file", string='Stevedoring Files')

    def _get_stevedoring_file(self):
        obj = self.env['servoo.stevedoring.file']
        for record in self:
            record.stevedoring_file_count = obj.search_count([('shipping_file_id', '=', record.id)])

    def return_open_stevedoring_action(self):
        """ This opens the xml view specified in xml_id for the current file """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_shipping_file_id=self.id, group_by=False),
                domain=[('shipping_file_id', '=', self.id)]
            )
            return res
        return False