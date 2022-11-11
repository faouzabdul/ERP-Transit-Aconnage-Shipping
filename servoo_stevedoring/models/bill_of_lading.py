# # -*- coding: utf-8 -*-
# # Author: Marius YENKE MBEUYO
#
# from odoo import models, fields, api, _
#
#
# class BillOfLading(models.Model):
#     _inherit = 'servoo.shipping.bl'
#
#     outturn_report_count = fields.Integer(compute="_get_outturn_report", string='Outturns Report')
#
#     def _get_outturn_report(self):
#         outturn_report = self.env['servoo.stevedoring.outturn.report']
#         for record in self:
#             record.outturn_report_count = outturn_report.search_count([('bl_id', '=', record.id)])
