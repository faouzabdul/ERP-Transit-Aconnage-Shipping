# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from . import utils
from odoo.tools import is_html_empty
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    transport_means_id = fields.Many2one('res.transport.means', string="Means of transportation", tracking=3)
    travel_date = fields.Date('Travel Date')
    loading_place_id = fields.Many2one('res.locode', string='Loading place', tracking=3)
    unloading_place_id = fields.Many2one('res.locode', string='Unloading place', tracking=3)
    transport_letter = fields.Char('N° BL / N° LTA', index=True, tracking=3)
    volume = fields.Float('Volume (m3)', digits=(12, 3))
    weight = fields.Float('Weight', digits=(12, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')
    custom_declaration_reference = fields.Char('Custom Declaration Reference', tracking=3)
    custom_declaration_date = fields.Date('Custom Declaration Date')
    assessed_value = fields.Float('Assessed Value', digits=(12, 3), help='Valeur imposable', tracking=3)
    object = fields.Text('Object', tracking=3)
    number_of_packages = fields.Char('Number of packages/TC', tracking=3)
    amount_total_signed_letter = fields.Char('Total Signed letter', compute='_compute_display_amount_letter',
                                               store=True)
    amount_total_in_currency_signed_letter = fields.Char('Total in Currency Signed letter', compute='_compute_display_amount_letter',
                                               store=True)

    other_currency_id = fields.Many2one('res.currency', 'Other Currency')
    amount_other_currency = fields.Float(string='Total Currency', store=True, digits=(6, 3),
                                         compute='_compute_display_amount_letter')
    agency_name = fields.Selection([
        ('Douala', 'Douala'),
        ('Kribi', 'Kribi'),
        ('Tchad', 'Tchad'),
    ], string='Agency', default='Douala')
    # sale_order_template_id = fields.Many2one(
    #     'sale.order.template', 'Invoice Template',
    #     readonly=True, check_company=True,
    #     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    department_id = fields.Many2one('hr.department', 'Department')
    observation = fields.Text('Observation', tracking=2)
    import_pad_invoice = fields.Boolean('Import PAD Invoice', tracking=3)
    export_pad_invoice = fields.Boolean('Export PAD Invoice', tracking=3)
    additional_invoice = fields.Boolean('Additional Invoice', tracking=3)
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('direction_routing', 'Submitted'),
        ('department_approval', 'Department Approval'),
        ('direction_approval', 'Direction Approval'),
        ('accounting_approval', 'Accounting Approval'),
        ('management_control_approval', 'Management Control Approval'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], ondelete={
        'direction_routing': 'cascade',
        'department_approval': 'cascade',
        'direction_approval': 'cascade',
        'accounting_approval': 'cascade',
        'management_control_approval': 'cascade'
    })
    invoice_line_ids = fields.One2many(states={'draft': [('readonly', False)],
                                               'direction_routing': [('readonly', False)],
                                               'department_approval': [('readonly', False)],
                                               'direction_approval': [('readonly', False)],
                                               'accounting_approval': [('readonly', False)],
                                               'management_control_approval': [('readonly', False)],
                                               })
    apm_reference = fields.Char('APM Reference', tracking=3)

    @api.depends('amount_total', 'currency_id')
    def _compute_display_amount_letter(self):
        for move in self:
            move.amount_total_signed_letter = utils.translate(move.amount_total_signed if move.amount_total_signed > -1 else (-1*move.amount_total_signed)).upper()
            move.amount_total_in_currency_signed_letter = utils.translate(move.amount_total_in_currency_signed if move.amount_total_in_currency_signed > -1 else (-1 * move.amount_total_in_currency_signed)).upper()
            currency_code = 'XAF'
            if move.currency_id.name == 'XAF':
                currency_code = 'EUR'
            other_currency = self.env['res.currency'].search([('name', '=', currency_code)])
            rate = other_currency.rate if currency_code == 'EUR' else other_currency.inverse_rate
            move.other_currency_id = other_currency and other_currency.id
            move.amount_other_currency = (move.amount_total_signed if move.amount_total_signed > -1 else -1*move.amount_total_signed) * rate

    def action_submit(self):
        return self.write({'state': 'direction_routing'})

    def _generate_APM_reference(self, source, import_pad_invoice=None, export_pad_invoice=None, additional_invoice=None):
        if import_pad_invoice:
            return self.env['ir.sequence'].next_by_code('servoo.import.invoice.pad.apm.number')
        elif export_pad_invoice:
            return self.env['ir.sequence'].next_by_code('servoo.import.invoice.pad.apm.number')
        ref=''
        if source and additional_invoice:
            q = "SELECT apm_reference FROM account_move where invoice_origin = '%s' and apm_reference is not null" % source
            self._cr.execute(q)
            res = self._cr.fetchall()
            if res and res[0][0]:
                _logger.info('res : %s' % res)
                ref = res[0][0] + "-" + str(len(res))
                return ref
        if source and source[:2].isnumeric():
            ref = str(datetime.now().year)[-2:] + 'F' + source[2:-3]
        if ref:
            query = "SELECT apm_reference FROM account_move WHERE apm_reference LIKE '" + ref + "%' order by id desc limit 1"
            # query = "SELECT count(*) FROM account_move WHERE apm_reference LIKE '" + ref + "%'"
            self._cr.execute(query)
            # res = self._cr.fetchone()
            # record_count = int(res[0]) + 1
            # if len(str(record_count)) == 1:
            #     ref += '00'
            # elif len(str(record_count)) == 2:
            #     ref += '0'
            # ref += str(record_count)
            res = self._cr.fetchall()
            record_count = len(res) + 1
            if res and res[0][0][-5:].isnumeric():
                record_count = int(res[-1][0][-5:]) + 1
            elif res and res[0][0][-4:].isnumeric():
                record_count = int(res[-1][0][-4:]) + 1
            elif res and res[0][0][-3:].isnumeric():
                record_count = int(res[-1][0][-3:]) + 1
            if len(str(record_count)) == 1:
                ref += '00'
            elif len(str(record_count)) == 2:
                ref += '0'
            ref += str(record_count)
        return ref

    @api.model
    def create(self, vals):
        if vals.get('move_type') == 'out_invoice':
            vals['apm_reference'] = self._generate_APM_reference(vals.get('invoice_origin'), vals.get('import_pad_invoice'), vals.get('export_pad_invoice'), vals.get('additional_invoice'))
        return super(AccountMove, self).create(vals)

    api.model
    def write(self, vals):
        # _logger.info('apm_reference : %s - invoice_origin: %s' % (self.apm_reference, self.invoice_origin))
        if not self.apm_reference:
            origin = vals['invoice_origin'] if vals.get('invoice_origin') else self.invoice_origin
            additional_invoice = vals['additional_invoice'] if vals.get('additional_invoice') else self.additional_invoice
            import_pad_invoice = vals['import_pad_invoice'] if vals.get('import_pad_invoice') else self.import_pad_invoice
            export_pad_invoice = vals['export_pad_invoice'] if vals.get('export_pad_invoice') else self.export_pad_invoice
            vals['apm_reference'] = self._generate_APM_reference(origin, import_pad_invoice, export_pad_invoice, additional_invoice)
        return super(AccountMove, self).write(vals)

    def _get_total_disbursement(self):
        amount = 0.0
        for move in self:
            for line in move.invoice_line_ids:
                if line.product_id.detailed_type == 'disbursement':
                    amount += line.price_subtotal
        return amount

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




    # def _compute_line_data_for_template_change(self, line):
    #     return {
    #         'sequence': line.sequence,
    #         'display_type': line.display_type,
    #         'name': line.name,
    #     }
    #
    # def _sum_rule_amount(self, localdict, line, amount):
    #     localdict['rules'].dict[line.code] = line.code in localdict['rules'].dict and localdict['rules'].dict[line.code] + amount or amount
    #     return localdict
    #
    # def init_dicts(self):
    #     class BrowsableObject(object):
    #         def __init__(self, dict, env):
    #             self.dict = dict
    #             self.env = env
    #
    #         def __getattr__(self, attr):
    #             return attr in self.dict and self.dict.__getitem__(attr) or 0.0
    #
    #     rules_dict = {}
    #     rules = BrowsableObject(rules_dict, self.env)
    #     var_dict = {
    #         'VOLUME': self.volume,
    #         'TONNAGE': self.weight,
    #         'rules': rules
    #     }
    #     return dict(var_dict)
    #
    # def _get_template_lines(self, template_id, localdict):
    #     invoice_lines = [(5, 0, 0)]
    #     template = self.env['sale.order.template'].browse(template_id)
    #     for line in template.sale_order_template_line_ids:
    #         data = self._compute_line_data_for_template_change(line)
    #         localdict['result'] = None
    #         localdict['result_qty'] = 1.0
    #         if line.product_id:
    #             amount, qty = line._compute_rule(localdict)
    #             if line.code:
    #                 total_rule = amount * qty
    #                 localdict[line.code] = total_rule
    #                 localdict = self._sum_rule_amount(localdict, line, total_rule)
    #             price = amount
    #             discount = 0
    #             data.update({
    #                 'price_unit': price,
    #                 'discount': discount,
    #                 'quantity': qty,
    #                 'product_id': line.product_id.id,
    #                 'product_uom_id': line.product_uom_id.id,
    #             })
    #         invoice_lines.append((0, 0, data))
    #     self.invoice_line_ids = invoice_lines
    #
    # @api.onchange('sale_order_template_id')
    # def onchange_sale_order_template_id(self):
    #     template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
    #     localdict = self.init_dicts()
    #     self._get_template_lines(self.sale_order_template_id.id, localdict)
    #     if not is_html_empty(template.note):
    #         self.note = template.note
    #
    # @api.onchange('weight', 'volume')
    # def onchange_variables(self):
    #     localdict = self.init_dicts()
    #     self._get_template_lines(self.sale_order_template_id.id, localdict)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            line.name = line._get_computed_name()
            line.account_id = line._get_computed_account()
            taxes = line._get_computed_taxes()
            if taxes and line.move_id.fiscal_position_id:
                taxes = line.move_id.fiscal_position_id.map_tax(taxes)
            line.tax_ids = taxes
            line.product_uom_id = line._get_computed_uom()
            line.price_unit = line._get_computed_price_unit()
            if self.product_id.default_code in ('COM', 'COD'):
                line.quantity = line.move_id._get_total_disbursement()
