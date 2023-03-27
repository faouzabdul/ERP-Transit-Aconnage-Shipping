# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _
import logging
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HandlingRate(models.Model):
    _name = 'servoo.handling.rate'
    _description = 'Handling Rate'

    name = fields.Char('Name', required=True)
    office_code_id = fields.Many2one('res.locode', string='Customs office')
    rate = fields.Float('Rate')
    operation = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], string='Sens Operation')
    category_id = fields.Many2one('servoo.handling.rate.category', 'Category')

    def name_get(self):
        result = []
        for rate in self:
            name = rate.name + (rate.operation and (' [' + rate.operation + ']') or '')
            result.append((rate.id, name))
        return result


class HandlingRateCategory(models.Model):
    _name = 'servoo.handling.rate.category'
    _description = 'Handling Rate Category'

    name = fields.Char('Name', required=True)
