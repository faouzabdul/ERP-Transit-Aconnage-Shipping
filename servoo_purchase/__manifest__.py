# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Purchase needs',
    'version': '1.0',
    'author': 'servoo',
    'description': """
    """,
    'depends': ['purchase', 'hr'],
    'data': [
        'security/purchase_security.xml',
        'security/ir.model.access.csv',
        'data/purchase_data.xml',
        'views/purchase_need_view.xml',
        'views/purchase_view.xml',
        'report/purchase_order_templates.xml',
        'report/purchase_reports.xml'
    ],
    'installable': True,
    'auto_install': False,
}