# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO


{
    'name': 'Sales',
    'version': '1.0',
    'author': 'servoo',
    'description': """
    """,
    'depends': ['dyen_base', 'sale', 'account'],
    'data': [
        'views/account_move_views.xml',
        'views/sale_views.xml',
        # 'report/custom_header.xml',
        # 'report/custom_footer.xml',
        'report/sale_report_templates.xml',
        'report/report_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
}