# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import api, models, fields, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class OperationNature(models.Model):
    _name = 'servoo.logistic.operation.nature'

    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    sequence_code = fields.Char('Sequence Code')


class Operation(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'servoo.logistic.operation'
    _order = 'id desc'

    operation_nature = fields.Many2one('servoo.logistic.operation.nature', 'Operation Nature', tracking=1)
    volume = fields.Float('Volume', digits=(12, 3))
    weight = fields.Float('Weight', digits=(12, 3))
    goods_description = fields.Text('Description of goods')
    bill_of_lading = fields.Char('Bill of lading', tracking=1)
    name = fields.Char(string='Reference', required=True, index=True, default=lambda self: _('New'), copy=False)
    external_reference = fields.Char(string='External Reference')
    date_debut = fields.Datetime('Date Debut')
    date_end = fields.Datetime('Date End')
    partner_id = fields.Many2one('res.partner', 'Client', required=True, tracking=1)
    final_partner_id = fields.Many2one('res.partner', 'Final Client')
    formality_line = fields.One2many('servoo.logistic.formality', 'operation_id', string='Formality Lines',
                                     auto_join=True, tracking=1, copy=True)
    document_ids = fields.One2many('servoo.logistic.document', 'operation_id', string='Documents', auto_join=True,
                                   copy=True)
    operation_vehicle_ids = fields.One2many('servoo.logistic.operation.vehicle', 'operation_id', string='Vehicles',
                                            tracking=1, auto_join=True, copy=True)
    departure_country_id = fields.Many2one('res.country', 'Departure Country')
    destination_country_id = fields.Many2one('res.country', 'Destination Country')
    parent_id = fields.Many2one('servoo.logistic.operation', 'Parent')
    child_ids = fields.One2many('servoo.logistic.operation', 'parent_id', string='Sub-operation', auto_join=True, copy=True)
    loading_place_id = fields.Many2one('res.locode', string='Loading place')
    unloading_place_id = fields.Many2one('res.locode', string='Unloading place')
    transport_mode_id = fields.Many2one('res.transport.mode', string='Transport Mode')
    transport_means_id = fields.Many2one('res.transport.means', string="Mean of transportation")
    delivery_place = fields.Char('Delivery place')
    delivery_date = fields.Date('Delivery Date')
    arrival_date = fields.Date('Arrival Date')
    invoice_count = fields.Integer(compute="_get_invoiced", string='Invoices')
    user_id = fields.Many2one('res.users', 'User id')
    # travel_reference = fields.Char('Travel Number')
    # manifest_number = fields.Char('Manifest Number')
    operation_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('transit', 'Transit')], 'Type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=1)
    agency_name = fields.Selection([
        ('Douala', 'Douala'),
        ('Kribi', 'Kribi'),
        ('Tchad', 'Tchad'),
    ], string='Agency', default='Douala')
    cancel_note = fields.Text('Cancel Motivation', tracking=2)
    invoice_state = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('invoiced', 'Invoiced')
    ], string='Invoice State', default='not_invoiced')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('This reference must be unique!'))
    ]

    def _get_invoiced(self):
        invoice = self.env['account.move']
        for record in self:
            record.invoice_count = invoice.search_count([('invoice_origin', '=', record.name)])
            if record.invoice_count > 0:
                record.invoice_state = 'invoiced'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            # if 'company_id' in vals:
            #     vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
            #         'servoo.logistic.operation') or _('New')
            # else:
            #     vals['name'] = self.env['ir.sequence'].next_by_code('servoo.logistic.operation') or _('New')
            vals['name'] = self.generate_reference(vals)
        return super().create(vals)

    def generate_reference(self, vals):
        reference = str(datetime.now().year)[-2:]
        type = self.env['servoo.logistic.operation.nature'].search([('id', '=', vals['operation_nature'])])
        if type:
            reference += type.sequence_code if type.sequence_code else ''
        transport_mode = self.env['res.transport.mode'].search([('id', '=', vals['transport_mode_id'])])
        if type and type.sequence_code and type.sequence_code != 'DLOG':
            if transport_mode:
                if transport_mode.code == '10':
                    reference += "M"
                elif transport_mode.code == "30":
                    reference += "T"
                elif transport_mode.code == "40":
                    reference += "A"
                elif vals['operation_type']:
                    reference += str(vals['operation_type'][0].upper())
            elif vals['operation_type']:
                reference += str(vals['operation_type'][0].upper())
        query = "SELECT count(*) FROM servoo_logistic_operation WHERE name LIKE '" + reference + "%'"
        self._cr.execute(query)
        res = self._cr.fetchone()
        record_count = int(res[0]) + 1
        if len(str(record_count)) == 1:
            reference += '00'
        elif len(str(record_count)) == 2:
            reference += '0'
        reference += str(record_count)
        return reference


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
                context=dict(self.env.context, default_operation_id=self.id, group_by=False),
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
            'weight': self.weight,
            'custom_declaration_reference': '',
            'custom_declaration_date': '',
            'unit_id': self.env.ref('dyen_base.unit_KG').id,
            'agency_name': self.agency_name
        }
        return invoice_vals

    def _get_invoiceable_lines(self):
        invoiceable_line_ids = []
        for line in self.formality_line:
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
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_id.id,
                'default_invoice_origin': self.name,
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action


class OperationVehicle(models.Model):
    _name = 'servoo.logistic.operation.vehicle'

    operation_id = fields.Many2one('servoo.logistic.operation', 'Operation')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    license_plate = fields.Char(related='vehicle_id.license_plate', store=True, readonly=False)
    vin_sn = fields.Char(related='vehicle_id.vin_sn', store=True, readonly=True)
    driver_id = fields.Many2one('res.partner', 'Driver', copy=False, readonly=True)
    category_id = fields.Many2one('fleet.vehicle.model.category', related='vehicle_id.model_id.category_id', store=True,
                                  readonly=True)


# class AccountMove(models.Model):
#     _inherit = 'account.move'
#
#     operation_id = fields.Many2one('servoo.logistic.operation', 'Logistic Operation')
