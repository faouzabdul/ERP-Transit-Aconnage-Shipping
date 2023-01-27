# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    volume = fields.Float('Volume (m3)', digits=(12, 3))
    weight = fields.Float('Weight', digits=(12, 3))
    unit_id = fields.Many2one('res.unit', 'Unit')


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    code = fields.Char('Code')
    quantity_python_compute = fields.Char(default='result_qty = 1.0', string='Quantity formula',
                                          help=""" # Available variables:
                                                       #----------------------
                                                       # VOLUME: the volume                                                
                                                       # TONNAGE: The tonnage of goods in the vessel
                                                       # rules: object containing the rules code (previously computed)

                                                       # Note: returned value have to be set in the variable 'result_qty'""")
    amount_python_compute = fields.Text(string='Amount Formula', default="result = 1.0",
                                        help=""" # Available variables:
                                                     #----------------------
                                                     # VOLUME: the CBM of vessel
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
            except Exception as ex:
                raise UserError(_(
                    """
                    Wrong python code defined for amount formula %s in line %s.
                    Here is the error received:
                    %s
                    """
                ) % (self.amount_python_compute, self.name, repr(ex)))
        return amount, qty