# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models


class ShippingPdaCancel(models.TransientModel):
    _name = 'servoo.shipping.pda.cancel'
    _description = "PDA Cancel"

    pda_id = fields.Many2one('servoo.shipping.pda', string='PDA', required=True, ondelete='cascade')
    display_invoice_alert = fields.Boolean('Invoice Alert', compute='_compute_display_invoice_alert')

    @api.depends('pda_id')
    def _compute_display_invoice_alert(self):
        for wizard in self:
            wizard.display_invoice_alert = bool(wizard.pda_id.invoice_ids.filtered(lambda inv: inv.state == 'draft'))

    def action_cancel(self):
        return self.pda_id.with_context({'disable_cancel_warning': True}).action_cancel()
