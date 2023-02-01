# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO


from odoo import models, fields, api, _
from datetime import datetime


class PackagingType(models.Model):
    _name = 'servoo.transit.packaging.type'

    name = fields.Char('Name', required=True)


class OperationSubType(models.Model):
    _name = 'servoo.transit.operation.sub.type'

    name = fields.Char('Name', required=True)
    operation_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('transit', 'Transit')], 'Parent Type', required=True)


class TransitOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.transit.order'
    _order = 'id desc'
    _sql_constraints = [
        ('bill_of_lading_uniq', 'unique (bill_of_lading)', 'The bill of lading must be unique !')
    ]

    volume = fields.Float('Volume (m3)', digits=(12, 3))
    gross_weight = fields.Float('Gross Weight (kg)', digits=(12, 3))
    net_weight = fields.Float('Net Weight (kg)', digits=(12, 3))
    goods_description = fields.Char('Description of goods')
    bill_of_lading = fields.Char('Bill of lading')
    name = fields.Char(string='Reference', required=True, tracking=1, default=lambda self: _('New'), copy=False)
    external_reference = fields.Char(string='External Reference')
    date_debut = fields.Datetime('Date Debut')
    date_end = fields.Datetime('Date End')
    partner_id = fields.Many2one('res.partner', 'Client', required=True)
    final_partner_id = fields.Many2one('res.partner', 'Final Client')
    container_ids = fields.One2many('servoo.transit.container', 'order_id', string='Containers',
                                     auto_join=True, tracking=1, copy=True)
    good_ids = fields.One2many('servoo.transit.good', 'order_id', string='Goods',
                                     auto_join=True, tracking=1, copy=True)

    formality_line = fields.One2many('servoo.transit.formality', 'order_id', string='Formality Lines',
                                     auto_join=True, tracking=1, copy=True)
    document_ids = fields.One2many('servoo.transit.document', 'order_id', string='Documents', auto_join=True,
                                   copy=True)
    departure_country_id = fields.Many2one('res.country', 'Departure Country')
    destination_country_id = fields.Many2one('res.country', 'Destination Country')
    transit_country_id = fields.Many2one('res.country', 'Transit Country')
    loading_place_id = fields.Many2one('res.locode', string='Loading place')
    unloading_place_id = fields.Many2one('res.locode', string='Unloading place')
    transit_place_id = fields.Many2one('res.locode', string='Transit place')
    customs_office = fields.Many2one('res.locode', string='Customs Office')
    transport_mode_id = fields.Many2one('res.transport.mode', string='Transport Mode')
    transport_means_id = fields.Many2one('res.transport.means', string="Mean of transportation")
    delivery_country_id = fields.Many2one('res.country', 'Delivery Country')
    delivery_place = fields.Char('Delivery place')
    delivery_date = fields.Date('Delivery Date')
    arrival_date = fields.Date('Arrival Date')
    invoice_count = fields.Integer(compute="_get_invoiced", string='Invoices')
    user_id = fields.Many2one('res.users', 'User id')
    travel_reference = fields.Char('Travel Number')
    manifest_number = fields.Char('Manifest Number')
    currency_id = fields.Many2one('res.currency', 'Currency')
    exchange_rate = fields.Float('Exchange rate', digits=(12, 4))
    custom_regime_id = fields.Many2one('res.customs.regime', 'Customs regime')
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm')
    fob_value_currency = fields.Float('FOB Value in currency', digits=(12, 3))
    fob_value_xaf = fields.Float('FOB Value in XAF', digits=(12, 3))
    fob_charges = fields.Float('FOB Charges', digits=(12, 3))
    freight_amount = fields.Float('Freight Amount', digits=(12, 3))
    insurance_amount = fields.Float('Insurance Amount', digits=(12, 6))
    invoice_number = fields.Char('Proforma/Invoice number')
    invoice_date = fields.Char('Proforma/Invoice Date')
    total_amount_currency = fields.Float('Total amount in currency')
    operation_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('transit', 'Transit')], 'Type')
    sub_operation_type = fields.Many2one('servoo.transit.operation.sub.type', 'Sub Type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', default='draft')
    note = fields.Text('Notes')
    packaging_type_id = fields.Many2one('servoo.transit.packaging.type', 'Packaging type')

    def generate_reference(self, vals):
        reference = str(datetime.now().year)[-2:] + 'D'
        type = vals['operation_type']
        transport_mode = self.env['res.transport.mode'].search([('id', '=', vals['transport_mode_id'])])
        if type == 'import' and transport_mode and transport_mode.code == '10':
            reference += 'DMI'
        elif type == 'export' and transport_mode and transport_mode.code == '10':
            reference += 'DME'
        elif type == 'import' and transport_mode and transport_mode.code == '40':
            reference += 'DAI'
        elif type == 'export' and transport_mode and transport_mode.code == '40':
            reference += 'DAE'
        elif type == 'transit' and transport_mode and transport_mode.code == '40':
            reference += 'TAI'
        elif type == 'transit':
            reference += 'TRI'
        if transport_mode and transport_mode.code in ('10', '40'):
            query = "SELECT count(*) FROM servoo_transit_order WHERE name LIKE '" + reference + "%'"
            self._cr.execute(query)
            res = self._cr.fetchone()
            record_count = int(res[0]) + 1
            if len(str(record_count)) == 1:
                reference += '00'
            elif len(str(record_count)) == 2:
                reference += '0'
            reference += str(record_count)
        else:
            reference = self.env['ir.sequence'].next_by_code('servoo.transit.order') or _('New')
        return reference

    def _get_invoiced(self):
        invoice = self.env['account.move']
        for record in self:
            record.invoice_count = invoice.search_count([('invoice_origin', '=', record.name)])

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        self.exchange_rate = self.currency_id.rate

    @api.onchange('exchange_rate', 'fob_value_currency')
    def onchange_exchange_rate(self):
        self.fob_value_xaf = self.fob_value_currency * self.exchange_rate

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            # if 'company_id' in vals:
            #     vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
            #         'servoo.transit.operation') or _('New')
            # else:
            #     vals['name'] = self.env['ir.sequence'].next_by_code('servoo.transit.order') or _('New')
            vals['name'] = self.generate_reference(vals)
        return super().create(vals)

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_done(self):
        datas = {'state': 'done'}
        for item in self:
            if not item.date_end:
                datas['date_end'] = datetime.now()
        return self.write(datas)

    def action_open(self):
        return self.write({'state': 'open'})

    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current operation """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_order_id=self.id, group_by=False),
                domain=[('invoice_origin', '=', self.name)]
            )
            return res
        return False

    def _prepare_invoice(self):
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).', self.company_id.name, self.company_id.id))

        invoice_vals = {
            'move_type': 'out_invoice',
            'user_id': self.user_id.id,
            'invoice_user_id': self.user_id.id,
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_line_ids': [],
            'transport_means_id': self.transport_means_id.id,
            'travel_date': self.arrival_date,
            'loading_place_id': self.loading_place_id.id,
            'unloading_place_id': self.unloading_place_id.id,
            'transport_letter': self.bill_of_lading,
            'volume': self.volume,
            'weight': self.gross_weight,
            'custom_declaration_reference': '',
            'custom_declaration_date': ''
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        for line in self.formality_line:
            invoiceable_line_ids.append(line.id)
        return self.env['servoo.transit.formality'].browse(invoiceable_line_ids)

    def create_invoices(self):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']
        # 1) Create invoices.
        invoice_vals_list = []
        for operation in self:
            invoice_vals = operation._prepare_invoice()
            invoiceable_lines = operation._get_invoiceable_lines()
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
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_id.id,
                'default_invoice_origin': self.name,
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action