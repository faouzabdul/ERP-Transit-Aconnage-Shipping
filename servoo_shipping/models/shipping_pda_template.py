# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
import logging

_logger = logging.getLogger(__name__)


class ShippingPdaTemplate(models.Model):
    _name = "servoo.shipping.pda.template"
    _description = "PDA Template"

    name = fields.Char('PDA Template', required=True)
    shipping_pda_template_line_ids = fields.One2many('servoo.shipping.pda.template.line', 'shipping_pda_template_id',
                                                     'Lines', copy=True)
    note = fields.Html('Terms and conditions', translate=True)
    active = fields.Boolean(default=True,
                            help="If unchecked, it will allow you to hide the quotation template without removing it.")
    company_id = fields.Many2one('res.company', string='Company')
    number_of_days = fields.Integer('Number of days', required=True)
    grt = fields.Float('GRT', digits=(12, 4), required=True)
    cbm_vessel = fields.Float('CBM Vessel', digits=(12, 4), required=True)
    tonnage = fields.Float('Tonnage', digits=(12, 4), required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    exchange_rate = fields.Float('Exchange rate', digits=(12, 4), required=True)

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        self.exchange_rate = self.currency_id.rate

    @api.constrains('company_id', 'shipping_pda_template_line_ids')
    def _check_company_id(self):
        for template in self:
            companies = template.mapped('shipping_pda_template_line_ids.product_id.company_id')
            if len(companies) > 1:
                raise ValidationError(_("Your template cannot contain products from multiple companies."))
            elif companies and companies != template.company_id:
                raise ValidationError(_(
                    "Your template contains products from company %(product_company)s whereas your template belongs to company %(template_company)s. \n Please change the company of your template or remove the products from other companies.",
                    product_company=', '.join(companies.mapped('display_name')),
                    template_company=template.company_id.display_name,
                ))

    @api.onchange('shipping_pda_template_line_ids')
    def _onchange_template_line_ids(self):
        companies = self.mapped('shipping_pda_template_line_ids.product_id.company_id')
        if companies and self.company_id not in companies:
            self.company_id = companies[0]

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ShippingPdaTemplate, self).create(vals_list)
        records._update_product_translations()
        return records

    def write(self, vals):
        if 'active' in vals and not vals.get('active'):
            companies = self.env['res.company'].sudo().search([('shipping_pda_template_id', 'in', self.ids)])
            companies.shipping_pda_template_id = None
        result = super(ShippingPdaTemplate, self).write(vals)
        self._update_product_translations()
        return result

    def _update_product_translations(self):
        languages = self.env['res.lang'].search([('active', '=', 'true')])
        for lang in languages:
            for line in self.shipping_pda_template_line_ids:
                if line.name == line.product_id.get_product_multiline_description_sale():
                    self.create_or_update_translations(model_name='servoo.shipping.pda.template.line,name',
                                                       lang_code=lang.code,
                                                       res_id=line.id, src=line.name,
                                                       value=line.product_id.with_context(
                                                           lang=lang.code).get_product_multiline_description_sale())

    def create_or_update_translations(self, model_name, lang_code, res_id, src, value):
        data = {
            'type': 'model',
            'name': model_name,
            'lang': lang_code,
            'res_id': res_id,
            'src': src,
            'value': value,
            'state': 'inprogress',
        }
        existing_trans = self.env['ir.translation'].search([('name', '=', model_name),
                                                            ('res_id', '=', res_id),
                                                            ('lang', '=', lang_code)])
        if not existing_trans:
            self.env['ir.translation'].create(data)
        else:
            existing_trans.write(data)


class ShippingPdaTemplateLine(models.Model):
    _name = "servoo.shipping.pda.template.line"
    _description = "Quotation Template Line"
    _order = 'shipping_pda_template_id, sequence, id'

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of pda quote lines.",
                              default=10)
    shipping_pda_template_id = fields.Many2one(
        'servoo.shipping.pda.template', 'Quotation Template Reference',
        required=True, ondelete='cascade', tracking=1)
    company_id = fields.Many2one('res.company', related='shipping_pda_template_id.company_id', store=True, tracking=1)
    code = fields.Char('Code')
    name = fields.Text('Description', required=True, translate=True)
    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        domain=[('sale_ok', '=', True)])
    product_uom_qty = fields.Float('Quantity', required=True, digits='Product Unit of Measure', default=1)
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure',
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    unit_price = fields.Float('Unit Price', digits=(12, 4))
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    quantity_python_compute = fields.Char(default='result_qty = 1.0', string='Quantity formula',
                                          help=""" # Available variables:
                                                   #----------------------
                                                   # CBM: the CBM of vessel
                                                   # GRT: the GRT
                                                   # DAY: The number of days
                                                   # TONNAGE: The tonnage of goods in the vessel
                                                   # rules: object containing the rules code (previously computed)
                                
                                                   # Note: returned value have to be set in the variable 'result_qty'""")
    amount_python_compute = fields.Text(string='Amount Formula', default="result = 1.0",
                                        help=""" # Available variables:
                                                 #----------------------
                                                 # CBM: the CBM of vessel
                                                 # GRT: the GRT
                                                 # DAY: The number of days
                                                 # TONNAGE: The tonnage of goods in the vessel
                                                 # rules: object containing the rules code (previously computed)

                                                 # Note: returned value have to be set in the variable 'result'""")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            self.name = self.product_id.get_product_multiline_description_sale()
            if self.product_id.default_code:
                self.code = self.product_id.default_code

    @api.model
    def create(self, values):
        if values.get('display_type', self.default_get(['display_type'])['display_type']):
            values.update(product_id=False, product_uom_qty=0, product_uom_id=False)
        return super(ShippingPdaTemplateLine, self).create(values)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_(
                "You cannot change the type of a sale quote line. Instead you should delete the current line and create a new line of the proper type."))
        return super(ShippingPdaTemplateLine, self).write(values)

    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float)
        """
        self.ensure_one()
        amount = 0.0
        try:
            safe_eval(self.quantity_python_compute, localdict, mode='exec', nocopy=True)
            qty = float(localdict['result_qty']) #if localdict['result_qty'] else 1.0
            # _logger.info('localdict after quantity_python_compute: %s' % localdict)
        except Exception as ex:
            raise UserError(_(
                """
                Wrong python code defined for quantity %s in line %s.
                Here is the error received:
                %s
                """
            ) % (self.quantity_python_compute, self.name, repr(ex)))
        if self.amount_python_compute:
            try:
                safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
                amount = float(localdict['result']) #if localdict['result'] else 1.0
                # _logger.info('localdict after amount_python_compute: %s' % localdict)
            except Exception as ex:
                raise UserError(_(
                    """
                    Wrong python code defined for amount formula %s in line %s.
                    Here is the error received:
                    %s
                    """
                ) % (self.amount_python_compute, self.name, repr(ex)))
        return amount, qty

    # _sql_constraints = [
    #     ('accountable_product_id_required',
    #      "CHECK(display_type IS NOT NULL OR (product_id IS NOT NULL AND product_uom_id IS NOT NULL))",
    #      "Missing required product and UoM on accountable sale quote line."),
    #
    #     ('non_accountable_fields_null',
    #      "CHECK(display_type IS NULL OR (product_id IS NULL AND product_uom_qty = 0 AND product_uom_id IS NULL))",
    #      "Forbidden product, unit price, quantity, and UoM on non-accountable sale quote line"),
    # ]
