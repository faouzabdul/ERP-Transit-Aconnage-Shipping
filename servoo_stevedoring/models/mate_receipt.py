# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class MateReceipt(models.Model):
    _name = 'servoo.stevedoring.mate.receipt'
    _description = 'Mate Receipt'

    name = fields.Char('Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    customs_declaration_id = fields.Many2one('servoo.customs.declaration', 'Customs Declaration', required=True)
    charger_id = fields.Many2one('res.partner', related='customs_declaration_id.charger_id')
    loading_port = fields.Many2one('res.locode', related='customs_declaration_id.loading_port')
    unloading_port = fields.Many2one('res.locode', related='customs_declaration_id.unloading_port')
    vessel_id = fields.Many2one('res.transport.means', related='customs_declaration_id.vessel_id')
    note = fields.Text('Notes')
    date = fields.Date('Date', default=datetime.now())
    create_uid = fields.Many2one('res.users')
    terms_and_conditions = fields.Char('Terms and conditions')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.stevedoring.mate.receipt') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.stevedoring.mate.receipt') or _('New')
        return super().create(vals)
