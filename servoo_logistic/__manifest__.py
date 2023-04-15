# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Logistic',
    'version': '1.0',
    'category': 'Logistic',
    'author': 'servoo',
    'description': """
    """,
    'depends': ['dyen_base', 'product', 'fleet', 'account'],
    'data': [
        'security/logistic_security.xml',
        'security/ir.model.access.csv',
        'data/logistic_data.xml',
        'wizard/wizard_cancel_logistic_operation_view.xml',
        'views/document_view.xml',
        'views/formality_view.xml',
        'views/operation_view.xml',
        'views/logistic_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}