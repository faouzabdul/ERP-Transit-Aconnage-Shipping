# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _


class LogisticOperation(models.Model):
    _inherit = 'servoo.logistic.operation'

    def return_action_finance_document_to_open(self):
        """ This opens the xml view specified in xml_id for the current operation """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_file_reference=self.name, group_by=False),
                domain=[('file_reference', '=', self.name)]
            )
            return res
        return False


class ShippingFile(models.Model):
    _inherit = 'servoo.shipping.file'

    def return_action_finance_document_to_open(self):
        """ This opens the xml view specified in xml_id for the current operation """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_file_reference=self.name, group_by=False),
                domain=[('file_reference', '=', self.name)]
            )
            return res
        return False


class StevedoringFile(models.Model):
    _inherit = 'servoo.stevedoring.file'

    def return_action_finance_document_to_open(self):
        """ This opens the xml view specified in xml_id for the current operation """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_file_reference=self.name, group_by=False),
                domain=[('file_reference', '=', self.name)]
            )
            return res
        return False

class TransitOrder(models.Model):
    _inherit = 'servoo.transit.order'

    def return_action_finance_document_to_open(self):
        """ This opens the xml view specified in xml_id for the current operation """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_file_reference=self.name, group_by=False),
                domain=[('file_reference', '=', self.name)]
            )
            return res
        return False