# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Transit',
    'version': '1.0',
    'category': 'Transit',
    'author': 'servoo',
    'description': """
    """,
    'depends': ['dyen_base', 'product', 'account'],
    'data': [
        'security/transit_security.xml',
        'security/ir.model.access.csv',
        'data/transit_data.xml',
        'views/transit_order_view.xml',
        'views/transit_menu.xml'
    ],
    'installable': True,
    'auto_install': False,
}