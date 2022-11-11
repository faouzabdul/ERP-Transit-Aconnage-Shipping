# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models, _
from datetime import datetime


class WizardMateReceipt(models.TransientModel):
    _name = 'servoo.stevedoring.mate.receipt.wizard'
    _description = "Mate Receipt"

    customs_declaration_id = fields.Many2one('servoo.customs.declaration', 'Customs Declaration', default=lambda self: self.env.context.get('active_id', None))
    charger_id = fields.Many2one('res.partner', related='customs_declaration_id.charger_id')
    loading_port = fields.Many2one('res.locode', related='customs_declaration_id.loading_port')
    unloading_port = fields.Many2one('res.locode', related='customs_declaration_id.unloading_port')
    vessel_id = fields.Many2one('res.transport.means', related='customs_declaration_id.vessel_id')
    terms_and_conditions = fields.Char('Terms and conditions')
    note = fields.Text('Notes')
    date = fields.Date('Date', default=datetime.now())

    def action_validate(self):
        vals = {
            'name': _('New'),
            'date': self.date,
            'customs_declaration_id': self.customs_declaration_id.id,
            'note': self.note,
            'terms_and_conditions': self.terms_and_conditions,
        }
        return self.env['servoo.stevedoring.mate.receipt'].create(vals)
