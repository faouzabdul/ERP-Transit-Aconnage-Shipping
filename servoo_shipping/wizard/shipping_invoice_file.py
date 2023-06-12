# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, fields, models


class ShippingInvoiceFile(models.Model):
    _name = 'servoo.shipping.invoice.file'
    _description = 'Wizard to invoice shipping file'

    shipping_file_id = fields.Many2one('servoo.shipping.file', 'Shipping File', required=True,
                            default=lambda self: self.env.context.get('active_id', None))
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    invoice_mode = fields.Selection([
        ('bl', 'Bill of lading'),
        ('formalities', 'Formalities')
    ], string='Invoice Mode', required=True)
    import_pad_invoice = fields.Boolean('Import PAD Invoice')
    export_pad_invoice = fields.Boolean('Export PAD Invoice')
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
            'partner_id': self.shipping_file_id.partner_id.id,
            'partner_shipping_id': self.shipping_file_id.partner_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.shipping_file_id.name,
            'invoice_line_ids': [],
            'transport_means_id': self.shipping_file_id.vessel.id,
            'travel_date': self.shipping_file_id.date_arrival_departure,
            'loading_place_id': self.shipping_file_id.port_previous_next.id,
            'unloading_place_id': self.shipping_file_id.port_arrival_departure.id,
            'volume': self.shipping_file_id.vessel_volume,
            'weight': self.shipping_file_id.gross_weight,
            'currency_id': self.currency_id.id
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        for line in self.shipping_file_id.formality_line:
            invoiceable_line_ids.append(line.id)
        return self.env['servoo.shipping.formality'].browse(invoiceable_line_ids)

    def create_invoices(self):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']
        # 1) Create invoices.
        invoice_vals_list = []
        if self.invoice_mode == 'bl':
            for bl in self.shipping_file_id.bl_ids:
                # for client in self.partner_ids:
                invoice_vals = self._prepare_invoice()
                invoice_vals['transport_letter'] = bl.name
                # Calculer le poids des marchandises dans chaque BL
                volume = 0.0
                weight = 0.0
                net_weight = 0.0
                for good in bl.good_ids:
                    volume += good.volume
                    weight += good.gross_weight
                    net_weight += good.net_weight
                invoice_vals['import_pad_invoice'] = self.import_pad_invoice
                invoice_vals['export_pad_invoice'] = self.export_pad_invoice
                invoice_vals['volume'] = volume
                invoice_vals['weight'] = weight or net_weight
                invoice_vals['partner_id'] = bl.notify_id.id if bl.notify_id else bl.shipper_id.id
                invoice_vals['partner_shipping_id'] = bl.notify_id.id if bl.notify_id else bl.shipper_id.id
                # invoiceable_lines = file._get_invoiceable_lines()
                # invoice_line_vals = []
                # for line in invoiceable_lines:
                #     invoice_line_vals.append(
                #         (0, 0, {
                #             'name': line.name,
                #             'product_id': line.service_id.id,
                #             'quantity': 1.0,
                #             'price_unit': line.amount,
                #         }),
                #     )
                # invoice_vals['invoice_line_ids'] += invoice_line_vals
                invoice_vals_list.append(invoice_vals)
        else:
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
                    }),
                )
            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(moves) > 1:
            action['domain'] = [('id', 'in', moves.ids)]
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
                'default_partner_id': self.shipping_file_id.partner_id.id,
                'default_partner_shipping_id': self.shipping_file_id.partner_id.id,
                'default_invoice_origin': self.shipping_file_id.name,
                'default_user_id': self.env.user.id,
            })
        action['context'] = context
        return action

    def action_validate(self):
        return self.create_invoices()

    @api.onchange('import_pad_invoice', 'export_pad_invoice', 'additional_invoice')
    def onchange_invoice_boolean_params(self):
        if self.additional_invoice:
            self.import_pad_invoice = False
            self.export_pad_invoice = False
        if self.export_pad_invoice:
            self.import_pad_invoice = False
            self.additional_invoice = False
        if self.import_pad_invoice:
            self.export_pad_invoice = False
            self.additional_invoice = False