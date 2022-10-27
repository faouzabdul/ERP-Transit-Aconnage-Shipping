# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, models, fields, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class ShippingFileType(models.Model):
    _name = 'servoo.shipping.file.type'

    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    sequence_code = fields.Char('Sequence Code')


class ShippingFile(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.shipping.file'
    _order = 'id desc'

    file_type_id = fields.Many2one('servoo.shipping.file.type', 'File Type', required=True)
    name = fields.Char(string='Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    shipping_pda_id = fields.Many2one('servoo.shipping.pda', 'PDA')
    partner_id = fields.Many2one('res.partner', 'Client', required=True)
    shipowner_id = fields.Many2one('res.partner', 'Shipowner')
    charterer_id = fields.Many2one('res.partner', 'Charterer')
    formality_line = fields.One2many('servoo.shipping.formality', 'file_id', string='Formality Lines',
                                     auto_join=True, tracking=True, copy=True)
    document_ids = fields.One2many('servoo.shipping.document', 'file_id', string='Documents', auto_join=True,
                                   copy=True)

    parent_id = fields.Many2one('servoo.shipping.file', 'Parent')
    child_ids = fields.One2many('servoo.shipping.file', 'parent_id', string='Sub-file', auto_join=True, copy=True)
    invoice_count = fields.Integer(compute="_get_invoiced", string='Invoices')
    user_id = fields.Many2one('res.users', 'User id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', default='draft')
    # FAL 1: General Information
    vessel = fields.Many2one('res.transport.means', string="Vessel")
    loa = fields.Float('LOA', digits=(6, 3))
    beam = fields.Float('Beam', digits=(6, 3), help='Largeur')
    summer_draft = fields.Float('Summer draft', digits=(6, 3))
    vessel_volume = fields.Float('Vessel Volume', digits=(6, 3))
    nrt = fields.Float('NRT', digits=(6, 3), help='NRT')
    grt = fields.Float('GRT', digits=(12, 4), required=False, tracking=6)
    cbm_vessel = fields.Float('CBM Vessel', digits=(12, 4), required=False, tracking=6)
    operation_type = fields.Selection([('arrival', 'Arrival'), ('departure', 'Departure')])
    imo_number = fields.Char('IMO Number')
    call_sign = fields.Char('Call Sign')
    name_of_master = fields.Char('Name of master')
    voyage_number = fields.Char('Travel Number')
    port_arrival_departure = fields.Many2one('res.locode', 'Port of loading/discharge')
    port_previous_next = fields.Many2one('res.locode', 'Last Port/Next Port')
    date_arrival_departure = fields.Datetime('Date and time of arrival/departure')
    flag_vessel = fields.Many2one('res.country', 'Flag')
    gross_weight = fields.Float('Cargo gross tonnage (kg)', digits=(12, 3))
    net_weight = fields.Float('Cargo net tonnage (kg)', digits=(12, 3))
    travel_description = fields.Text('Particulars of voyage')
    goods_description = fields.Text('Description of goods')

    bl_ids = fields.One2many('servoo.shipping.bl', 'shipping_file_id', string='Bill of loading', tracking=True)
    # crew_count = fields.Integer('Crew Count', compute="_get_crew_count")
    # passenger_count = fields.Integer('Passenger Count', compute="_get_passenger_count")
    # FAL 2: Cargo Declaration
    good_ids = fields.One2many('servoo.shipping.good', 'file_id', string='Goods',
                               auto_join=True, tracking=True, copy=True)
    container_ids = fields.One2many('servoo.shipping.container', 'file_id', string='Containers',
                                    auto_join=True, tracking=True, copy=True)
    # FAL 3: Ship's stores Declaration
    store_ids = fields.One2many('servoo.shipping.ship.store', 'file_id', "Ship's stores")
    # FAL 4: Crew's effects Declaration
    crew_effect_ids = fields.One2many('servoo.shipping.crew.effect', 'file_id', "Crew's effects")
    # FAL 5: Crew List
    crew_ids = fields.One2many('servoo.shipping.crew', 'file_id', 'Crew List')
    # FAL 6: Passenger List
    passenger_ids = fields.One2many('servoo.shipping.passenger', 'file_id', 'Passengers List')
    # FAL 7: Dangerous Goods Manifest
    dangerous_good_ids = fields.One2many('servoo.shipping.dangerous.good', 'file_id', 'Dangerous Goods')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('This reference must be unique!'))
    ]

    def name_get(self):
        result = []
        for pda in self:
            name = pda.name + (pda.vessel and (' - ' + pda.vessel.name) or '')
            result.append((pda.id, name))
        return result

    def _get_invoiced(self):
        invoice = self.env['account.move']
        for record in self:
            record.invoice_count = invoice.search_count([('invoice_origin', '=', record.name)])

    # def _get_crew_count(self):
    #     for record in self:
    #         record.crew_count = len(record.crew_ids)
    #
    # def _get_passenger_count(self):
    #     for record in self:
    #         record.passenger_count = len(record.passenger_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'servoo.shipping.file') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('servoo.shipping.file') or _('New')
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
        """ This opens the xml view specified in xml_id for the current file """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window']._for_xml_id('%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_file_id=self.id, group_by=False),
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
            'invoice_line_ids': []
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        for line in self.formality_line:
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
        for file in self:
            invoice_vals = file._prepare_invoice()
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

    @api.onchange('shipping_pda_id')
    def onchange_shipping_pda(self):
        if self.shipping_pda_id:
            self.vessel = self.shipping_pda_id.vessel_id.id
            if not self.partner_id:
                self.partner_id = self.shipping_pda_id.partner_id.id
            self.voyage_number = self.shipping_pda_id.voyage_number
            self.beam = self.shipping_pda_id.beam
            self.loa = self.shipping_pda_id.loa
            self.summer_draft = self.shipping_pda_id.summer_draft
            self.vessel_volume = self.shipping_pda_id.vessel_volume
            self.nrt = self.shipping_pda_id.nrt
            self.grt = self.shipping_pda_id.grt
            self.cbm_vessel = self.shipping_pda_id.cbm_vessel
            self.gross_weight = self.shipping_pda_id.tonnage_of_goods


