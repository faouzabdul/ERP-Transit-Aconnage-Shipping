# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Stevedoring',
    'version': '1.0',
    'author': 'servoo',
    'description': """
    """,
    'depends': ['servoo_shipping'],
    'data': [
        'security/stevedoring_security.xml',
        'security/ir.model.access.csv',
        'data/stevedoring_data.xml',
        'report/stevedoring_outturn_report.xml',
        'report/stevedoring_mate_receipt.xml',
        'report/stevedoring_shift_report.xml',
        'wizard/wizard_outturn_report_view.xml',
        'wizard/wizard_mate_receipt_view.xml',
        'wizard/wizard_cancel_stevedoring_file_view.xml',
        # 'views/shipping_bl_view.xml',
        'views/shipping_file_view.xml',
        'views/operation_view.xml',
        'views/document_view.xml',
        'views/formality_view.xml',
        'views/outturn_report_view.xml',
        'views/mate_receipt_view.xml',
        'views/customs_declaration_view.xml',
        'views/stevedoring_menu.xml',
        'views/stevedoring_file_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}