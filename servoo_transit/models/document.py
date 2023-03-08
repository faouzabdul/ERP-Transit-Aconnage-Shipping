# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO


from odoo import models, fields, api, _


class DocumentType(models.Model):
    _name = 'servoo.transit.document.type'
    _description = "Document Type"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')


class Document(models.Model):
    _name = 'servoo.transit.document'
    _description = "Document"

    name = fields.Char('Reference', required=True)
    document_type_id = fields.Many2one('servoo.transit.document.type', 'Document type', required=True)
    order_id = fields.Many2one('servoo.transit.order', 'Transit Order')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'servoo_transit_document_attachment_rel',
        'document_id', 'attachment_id',
        string='Attachments')

    @api.model
    def create(self, vals):
        documents = super(Document, self).create(vals)
        for document in documents:
            if document.attachment_ids:
                document.attachment_ids.write({'res_model': self._name, 'res_id': document.id})
        return documents

    def write(self, vals):
        documents = super(Document, self).write(vals)
        for document in self:
            if document.attachment_ids:
                document.attachment_ids.write({'res_model': self._name, 'res_id': formality.id})
        return documents
