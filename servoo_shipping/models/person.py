# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

from odoo import models, fields


class Person(models.Model):
    _name = 'servoo.shipping.person'
    _description = 'Person (crew or passenger)'
    name = fields.Char('Family name', required=True)
    given_names = fields.Char('Given names')
    nationality = fields.Many2one('res.country', 'Nationality')
    date_birth = fields.Date('Date of birth')
    place_birth = fields.Char('Place of birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    identity_document_nature = fields.Many2one('servoo.shipping.identity.document.type', 'Identity document nature')
    identity_document_number = fields.Char('Identity document number')
    identity_document_issue_date = fields.Date('Issue date')
    identity_document_expiry_date = fields.Date('Expiry date')


class IdentityDocumentType(models.Model):
    _name = 'servoo.shipping.identity.document.type'
    _description = 'Identity Document Type'

    name = fields.Char('Name', required=True)