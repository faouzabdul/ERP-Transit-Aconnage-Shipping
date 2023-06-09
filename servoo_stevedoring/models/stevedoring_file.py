# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from datetime import datetime


class StevedoringFileType(models.Model):
    _name = 'servoo.stevedoring.file.type'
    _description = 'Stevedoring File Type'

    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    sequence_code = fields.Char('Sequence Code')


class StevedoringFile(models.Model):
    _name = 'servoo.stevedoring.file'
    _description = 'Stevedoring File'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, tracking=1, default=lambda self: _('New'), copy=False)
    file_type_id = fields.Many2one('servoo.stevedoring.file.type', 'File Type', required=True, tracking=1)
    partner_id = fields.Many2one('res.partner', 'Client')
    partner_ids = fields.Many2many('res.partner', string='Clients', tracking=1)
    external_reference = fields.Char('External Reference')
    date = fields.Date('Date', required=True, default=lambda self: fields.datetime.now())
    vessel_id = fields.Many2one('res.transport.means', 'Vessel')
    voyage_number = fields.Char('Voyage number')
    shipowner_id = fields.Many2one('res.partner', 'Shipowner')
    charterer_id = fields.Many2one('res.partner', 'Charterer')
    consignee_agent_id = fields.Many2one('res.partner', 'Consignee Agent')
    formality_line = fields.One2many('servoo.stevedoring.formality', 'file_id', string='Formality Lines',
                                     auto_join=True, tracking=1, copy=True)
    document_ids = fields.One2many('servoo.stevedoring.document', 'file_id', string='Documents', auto_join=True,
                                   copy=True)
    customs_declaration_ids = fields.One2many('servoo.customs.declaration', 'stevedoring_file_id', string='Customs Declaration', tracking=1)
    bl_ids = fields.Many2many(
        'servoo.shipping.bl', 'servoo_stevedoring_bl_rel',
        'bl_id', 'stevedoring_file_id',
        string='Bills of lading')
    operation_ids = fields.One2many('servoo.stevedoring.operation', 'stevedoring_file_id', 'Operations', tracking=1)
    loading_port = fields.Many2one('res.locode', 'Port of loading', tracking=1)
    discharge_port = fields.Many2one('res.locode', 'Port of discharge', tracking=1)
    origin_place = fields.Char('Origin Place')
    destination_place = fields.Char('Destination Place')
    invoice_count = fields.Integer(compute="_get_invoiced", string='Invoices')
    shipping_file_id = fields.Many2one('servoo.shipping.file', 'Shipping File')
    cargo_description = fields.Text('Cargo Description')
    date_debut_operation = fields.Datetime('Date of commence operations')
    date_end_operation = fields.Datetime('Date of complete operations')

    manifested_quantity = fields.Float('Manifested quantity', digits=(6, 3))
    unloaded_quantity = fields.Float('Unloaded quantity', digits=(6, 3))
    transported_quantity = fields.Float('Transported quantity', digits=(6, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')
    # manifested_quantity_unit = fields.Many2one('res.unit', 'Unit manifested quantity')
    # unloaded_quantity_unit = fields.Many2one('res.unit', 'Unit Unloaded quantity')
    # transported_quantity_unit = fields.Many2one('res.unit', 'Unit Transported quantity')

    manifested_tonnage = fields.Float('Manifested Tonnage (kg)', digits=(6, 3))
    unloaded_tonnage = fields.Float('Unloaded Tonnage (kg)', digits=(6, 3))
    transported_tonnage = fields.Float('Transported Tonnage (kg)', digits=(6, 3))

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=1)
    user_id = fields.Many2one('res.users', 'User')
    outturn_count = fields.Integer(compute="_get_outturn", string='Outturns')
    operation_count = fields.Integer(compute="_get_operation", string='Operations')
    mate_receipt_count = fields.Integer(compute="_get_mate_receipt", string='Mate receipts')
    cancel_note = fields.Text('Cancel Motivation', tracking=2)
    invoice_state = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('invoiced', 'Invoiced')
    ], string='Invoice State', default='not_invoiced')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.stevedoring.file') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.stevedoring.file') or _('New')
        return super().create(vals)

    def name_get(self):
        result = []
        for item in self:
            name = item.name + (item.vessel_id and (' - ' + item.vessel_id.name) or '')
            result.append((item.id, name))
        return result

    def _get_invoiced(self):
        invoice = self.env['account.move']
        for record in self:
            record.invoice_count = invoice.search_count([('invoice_origin', '=', record.name)])
            if record.invoice_count > 0:
                record.invoice_state = 'invoiced'

    def _get_outturn(self):
        outturn = self.env['servoo.stevedoring.outturn.report']
        for record in self:
            record.outturn_count = outturn.search_count([('stevedoring_file_id', '=', record.id)])

    def _get_operation(self):
        # operation = self.env['servoo.stevedoring.operation']
        for record in self:
            # record.outturn_count = operation.search_count([('stevedoring_file_id', '=', record.id)])
            record.operation_count = len(record.operation_ids)

    def _get_mate_receipt(self):
        mate_receipt = self.env['servoo.stevedoring.mate.receipt']
        for record in self:
            record.mate_receipt_count = mate_receipt.search_count([('customs_declaration_id', 'in', [x.id for x in record.customs_declaration_ids])])

    def _prepare_invoice(self):
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).', self.company_id.name, self.company_id.id))

        invoice_vals = {
            'move_type': 'out_invoice',
            'user_id': self.user_id.id,
            'invoice_user_id': self.user_id.id,
            # 'partner_id': self.partner_id.id,
            # 'partner_shipping_id': self.partner_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_line_ids': [],
            'transport_means_id': self.vessel_id.id,
            'travel_date': self.date,
            'loading_place_id': self.loading_port.id,
            'unloading_place_id': self.discharge_port.id,
            'weight': self.unloaded_tonnage,
            'transport_letter': '',
            'unit_id': self.env.ref('dyen_base.unit_KG').id
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        for line in self.formality_line:
            invoiceable_line_ids.append(line.id)
        return self.env['servoo.stevedoring.formality'].browse(invoiceable_line_ids)

    def create_invoices(self):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']
        # 1) Create invoices.
        invoice_vals_list = []
        for file in self:
            for bl in file.bl_ids:
            # for client in self.partner_ids:
                invoice_vals = file._prepare_invoice()
                invoice_vals['transport_letter'] = bl.name
                # Calculer le poids des marchandises dans chaque BL
                volume = 0.0
                weight = 0.0
                for good in bl.good_ids:
                    volume += good.volume
                    weight += good.gross_weight
                invoice_vals['volume'] = volume
                invoice_vals['weight'] = weight
                invoice_vals['partner_id'] = bl.notify_id.id if bl.notify_id else bl.shipper_id.id
                invoice_vals['partner_shipping_id'] = bl.notify_id.id if bl.notify_id else bl.shipper_id.id
                invoiceable_lines = file._get_invoiceable_lines()
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
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_id.id,
                'default_invoice_origin': self.name,
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action

    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current file """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_invoice_origin=self.name, group_by=False),
                domain=[('invoice_origin', '=', self.name)]
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

    def open_operation_action(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_stevedoring_file_id=self.id, group_by=False),
                domain=[('stevedoring_file_id', '=', self.id)]
            )
            return res
        return False

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_done(self):
        datas = {'state': 'done'}
        # for item in self:
        #     if not item.date_end:
        #         datas['date_end'] = datetime.now()
        return self.write(datas)

    def action_open(self):
        return self.write({'state': 'open'})

    @api.onchange('shipping_file_id')
    def onchange_shipping_file(self):
        self.vessel_id = self.shipping_file_id.vessel.id
        self.shipowner_id = self.shipping_file_id.shipowner_id.id
        self.charterer_id = self.shipping_file_id.charterer_id.id
        self.bl_ids = [(6, 0, [bl.id for bl in self.shipping_file_id.bl_ids])]
        self.loading_port = self.shipping_file_id.port_previous_next.id
        self.discharge_port = self.shipping_file_id.port_arrival_departure.id
        self.voyage_number = self.shipping_file_id.voyage_number

