# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO


from odoo import models, fields, api, _


class DocumentType(models.Model):
    _name = 'servoo.stevedoring.document.type'
    _description = "Document Type"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')


class Document(models.Model):
    _name = 'servoo.stevedoring.document'
    _description = "Document"

    name = fields.Char('Reference', required=True)
    document_type_id = fields.Many2one('servoo.stevedoring.document.type', 'Document type', required=True)
    file_id = fields.Many2one('servoo.stevedoring.file', 'File')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'servoo_stevedoring_document_attachment_rel',
        'document_id', 'attachment_id',
        string='Attachments')
