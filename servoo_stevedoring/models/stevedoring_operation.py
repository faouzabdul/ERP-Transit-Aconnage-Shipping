# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class StevedoringOperation(models.Model):
    _name = 'servoo.stevedoring.operation'
    _description = 'Stevedoring Operation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    user_id = fields.Many2one('res.users', 'User')
    name = fields.Char(string='Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    date_debut = fields.Datetime('Date debut', default=datetime.now())
    date_end = fields.Datetime('Date end')
    stevedoring_file_id = fields.Many2one('servoo.stevedoring.file', 'Stevedoring File', required=True)
    operation_nature = fields.Selection([
        ('loading', 'Loading'),
        ('unloading', 'Unloading'),
        ('transportation', 'Transportation')
    ], string='Operation nature', index=True, required=True)
    name_of_responsible = fields.Char('Name of responsible')
    operation_line_ids = fields.One2many('servoo.stevedoring.operation.line', 'operation_id', string='Operation lines')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.stevedoring.operation') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.stevedoring.operation') or _('New')
        return super().create(vals)


class StevedringOperationLine(models.Model):
    _name = 'servoo.stevedoring.operation.line'
    _description = 'Stevedoring Operation Line'

    product_id = fields.Many2one('product.product', 'Product', help='Fill in this field if it is a storable item')
    cargo_description = fields.Char('Cargo Description', required=True)
    quantity = fields.Float('Quantity', digits=(6, 3))
    weight = fields.Float('Weight', digits=(6, 3))
    volume = fields.Float('Volume', digits=(6, 3))
    note = fields.Text('Notes')
    location = fields.Char('Location')
    operation_id = fields.Many2one('servoo.stevedoring.operation', 'Operation')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.cargo_description = self.product_id.name

