# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO


{
    'name': 'Sales',
    'version': '1.0',
    'author': 'servoo',
    'description': """
    """,
    'depends': ['dyen_base', 'sale_management', 'account'],
    'data': [
        'security/sales_security.xml',
        # 'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/sale_views.xml',
        'views/sale_order_template_views.xml',
        'report/sale_report_templates.xml',
        'report/report_invoice.xml',
        'views/invoice_menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}