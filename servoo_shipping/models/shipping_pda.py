# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from datetime import datetime, timedelta
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty

from odoo.addons.payment import utils as payment_utils


class ShippingPda(models.Model):
    _name = "servoo.shipping.pda"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Shipping PDA"
    _order = 'date_pda desc, id desc'
    _check_company_auto = True


    @api.depends('shipping_pda_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.shipping_pda_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    def _get_payment(self):
        payment = self.env['account.payment']
        for record in self:
            payments = payment.search([('ref', '=', record.name)])
            record.payment_ids = payments
            record.payment_count = len(payments)

    def _get_invoiced(self):
        invoice = self.env['account.move']
        for record in self:
            invoices = invoice.search([('invoice_origin', '=', record.name)])
            record.invoice_ids = invoices
            record.invoice_count = len(invoices)

    @api.depends('state', 'shipping_pda_line.invoice_status')
    def _get_invoice_status(self):
        """
        Compute the invoice status of a PDA. Possible statuses:
        - no: if the PDA is not in status 'won', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any PDA line is 'to invoice', the whole PDA is 'to invoice'
        - invoiced: if all PDA lines are invoiced, the PDA is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        unconfirmed_pdas = self.filtered(lambda so: so.state not in ['won'])
        unconfirmed_pdas.invoice_status = 'no'
        confirmed_pdas = self - unconfirmed_pdas
        if not confirmed_pdas:
            return
        line_invoice_status_all = [
            (d['shipping_pda_id'][0], d['invoice_status'])
            for d in self.env['servoo.shipping.pda.line'].read_group([
                    ('shipping_pda_id', 'in', confirmed_pdas.ids),
                    ('is_downpayment', '=', False),
                    ('display_type', '=', False),
                ],
                ['shipping_pda_id', 'invoice_status'],
                ['shipping_pda_id', 'invoice_status'], lazy=False)]
        for order in confirmed_pdas:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state not in 'won':
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'

    @api.model
    def get_empty_list_help(self, help):
        self = self.with_context(
            empty_list_help_document_name=_("shipping pda"),
        )
        return super(ShippingPda, self).get_empty_list_help(help)

    @api.model
    def _default_note_url(self):
        return self.env.company.get_base_url()

    @api.model
    def _default_note(self):
        use_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms')
        if use_invoice_terms and self.env.company.terms_type == "html":
            baseurl = html_keep_url(self._default_note_url() + '/terms')
            return _('Terms & Conditions: %s', baseurl)
        return use_invoice_terms and self.env.company.invoice_terms or ''

    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed on the SO.
        """
        for order in self:
            order.shipping_pda_line._compute_tax_id()

    def _search_invoice_ids(self, operator, value):
        if operator == 'in' and value:
            self.env.cr.execute("""
                SELECT array_agg(pda.id)
                    FROM servoo_shipping_pda pda
                    JOIN servoo_shipping_pda_line pdal ON pdal.shipping_pda_id = pda.id
                    JOIN servoo_shipping_pda_line_invoice_rel pdal_rel ON pdal_rel.shipping_pda_line_id = pda.id
                    JOIN account_move_line aml ON aml.id = pdal_rel.invoice_line_id
                    JOIN account_move am ON am.id = aml.move_id
                WHERE
                    am.move_type in ('out_invoice', 'out_refund') AND
                    am.id = ANY(%s)
            """, (list(value),))
            so_ids = self.env.cr.fetchone()[0] or []
            return [('id', 'in', so_ids)]
        elif operator == '=' and not value:
            # special case for [('invoice_ids', '=', False)], i.e. "Invoices is not set"
            #
            # We cannot just search [('shipping_pda_line.invoice_lines', '=', False)]
            # because it returns pdas with uninvoiced lines, which is not
            # same "Invoices is not set" (some lines may have invoices and some
            # doesn't)
            #
            # A solution is making inverted search first ("pdas with invoiced
            # lines") and then invert results ("get all other pdas")
            #
            # Domain below returns subset of ('shipping_pda_line.invoice_lines', '!=', False)
            shipping_pda_ids = self._search([
                ('shipping_pda_line.invoice_lines.move_id.move_type', 'in', ('out_invoice', 'out_refund'))
            ])
            return [('id', 'not in', shipping_pda_ids)]
        return ['&', ('shipping_pda_line.invoice_lines.move_id.move_type', 'in', ('out_invoice', 'out_refund')), ('shipping_pda_line.invoice_lines.move_id', operator, value)]


    def _search_payment_ids(self, operator, value):
        if operator == 'in' and value:
            self.env.cr.execute("""
                SELECT array_agg(pda.id)
                    FROM servoo_shipping_pda pda
                    JOIN account_payment ap ON ap.ref = pda.name
                WHERE
                    ap.payment_type = 'inbound' AND
                    ap.id = ANY(%s)
            """, (list(value),))
            so_ids = self.env.cr.fetchone()[0] or []
            return [('id', 'in', so_ids)]
        elif operator == '=' and not value:
            shipping_pda_ids = self._search()
            return [('id', 'not in', shipping_pda_ids)]
        return []

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    origin = fields.Char(string='Source Document', help="Reference of the document that generated this sales order request.")
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    reference = fields.Char(string='Payment Ref.', copy=False,
        help='The payment communication of this shipping pda.')
    paid_amount = fields.Float('Paid Amount')
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
    ], string="Payment Status", store=True, default='not_paid',
        readonly=True, copy=False, tracking=True)
    payment_count = fields.Integer(string='Payment Count', compute='_get_payment')
    payment_ids = fields.Many2many("account.payment", 'account_payment_shipping_pda_rel', string='Payments',
                                   compute="_get_payment", copy=False, search="_search_payment_ids")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    date_pda = fields.Datetime(string='PDA Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now, help="Creation date of draft/sent pdas,\nConfirmation date of confirmed pdas.")

    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which PDA is created.")

    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ),)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'won': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'won': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)

    currency_id = fields.Many2one('res.currency', 'Currency', states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account',
        compute='_compute_analytic_account_id', store=True,
        readonly=False, copy=False, check_company=True,  # Unrequired company
        states={'won': [('readonly', True)], 'lost': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales order.")

    shipping_pda_line = fields.One2many('servoo.shipping.pda.line', 'shipping_pda_id', string='Lines', states={'cancel':[('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]}, copy=True, auto_join=True)

    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced')
    invoice_ids = fields.Many2many("account.move", 'account_move_shipping_pda_rel', string='Invoices', compute="_get_invoiced", copy=False, search="_search_invoice_ids")
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status', compute='_get_invoice_status', store=True)

    note = fields.Html('Terms and conditions', default=_default_note)
    # terms_type = fields.Selection(related='company_id.terms_type')

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, compute='_amount_all', tracking=5)
    tax_totals_json = fields.Char(compute='_compute_tax_totals_json')
    amount_tax = fields.Monetary(string='Taxes', store=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, compute='_amount_all', tracking=4)
    currency_rate = fields.Float("Currency Rate", compute='_compute_currency_rate', store=True, digits=(12, 6), help='The rate of the currency to the currency of rate 1 applicable at the date of the order')

    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms')
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position',
        domain="[('company_id', '=', company_id)]", check_company=True,
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales pdas/invoices."
        "The default value comes from the customer.")
    tax_country_id = fields.Many2one(
        comodel_name='res.country',
        compute_sudo=True,
        help="Technical field to filter the available taxes depending on the fiscal country and fiscal position.")
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    commitment_date = fields.Datetime('Delivery Date', copy=False,
                                      states={'won': [('readonly', True)], 'cancel': [('readonly', True)], 'lost': [('readonly', True)]},
                                      help="This is the delivery date promised to the customer. "
                                           "If set, the delivery order will be scheduled based on "
                                           "this date rather than product lead times.")
    expected_date = fields.Datetime("Expected Date", compute='_compute_expected_date', store=False,  # Note: can not be stored since depends on today()
        help="Delivery date you can promise to the customer, computed from the minimum lead time of the order lines.")
    amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_amount_undiscounted', digits=0)

    transaction_ids = fields.Many2many('payment.transaction', 'servoo_shipping_pda_transaction_rel', 'sale_shipping_pda_id', 'transaction_id',
                                       string='Transactions', copy=False, readonly=True)
    authorized_transaction_ids = fields.Many2many('payment.transaction', compute='_compute_authorized_transaction_ids',
                                                  string='Authorized Transactions', copy=False)
    show_update_pricelist = fields.Boolean(string='Has Pricelist Changed',
                                           help="Technical Field, True if the pricelist was changed;\n"
                                                " this will then display a recomputation button")
    tag_ids = fields.Many2many('crm.tag', 'servoo_shipping_pda_tag_rel', 'shipping_pda_id', 'tag_id', string='Tags')
    operation_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('transit', 'Transit'),
    ], states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    vessel_id = fields.Many2one('res.transport.means', 'Vessel', tracking=6, states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    voyage_number = fields.Char('Travel Number', states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    eta = fields.Date('ETA', states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    etd = fields.Date('ETD', states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    loa = fields.Float('LOA', digits=(6, 3), states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    beam = fields.Float('Beam', digits=(6, 3), states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    summer_draft = fields.Float('Summer draft', digits=(6, 3), states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    vessel_volume = fields.Float('Vessel Volume', digits=(6, 3), states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    nrt = fields.Float('NRT', digits=(6, 3), states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    tonnage_of_goods = fields.Float('Tonnage of goods', digits=(6, 3), tracking=6, states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    volume_of_goods = fields.Float('Volume of goods', digits=(6, 3), states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    number_of_days = fields.Integer('Number of days', required=False, tracking=6, states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    grt = fields.Float('GRT', digits=(12, 4), required=False, tracking=6, states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    cbm_vessel = fields.Float('CBM Vessel', digits=(12, 4), required=False, tracking=6, states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})
    location_code = fields.Many2one('res.locode', 'Localisation Code', tracking=6, states={'cancel': [('readonly', True)], 'won': [('readonly', True)], 'lost': [('readonly', True)]})

    _sql_constraints = [
        ('date_order_conditional_required', "CHECK( (state IN ('won', 'done') AND date_pda IS NOT NULL) OR state NOT IN ('won', 'done') )", "A confirmed shipping PDA requires a confirmation date."),
    ]

    @api.onchange('loa', 'beam', 'summer_draft')
    def compute_cbm(self):
        self.cbm_vessel = self.loa * self.beam * self.summer_draft

    @api.constrains('company_id', 'shipping_pda_line')
    def _check_shipping_pda_line_company_id(self):
        for order in self:
            companies = order.shipping_pda_line.product_id.company_id
            if companies and companies != order.company_id:
                bad_products = order.shipping_pda_line.product_id.filtered(lambda p: p.company_id and p.company_id != order.company_id)
                raise ValidationError(_(
                    "Your PDA contains products from company %(product_company)s whereas your PDA belongs to company %(quote_company)s. \n Please change the company of your PDA or remove the products from other companies (%(bad_products)s).",
                    product_company=', '.join(companies.mapped('display_name')),
                    quote_company=order.company_id.display_name,
                    bad_products=', '.join(bad_products.mapped('display_name')),
                ))

    @api.depends('currency_id', 'date_pda', 'company_id')
    def _compute_currency_rate(self):
        for order in self:
            if not order.company_id:
                order.currency_rate = order.currency_id.with_context(date=order.date_pda).rate or 1.0
                continue
            elif order.company_id.currency_id and order.currency_id:  # the following crashes if any one is undefined
                order.currency_rate = self.env['res.currency']._get_conversion_rate(order.company_id.currency_id, order.currency_id, order.company_id, order.date_pda)
            else:
                order.currency_rate = 1.0

    def _compute_access_url(self):
        super(ShippingPda, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/pdas/%s' % (order.id)

    @api.depends('shipping_pda_line.customer_lead', 'date_pda', 'shipping_pda_line.state')
    def _compute_expected_date(self):
        """ For service and consumable, we only take the min dates. This method is extended in sale_stock to
            take the picking_policy of SO into account.
        """
        self.mapped("shipping_pda_line")  # Prefetch indication
        for order in self:
            dates_list = []
            for line in order.shipping_pda_line.filtered(lambda x: x.state != 'cancel' and not x._is_delivery() and not x.display_type):
                dt = line._expected_date()
                dates_list.append(dt)
            if dates_list:
                order.expected_date = fields.Datetime.to_string(min(dates_list))
            else:
                order.expected_date = False

    @api.depends('shipping_pda_line.tax_id', 'shipping_pda_line.price_unit', 'amount_total', 'amount_untaxed')
    def _compute_tax_totals_json(self):
        def compute_taxes(shipping_pda_line):
            price = shipping_pda_line.price_unit * (1 - (shipping_pda_line.discount or 0.0) / 100.0)
            order = shipping_pda_line.shipping_pda_id
            return shipping_pda_line.tax_id._origin.compute_all(price, order.currency_id, shipping_pda_line.product_uom_qty, product=shipping_pda_line.product_id, partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.shipping_pda_line, compute_taxes)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
            order.tax_totals_json = json.dumps(tax_totals)

    @api.depends('transaction_ids')
    def _compute_authorized_transaction_ids(self):
        for trans in self:
            trans.authorized_transaction_ids = trans.transaction_ids.filtered(lambda t: t.state == 'authorized')

    def _compute_amount_undiscounted(self):
        for order in self:
            total = 0.0
            for line in order.shipping_pda_line:
                total += (line.price_subtotal * 100)/(100-line.discount) if line.discount != 100 else (line.price_unit * line.product_uom_qty)
            order.amount_undiscounted = total

    @api.depends('partner_id', 'date_pda')
    def _compute_analytic_account_id(self):
        for order in self:
            if not order.analytic_account_id:
                default_analytic_account = order.env['account.analytic.default'].sudo().account_get(
                    partner_id=order.partner_id.id,
                    user_id=order.env.uid,
                    date=order.date_pda,
                    company_id=order.company_id.id,
                )
                order.analytic_account_id = default_analytic_account.analytic_id

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete a sent pda or a confirmed one. You must first cancel it.'))

    def validate_taxes_on_sales_order(self):
        # Override for correct taxcloud computation
        # when using coupon and delivery
        return True

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'won':
            return self.env.ref('servoo_shipping.mt_pda_confirmed')
        elif 'state' in init_values and self.state == 'sent':
            return self.env.ref('servoo_shipping.mt_pda_sent')
        return super(ShippingPda, self)._track_subtype(init_values)

    @api.onchange('partner_shipping_id', 'partner_id', 'company_id')
    def onchange_partner_shipping_id(self):
        """
        Trigger the change of fiscal position when the shipping address is modified.
        """
        self.fiscal_position_id = self.env['account.fiscal.position'].with_company(self.company_id).get_fiscal_position(self.partner_id.id, self.partner_shipping_id.id)
        return {}

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        self = self.with_company(self.company_id)

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms'):
            if self.env.company.invoice_terms_html:
                baseurl = html_keep_url(self.get_base_url() + '/terms')
                values['note'] = _('Terms & Conditions: %s', baseurl)
            elif not is_html_empty(self.env.company.invoice_terms):
                values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        self.update(values)


    @api.onchange('partner_id')
    def _onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn and partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' and partner.parent_id and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id

            if partner.sale_warn == 'block':
                self.update({'partner_id': False, 'partner_invoice_id': False, 'partner_shipping_id': False})

            return {
                'warning': {
                    'title': _("Warning for %s", partner.name),
                    'message': partner.sale_warn_msg,
                }
            }

    @api.onchange('commitment_date', 'expected_date')
    def _onchange_commitment_date(self):
        """ Warn if the commitment dates is sooner than the expected date """
        if (self.commitment_date and self.expected_date and self.commitment_date < self.expected_date):
            return {
                'warning': {
                    'title': _('Requested date is too soon.'),
                    'message': _("The delivery date is sooner than the expected date."
                                 "You may be unable to honor the delivery date.")
                }
            }

    def _get_update_prices_lines(self):
        """ Hook to exclude specific lines which should not be updated based on price list recomputation """
        return self.shipping_pda_line.filtered(lambda line: not line.display_type)

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_pda' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_pda']))
            vals['name'] = self.env['ir.sequence'].next_by_code('servoo.shipping.pda', sequence_date=seq_date) or _('New')

        # Makes sure partner_invoice_id' and 'partner_shipping_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
        result = super(ShippingPda, self).create(vals)
        return result

    def _compute_field_value(self, field):
        if field.name == 'invoice_status' and not self.env.context.get('mail_activity_automation_skip'):
            filtered_self = self.filtered(lambda so: (so.user_id or so.partner_id.user_id) and so._origin.invoice_status != 'upselling')
        super()._compute_field_value(field)
        if field.name != 'invoice_status' or self.env.context.get('mail_activity_automation_skip'):
            return

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'shipping_pda_line' not in default:
            default['shipping_pda_line'] = [(0, 0, line.copy_data()[0]) for line in self.shipping_pda_line.filtered(lambda l: not l.is_downpayment)]
        return super(ShippingPda, self).copy_data(default)

    def name_get(self):
        if self._context.get('sale_show_partner_name'):
            res = []
            for order in self:
                name = order.name
                if order.partner_id.name:
                    name = '%s - %s' % (name, order.partner_id.name)
                res.append((order.id, name))
            return res
        return super(ShippingPda, self).name_get()

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if self._context.get('sale_show_partner_name'):
            if operator == 'ilike' and not (name or '').strip():
                domain = []
            elif operator in ('ilike', 'like', '=', '=like', '=ilike'):
                domain = expression.AND([
                    args or [],
                    ['|', ('name', operator, name), ('partner_id.name', operator, name)]
                ])
                return self._search(domain, limit=limit, access_rights_uid=name_get_uid)
        return super(ShippingPda, self)._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)


    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).', self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'user_id': self.user_id.id,
            'invoice_user_id': self.user_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_invoice_id.id)).id,
            'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def action_pda_sent(self):
        if self.filtered(lambda so: so.state != 'draft'):
            raise UserError(_('Only draft pdas can be marked as sent directly.'))
        for order in self:
            order.message_subscribe(partner_ids=order.partner_id.ids)
        self.write({'state': 'sent'})

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_shipping_id.id,
                'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin': self.name,
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action

    def _get_invoice_grouping_keys(self):
        return ['company_id', 'partner_id', 'currency_id']

    @api.model
    def _nothing_to_invoice_error(self):
        return UserError(_(
            "There is nothing to invoice!\n\n"
            "Reason(s) of this behavior could be:\n"
            "- You should deliver your products before invoicing them: Click on the \"truck\" icon "
            "(top-right of your screen) and follow instructions.\n"
            "- You should modify the invoicing policy of your product: Open the product, go to the "
            "\"Sales\" tab and modify invoicing policy from \"delivered quantities\" to \"ordered "
            "quantities\". For Services, you should modify the Service Invoicing Policy to "
            "'Prepaid'."
        ))

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.shipping_pda_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['servoo.shipping.pda.line'].browse(invoiceable_line_ids + down_payment_line_ids)

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the PDA.
        :param grouped: if True, invoices are grouped by PDA id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['servoo.shipping.pda.line']

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # pdas, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            ShippingPdaLine = self.env['servoo.shipping.pda.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = ShippingPdaLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # shipping pda without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        # for move in moves:
        #     move.message_post_with_view('mail.message_origin_link',
        #         values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.shipping_pda_id')},
        #         subtype_id=self.env.ref('mail.mt_note').id
        #     )
        return moves

    def create_invoices(self):
        moves = self._create_invoices()
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

    def action_draft(self):
        pdas = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        return pdas.write({
            'state': 'draft'
        })

    def action_cancel(self):
        cancel_warning = self._show_cancel_wizard()
        if cancel_warning:
            return {
                'name': _('Cancel PDA'),
                'view_mode': 'form',
                'res_model': 'servoo.shipping.pda.cancel',
                'view_id': self.env.ref('servoo_shipping.servoo_shipping_pda_cancel_view_form').id,
                'type': 'ir.actions.act_window',
                'context': {'default_shipping_pda_id': self.id},
                'target': 'new'
            }
        return self._action_cancel()

    def _action_cancel(self):
        inv = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        inv.button_cancel()
        return self.write({'state': 'cancel'})

    def _show_cancel_wizard(self):
        for order in self:
            if order.invoice_ids.filtered(lambda inv: inv.state == 'draft') and not order._context.get('disable_cancel_warning'):
                return True
        return False

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = int(
            self.env['ir.config_parameter'].sudo().get_param('servoo_shipping.default_confirmation_template'))
        template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
        if not template_id:
            template_id = self.env['ir.model.data']._xmlid_to_res_id('servoo_shipping.mail_template_pda_confirmation',
                                                                     raise_if_not_found=False)
        return template_id

    def action_send(self):
        self.write({'state': 'sent'})

    def action_pda_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'servoo.shipping.pda',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_pda_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': 'PDA',
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_pda_as_sent'):
            self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})
        return super(ShippingPda, self.with_context(mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    def _sms_get_number_fields(self):
        """ No phone or mobile field is available on sale model. Instead SMS will
        fallback on partner-based computation using ``_sms_get_partner_fields``. """
        return []

    def _sms_get_partner_fields(self):
        return ['partner_id']

    def _send_order_confirmation_mail(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        template_id = self._find_mail_template(force_confirmation_template=True)
        if template_id:
            for order in self:
                order.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment', email_layout_xmlid="mail.mail_notification_paynow")

    def action_done(self):
        for order in self:
            tx = order.sudo().transaction_ids._get_last()
            if tx and tx.state == 'pending' and tx.acquirer_id.provider == 'transfer':
                tx._set_done()
                tx.write({'is_post_processed': True})
        return self.write({'state': 'won'})

    def action_lose(self):
        return self.write({'state': 'lost'})

    def action_unlock(self):
        self.write({'state': 'won'})

    def _action_confirm(self):
        """ Implementation of additionnal mecanism of Sales Order confirmation.
            This method should be extended when the confirmation should generated
            other documents. In this method, the SO are in 'won' state.
        """
        # create an analytic account if at least an expense product
        for order in self:
            if any(expense_policy not in [False, 'no'] for expense_policy in order.shipping_pda_line.mapped('product_id.expense_policy')):
                if not order.analytic_account_id:
                    order._create_analytic_account()

        return True

    def _prepare_confirmation_values(self):
        return {
            'state': 'won',
            'date_pda': fields.Datetime.now()
        }

    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True

    def _get_forbidden_state_confirm(self):
        return {'lost', 'cancel', 'won'}

    def _prepare_analytic_account_data(self, prefix=None):
        """
        Prepare method for analytic account data

        :param prefix: The prefix of the to-be-created analytic account name
        :type prefix: string
        :return: dictionary of value for new analytic account creation
        """
        name = self.name
        if prefix:
            name = prefix + ": " + self.name
        return {
            'name': name,
            'code': self.client_order_ref,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id
        }

    def _create_analytic_account(self, prefix=None):
        for order in self:
            analytic = self.env['account.analytic.account'].create(order._prepare_analytic_account_data(prefix))
            order.analytic_account_id = analytic

    def _notify_get_groups(self, msg_vals=None):
        """ Give access button to users and portal customer as portal is integrated
        in sale. Customer and portal group have probably no right to see
        the document so they don't have the access button. """
        groups = super(ShippingPda, self)._notify_get_groups(msg_vals=msg_vals)

        self.ensure_one()
        if self.state not in ('draft', 'cancel'):
            for group_name, group_method, group_data in groups:
                if group_name not in ('customer', 'portal'):
                    group_data['has_button_access'] = True

        return groups

    def _force_lines_to_invoice_policy_order(self):
        for line in self.shipping_pda_line:
            if self.state in 'won':
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    def payment_action_capture(self):
        """ Capture all transactions linked to this shipping pda. """
        payment_utils.check_rights_on_recordset(self)
        # In sudo mode because we need to be able to read on acquirer fields.
        self.authorized_transaction_ids.sudo().action_capture()

    def payment_action_void(self):
        """ Void all transactions linked to this shipping pda. """
        payment_utils.check_rights_on_recordset(self)
        # In sudo mode because we need to be able to read on acquirer fields.
        self.authorized_transaction_ids.sudo().action_void()

    def get_portal_last_transaction(self):
        self.ensure_one()
        return self.transaction_ids._get_last()

    @api.model
    def _get_customer_lead(self, product_tmpl_id):
        return False

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'PDA %s' % self.name

    @api.model
    def _prepare_down_payment_section_line(self, **optional_values):
        """
        Prepare the dict of values to create a new down payment section for a sales order line.

        :param optional_values: any parameter that should be added to the returned down payment section
        """
        context = {'lang': self.partner_id.lang}
        down_payments_section_line = {
            'display_type': 'line_section',
            'name': _('Down Payments'),
            'product_id': False,
            'product_uom_id': False,
            'quantity': 0,
            'discount': 0,
            'price_unit': 0,
            'account_id': False
        }
        del context
        if optional_values:
            down_payments_section_line.update(optional_values)
        return down_payments_section_line

    def add_option_to_order_with_taxcloud(self):
        self.ensure_one()
