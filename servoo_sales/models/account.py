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
    travel_date = fields.Date('Travel Date', tracking=3)
    loading_place_id = fields.Many2one('res.locode', string='Loading place', tracking=3)
    unloading_place_id = fields.Many2one('res.locode', string='Unloading place', tracking=3)
    transport_letter = fields.Char('N° BL / N° LTA', index=True, tracking=3)
    volume = fields.Float('Volume (m3)', digits=(12, 3), tracking=3)
    weight = fields.Float('Weight', digits=(12, 3), tracking=3)
    unit_id = fields.Many2one('res.unit', 'Unit', tracking=3)
    custom_declaration_reference = fields.Char('Custom Declaration Reference', tracking=3)
    custom_declaration_date = fields.Date('Custom Declaration Date', tracking=3)
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
    ], string='Agency', default='Douala', tracking=3)
    sale_order_template_id = fields.Many2one(
        'sale.order.template', 'Invoice Template',
        readonly=True, check_company=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=3)
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
    handling = fields.Float('Rate')
    include_tax_for_handling = fields.Boolean('Include Taxes')
    quantity = fields.Float('Quantity')
    handling_rate_id = fields.Many2one('servoo.handling.rate', 'Good Type')
    rate_type = fields.Selection(related='handling_rate_id.rate_type', string='Rate Type')

    handling2 = fields.Float('Rate 2')
    include_tax_for_handling2 = fields.Boolean('Include Taxes 2')
    quantity2 = fields.Float('Quantity 2')
    handling_rate_2_id = fields.Many2one('servoo.handling.rate', 'Good Type 2')
    rate_type_2 = fields.Selection(related='handling_rate_2_id.rate_type', string='Rate Type 2')

    handling3 = fields.Float('Rate 3')
    include_tax_for_handling3 = fields.Boolean('Include Taxes 3')
    quantity3 = fields.Float('Quantity 3')
    handling_rate_3_id = fields.Many2one('servoo.handling.rate', 'Good Type 3')
    rate_type_3 = fields.Selection(related='handling_rate_3_id.rate_type', string='Rate Type 3')

    distribute_ht_amount = fields.Boolean('Distribute HT Amount')
    pc_partner_id = fields.Many2one('res.partner', 'P/C', tracking=3)

    @api.onchange('distribute_ht_amount', 'amount_untaxed')
    def onchange_distribute_ht_amount(self):
        narration = ''
        if self.distribute_ht_amount:
            part = self.amount_untaxed / 2
            narration = """50%% APM SA: %s %s<br />
            50%% PAK: %s %s
            """ % (part, self.currency_id.symbol, part, self.currency_id.symbol)
        self.narration = narration

    @api.depends('amount_total', 'currency_id')
    def _compute_display_amount_letter(self):
        for move in self:
            move.amount_total_signed_letter = utils.translate(move.amount_total_signed if move.amount_total_signed > -1 else (-1*move.amount_total_signed), currency=move.currency_id.name).upper()
            move.amount_total_in_currency_signed_letter = utils.translate(move.amount_total_in_currency_signed if move.amount_total_in_currency_signed > -1 else (-1 * move.amount_total_in_currency_signed), currency=move.currency_id.name).upper()
            currency_code = 'XAF'
            if move.currency_id.name == 'XAF':
                currency_code = 'EUR'
            other_currency = self.env['res.currency'].search([('name', '=', currency_code)])
            rate = other_currency.rate if currency_code == 'EUR' else other_currency.inverse_rate
            move.other_currency_id = other_currency and other_currency.id
            move.amount_other_currency = (move.amount_total_signed if move.amount_total_signed > -1 else -1*move.amount_total_signed) * rate

    def action_submit(self):
        return self.write({'state': 'direction_routing'})

    def _get_sequence_name(self, code):
        return self.env['ir.sequence'].next_by_code(code)

    def _get_root(self, source, move_type=None):
        res = ''
        if source and source[:2].isnumeric():
            if not source[-1].isnumeric():
                if source[-7:-1].isnumeric():
                    res = source[2:-7]
                elif source[-6:-1].isnumeric():
                    res = source[2:-6]
                elif source[-5:-1].isnumeric():
                    res = source[2:-5]
                elif source[-4:-1].isnumeric():
                    res = source[2:-4]
            if source[-6:].isnumeric():
                res = source[2:-6]
            elif source[-5:].isnumeric():
                res = source[2:-5]
            elif source[-4:].isnumeric():
                res = source[2:-4]
            elif source[-3:].isnumeric():
                res = source[2:-3]
        elif source and source[:4] == 'APM/':
            rac = source[14:-4]
            if rac == 'VRAC':
                res = 'VRA'
            elif rac == 'GC':
                res = 'GCC'
            elif rac == 'SAC':
                res = 'SAC'
            elif rac == 'BOIS':
                res = 'BOD'
        _logger.info('res : %s' % res)
        if res:
            if res in ('DDMI', 'DDME', 'DDAI', 'DDAE', 'DTRI', 'DTRE', 'DTAI', 'DTAE', 'TDMI', 'TDME', 'TDAI', 'TDAE', 'TTRI', 'TTRE', 'TTAI', 'TTAE', 'DLOG'):
                if move_type and move_type == 'out_refund':
                    res = 'A' + res
                else:
                    res = 'F' + res[1:]
            else:
                if move_type and move_type == 'out_refund':
                    res = 'A' + res
                else:
                    res = 'F' + res
                # res = 'F'+ res
            # res = 'F' + res
        return res

    def _generate_APM_Credit_Debit_Note_reference(self, move_type):
        code = ''
        if move_type == 'out_refund':
            code = 'APMCN'
        elif move_type == 'in_refund':
            code = 'APMDN'
        if not code:
            return
        return self._get_sequence_name(code)


    def _generate_APM_reference(self, source, import_pad_invoice=None, export_pad_invoice=None, additional_invoice=None, move_type = None):
        if import_pad_invoice:
            if move_type and move_type == 'out_refund':
                return self._get_sequence_name('servoo.import.avoir.pad.apm.number')
            return self._get_sequence_name('servoo.import.invoice.pad.apm.number')
        elif export_pad_invoice:
            if move_type and move_type == 'out_refund':
                return self._get_sequence_name('servoo.export.avoir.pad.apm.number')
            return self._get_sequence_name('servoo.export.invoice.pad.apm.number')
        # ref=''
        if source and additional_invoice:
            q = "SELECT apm_reference FROM account_move where invoice_origin = '%s' and apm_reference is not null order by id desc" % source
            self._cr.execute(q)
            res = self._cr.fetchall()
            if res and res[0][0]:
                ref = res[0][0] + "-" + str(len(res))
                return ref
        ref = self._get_root(source, move_type)
        sequence = self._get_sequence_name(ref)
        return sequence

    @api.model
    def create(self, vals):
        move_type = vals.get('move_type')
        if move_type in ('out_invoice', 'out_refund'):
            vals['apm_reference'] = self._generate_APM_reference(vals.get('invoice_origin'), vals.get('import_pad_invoice'), vals.get('export_pad_invoice'), vals.get('additional_invoice'), move_type)
        else:
            vals['apm_reference'] = self._generate_APM_Credit_Debit_Note_reference(move_type)
        return super(AccountMove, self).create(vals)

    api.model
    def write(self, vals):
        if not self.apm_reference:
            origin = vals['invoice_origin'] if vals.get('invoice_origin') else self.invoice_origin
            additional_invoice = vals['additional_invoice'] if vals.get('additional_invoice') else self.additional_invoice
            import_pad_invoice = vals['import_pad_invoice'] if vals.get('import_pad_invoice') else self.import_pad_invoice
            export_pad_invoice = vals['export_pad_invoice'] if vals.get('export_pad_invoice') else self.export_pad_invoice
            if self.move_type =='in_refund':
                vals['apm_reference'] = self._generate_APM_Credit_Debit_Note_reference(self.move_type)
            else:
                vals['apm_reference'] = self._generate_APM_reference(origin, import_pad_invoice, export_pad_invoice, additional_invoice, self.move_type)
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


    def _compute_line_data_for_template_change(self, line):
        return {
            # 'sequence': line.sequence,
            'display_type': line.display_type,
            'name': line.name,
        }

    def _sum_rule_amount(self, localdict, line, amount):
        localdict['rules'].dict[line.code] = line.code in localdict['rules'].dict and localdict['rules'].dict[line.code] + amount or amount
        return localdict

    def init_dicts(self):
        class BrowsableObject(object):
            def __init__(self, dict, env):
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        rules_dict = {}
        rules = BrowsableObject(rules_dict, self.env)
        var_dict = {
            'VOLUME': self.volume,
            'TONNAGE': self.weight,
            'ROYALTY': self.handling,
            'ROYALTY2': self.handling2,
            'ROYALTY3': self.handling3,
            'QUANTITY': self.quantity,
            'QUANTITY2': self.quantity2,
            'QUANTITY3': self.quantity3,
            'rules': rules
        }
        return dict(var_dict)

    def _get_computed_account(self, product_id):
        if not product_id:
            return
        accounts = product_id.product_tmpl_id.get_product_accounts()
        return accounts['income']

    def _apply_added_lines(self):
        for line in self.invoice_line_ids:
            line.account_id = line._get_computed_account()
            taxes = line._get_computed_taxes()
            if taxes and line.move_id.fiscal_position_id:
                taxes = line.move_id.fiscal_position_id.map_tax(taxes)
            line.tax_ids = taxes

    def _get_template_lines(self, template_id, localdict):
        # invoice_lines = [(5, 0, 0)]
        invoice_lines = []
        self.invoice_line_ids = [(5, 0, 0)]
        self.line_ids = [(5, 0, 0)]
        template = self.env['sale.order.template'].browse(template_id)
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            localdict['result'] = None
            localdict['result_qty'] = 1.0
            if line.product_id:
                amount, qty = line._compute_rule(localdict)
                if line.code:
                    total_rule = amount * qty
                    localdict[line.code] = total_rule
                    localdict = self._sum_rule_amount(localdict, line, total_rule)
                price = amount
                data.update({
                    'price_unit': price,
                    'quantity': qty,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'currency_id': self.currency_id.id,
                })
            invoice_lines.append((0, 0, data))
        self.invoice_line_ids = invoice_lines
        self._apply_added_lines()
        self.invoice_line_ids._onchange_price_subtotal()
        self._onchange_tax_totals_json()


    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):
        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)
        localdict = self.init_dicts()
        self._get_template_lines(self.sale_order_template_id.id, localdict)
        if not is_html_empty(template.note):
            self.note = template.note

    @api.onchange('weight', 'volume', 'handling', 'quantity','handling2', 'quantity2','handling3', 'quantity3', 'include_tax_for_handling', 'include_tax_for_handling2', 'include_tax_for_handling3', 'handling_rate_id', 'handling_rate_2_id', 'handling_rate_3_id')
    def onchange_variables(self):
        localdict = self.init_dicts()
        self._get_template_lines(self.sale_order_template_id.id, localdict)

    @api.onchange('handling_rate_id')
    def onchange_hanlding_rate(self):
        self.handling = self.handling_rate_id.rate

    @api.onchange('handling_rate_2_id')
    def onchange_hanlding_rate2(self):
        self.handling2 = self.handling_rate_2_id.rate

    @api.onchange('handling_rate_3_id')
    def onchange_hanlding_rate3(self):
        self.handling3 = self.handling_rate_3_id.rate

    @api.onchange('include_tax_for_handling')
    def onchange_include_tax(self):
        if self.handling == 0.0:
            return
        rate = self.handling
        if self.include_tax_for_handling:
            rate += rate * 0.1925
        else:
            rate = self.handling_rate_id.rate
        self.handling = rate

    @api.onchange('include_tax_for_handling2')
    def onchange_include_tax2(self):
        if self.handling2 == 0.0:
            return
        rate = self.handling2
        if self.include_tax_for_handling2:
            rate += rate * 0.1925
        else:
            rate = self.handling_rate_2_id.rate
        self.handling2 = rate

    @api.onchange('include_tax_for_handling3')
    def onchange_include_tax3(self):
        if self.handling3 == 0.0:
            return
        rate = self.handling3
        if self.include_tax_for_handling3:
            rate += rate * 0.1925
        else:
            rate = self.handling_rate_3_id.rate
        self.handling3 = rate

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
        """ Compute the dynamic tax lines of the journal entry.

        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        """
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                is_refund = move.move_type in ('out_refund', 'in_refund')
                price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
            else:
                handle_price_include = False
                quantity = 1.0
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
                price_unit_wo_discount = base_line.amount_currency

            if base_line.no_days and base_line.no_days > 0:
                quantity *= base_line.no_days
            return base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=move.always_tax_exigible,
            )

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
                taxes_map_entry['grouping_dict'] = grouping_dict

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                if not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

            # Don't create tax lines with zero balance.
            if currency.is_zero(taxes_map_entry['amount']):
                if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            balance = currency._convert(
                taxes_map_entry['amount'],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )
            amount_currency = currency.round(taxes_map_entry['amount'])
            sign = -1 if self.is_inbound() else 1
            to_write_on_line = {
                'amount_currency': amount_currency,
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,
                'price_total': sign * amount_currency,
                'price_subtotal': sign * amount_currency,
            }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                if tax_rep_lines_to_recompute and taxes_map_entry['tax_line'].tax_repartition_line_id not in tax_rep_lines_to_recompute:
                    continue

                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                # Create a new tax line.
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)

                if tax_rep_lines_to_recompute and tax_repartition_line not in tax_rep_lines_to_recompute:
                    continue

                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    no_days = fields.Integer('Days', help='Number of days')

    @api.onchange('no_days')
    def _onchange_nodays(self):
        self._onchange_price_subtotal()

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

    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None, no_days=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model(
            price_unit=self.price_unit if price_unit is None else price_unit,
            quantity=self.quantity if quantity is None else quantity,
            discount=self.discount if discount is None else discount,
            currency=self.currency_id if currency is None else currency,
            product=self.product_id if product is None else product,
            partner=self.partner_id if partner is None else partner,
            taxes=self.tax_ids if taxes is None else taxes,
            move_type=self.move_id.move_type if move_type is None else move_type,
            no_days=self.no_days if no_days is None else no_days
        )

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type, no_days = None):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :param no_days:     The number of days.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}
        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        qty = quantity * no_days if no_days and no_days > 0 else quantity
        subtotal = qty * line_discount_price_unit

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(line_discount_price_unit,
                                                                             quantity=qty, currency=currency,
                                                                             product=product, partner=partner,
                                                                             is_refund=move_type in (
                                                                             'out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res


    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        ACCOUNTING_FIELDS = ('debit', 'credit', 'amount_currency')
        BUSINESS_FIELDS = ('price_unit', 'quantity', 'discount', 'tax_ids')

        for vals in vals_list:
            no_days = vals.get('no_days')
            move = self.env['account.move'].browse(vals['move_id'])
            vals.setdefault('company_currency_id',
                            move.company_id.currency_id.id)  # important to bypass the ORM limitation where monetary fields are not rounded; more info in the commit message

            # Ensure balance == amount_currency in case of missing currency or same currency as the one from the
            # company.
            currency_id = vals.get('currency_id') or move.company_id.currency_id.id
            if currency_id == move.company_id.currency_id.id:
                balance = vals.get('debit', 0.0) - vals.get('credit', 0.0)
                vals.update({
                    'currency_id': currency_id,
                    'amount_currency': balance,
                })
            else:
                vals['amount_currency'] = vals.get('amount_currency', 0.0)

            if move.is_invoice(include_receipts=True):
                currency = move.currency_id
                partner = self.env['res.partner'].browse(vals.get('partner_id'))
                taxes = self.new({'tax_ids': vals.get('tax_ids', [])}).tax_ids
                tax_ids = set(taxes.ids)
                taxes = self.env['account.tax'].browse(tax_ids)

                # Ensure consistency between accounting & business fields.
                # As we can't express such synchronization as computed fields without cycling, we need to do it both
                # in onchange and in create/write. So, if something changed in accounting [resp. business] fields,
                # business [resp. accounting] fields are recomputed.
                if any(vals.get(field) for field in ACCOUNTING_FIELDS):
                    price_subtotal = self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                        no_days=no_days
                    ).get('price_subtotal', 0.0)
                    vals.update(self._get_fields_onchange_balance_model(
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        vals['amount_currency'],
                        move.move_type,
                        currency,
                        taxes,
                        price_subtotal,
                        no_days=no_days
                    ))
                    vals.update(self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                        no_days=no_days
                    ))
                elif any(vals.get(field) for field in BUSINESS_FIELDS):
                    vals.update(self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                        no_days=no_days
                    ))
                    vals.update(self._get_fields_onchange_subtotal_model(
                        vals['price_subtotal'],
                        move.move_type,
                        currency,
                        move.company_id,
                        move.date
                    ))

        lines = super(AccountMoveLine, self).create(vals_list)

        moves = lines.mapped('move_id')
        if self._context.get('check_move_validity', True):
            moves._check_balanced()
        moves.filtered(lambda m: m.state == 'posted')._check_fiscalyear_lock_date()
        lines.filtered(lambda l: l.parent_state == 'posted')._check_tax_lock_date()
        moves._synchronize_business_models({'line_ids'})
        lines._onchange_price_subtotal()
        return lines
    #
    def _get_fields_onchange_balance(self, quantity=None, discount=None, amount_currency=None, move_type=None, currency=None, taxes=None, price_subtotal=None, force_computation=False, no_days=None):
        self.ensure_one()
        return self._get_fields_onchange_balance_model(
            quantity=self.quantity if quantity is None else quantity,
            discount=self.discount if discount is None else discount,
            amount_currency=self.amount_currency if amount_currency is None else amount_currency,
            move_type=self.move_id.move_type if move_type is None else move_type,
            currency=(self.currency_id or self.move_id.currency_id) if currency is None else currency,
            taxes=self.tax_ids if taxes is None else taxes,
            price_subtotal=self.price_subtotal if price_subtotal is None else price_subtotal,
            force_computation=force_computation,
            no_days = self.no_days if no_days is None else no_days
        )


    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes, price_subtotal, force_computation=False, no_days=None):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param amount_currency: The new balance in line's currency.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :param no_days:         The number of days.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}
        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(amount_currency, currency=currency, handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    amount_currency += tax_res['amount']

        discount_factor = 1 - (discount / 100.0)
        if (not no_days or no_days == 0) and price_subtotal and price_subtotal != 0:
            no_days = int(amount_currency / price_subtotal)
        if amount_currency and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': amount_currency / discount_factor / (quantity or 1.0) / (no_days or 1.0),
            }
            if no_days and no_days > 0:
                vals['no_days'] = no_days
                vals['price_total'] = amount_currency
        elif amount_currency and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                'price_unit': amount_currency / (quantity or 1.0) / (no_days or 1.0),
            }
            if no_days and no_days > 0:
                vals['no_days'] = no_days
                vals['price_total'] = amount_currency
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        return vals
