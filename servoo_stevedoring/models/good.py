# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class ShippingGood(models.Model):
    _inherit = 'servoo.shipping.good'

    customs_declaration_id = fields.Many2one('servoo.customs.declaration', 'Customs Declaration')

