# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _


class ShippingFile(models.Model):
    _inherit = 'servoo.shipping.file'

    stevedoring_file_count = fields.Integer(compute="_get_stevedoring_file", string='Stevedoring Files')
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('stevedoring', 'Stevedoring'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], ondelete={
        'stevedoring': 'cascade',
    })

    date_debut_operation = fields.Datetime('Date of commence operations')
    date_end_operation = fields.Datetime('Date of complete operations')

    manifested_quantity = fields.Float('Manifested quantity', digits=(6, 3))
    unloaded_quantity = fields.Float('Unloaded quantity', digits=(6, 3))
    transported_quantity = fields.Float('Transported quantity', digits=(6, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')

    manifested_tonnage = fields.Float('Manifested Tonnage (kg)', digits=(6, 3))
    unloaded_tonnage = fields.Float('Unloaded Tonnage (kg)', digits=(6, 3))
    transported_tonnage = fields.Float('Transported Tonnage (kg)', digits=(6, 3))

    outturn_count = fields.Integer(compute="_get_outturn", string='Outturns')
    operation_count = fields.Integer(compute="_get_operation", string='Operations count')
    mate_receipt_count = fields.Integer(compute="_get_mate_receipt", string='Mate receipts')

    operation_ids = fields.One2many('servoo.stevedoring.operation', 'shipping_file_id', 'Operations', tracking=1)
    customs_declaration_ids = fields.One2many('servoo.customs.declaration', 'shipping_file_id',
                                              string='Customs Declaration', tracking=1)

    partner_ids = fields.Many2many('res.partner', string='Stevedoring Clients', tracking=1)

    def action_stevedoring(self):
        return self.write({'state': 'stevedoring'})

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

    def _get_outturn(self):
        outturn = self.env['servoo.stevedoring.outturn.report']
        for record in self:
            record.outturn_count = outturn.search_count([('shipping_file_id', '=', record.id)])

    def _get_operation(self):
        for record in self:
            record.operation_count = len(record.operation_ids)

    def _get_mate_receipt(self):
        mate_receipt = self.env['servoo.stevedoring.mate.receipt']
        for record in self:
            record.mate_receipt_count = mate_receipt.search_count([('customs_declaration_id', 'in', [x.id for x in record.customs_declaration_ids])])

    def open_operation_action(self):
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

    def open_mate_receipt(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                domain=[('customs_declaration_id', 'in', [x.id for x in self.customs_declaration_ids])]
            )
            return res
        return False

