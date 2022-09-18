# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO


from odoo import models, fields, api, _


class DocumentType(models.Model):
    _name = 'servoo.logistic.document.type'
    _description = "Document Type"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')


class Document(models.Model):
    _name = 'servoo.logistic.document'
    _description = "Document"

    name = fields.Char('Reference', required=True)
    document_type_id = fields.Many2one('servoo.logistic.document.type', 'Document type', required=True)
    operation_id = fields.Many2one('servoo.logistic.operation', 'Operation')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'servoo_logistic_document_attachment_rel',
        'document_id', 'attachment_id',
        string='Attachments')
