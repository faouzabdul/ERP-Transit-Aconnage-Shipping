# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    commercial_register_number = fields.Char('Commercial Register Number')
