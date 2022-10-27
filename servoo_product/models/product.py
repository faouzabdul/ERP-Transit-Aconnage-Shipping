# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    detailed_type = fields.Selection(selection_add=[
        ('disbursement', 'Disbursement'),
        ('benefit', 'Benefit'),
        ('guarantee', 'Guarantee'),
        ('disbursement_benefit', 'Disbursement + Benefit')
    ], ondelete={
        'disbursement': 'cascade',
        'benefit': 'cascade',
        'guarantee': 'cascade',
        'disbursement_benefit': 'cascade'
    })
    type = fields.Selection(selection_add=[
        ('disbursement', 'Disbursement'),
        ('benefit', 'Benefit'),
        ('guarantee', 'Guarantee'),
        ('disbursement_benefit', 'Disbursement + Benefit')
    ], ondelete={
        'disbursement': 'cascade',
        'benefit': 'cascade',
        'guarantee': 'cascade',
        'disbursement_benefit': 'cascade'
    })


class Product(models.Model):
    _inherit = 'product.product'
    operation_type = fields.Selection([
        ('transit', 'Transit'),
        ('logistic', 'Logistic'),
        ('handling', 'Handling'),
        ('shipping', 'Shipping')
    ], string='Operation')

