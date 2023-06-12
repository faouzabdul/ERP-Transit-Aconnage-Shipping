# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models

class ShippingInvoiceFile(models.Model):
    _name = 'servoo.logistic.invoice.file'
    _description = 'Wizard to invoice logistic file'

    logistic_file_id = fields.Many2one('servoo.logistic.operation', 'logistic File', required=True,
                            default=lambda self: self.env.context.get('active_id', None))
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    additional_invoice = fields.Boolean('Additional Invoice')

    def _prepare_invoice(self):
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting sales journal for the company %s (%s).', self.company_id.name,
                  self.company_id.id))

        invoice_vals = {
            'move_type': 'out_invoice',
            'user_id': self.env.user.id,
            'invoice_user_id': self.env.user.id,
            'partner_id': self.logistic_file_id.partner_id.id,
            'partner_shipping_id': self.logistic_file_id.partner_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.logistic_file_id.name,
            'invoice_line_ids': [],
            'transport_means_id': self.logistic_file_id.transport_means_id.id,
            'travel_date': self.logistic_file_id.arrival_date,
            'loading_place_id': self.logistic_file_id.loading_place_id.id,
            'unloading_place_id': self.logistic_file_id.unloading_place_id.id,
            'transport_letter': self.logistic_file_id.bill_of_lading,
            'volume': self.logistic_file_id.volume,
            'weight': self.logistic_file_id.weight,
            'custom_declaration_reference': '',
            'custom_declaration_date': '',
            'unit_id': self.env.ref('dyen_base.unit_KG').id,
            'agency_name': self.logistic_file_id.agency_name,
            'currency_id': self.currency_id.id
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        for line in self.logistic_file_id.formality_line:
            invoiceable_line_ids.append(line.id)
        return self.env['servoo.logistic.formality'].browse(invoiceable_line_ids)

    def create_invoices(self):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']
        # 1) Create invoices.
        invoice_vals_list = []
        invoice_vals = self._prepare_invoice()
        invoice_vals['additional_invoice'] = self.additional_invoice
        invoiceable_lines = self._get_invoiceable_lines()
        invoice_line_vals = []
        for line in invoiceable_lines:
            invoice_line_vals.append(
                (0, 0, {
                    'name': line.name,
                    'product_id': line.service_id.id,
                    'quantity': 1.0,
                    'price_unit': line.amount,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                }),
            )
        invoice_vals['invoice_line_ids'] += invoice_line_vals
        invoice_vals_list.append(invoice_vals)
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(moves) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(moves) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = moves.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.logistic_file_id.partner_id.id,
                'default_partner_shipping_id': self.logistic_file_id.partner_id.id,
                'default_invoice_origin': self.logistic_file_id.name,
                 'default_user_id': self.env.user.id,
            })
        action['context'] = context
        return action

    def action_validate(self):
        return self.create_invoices()