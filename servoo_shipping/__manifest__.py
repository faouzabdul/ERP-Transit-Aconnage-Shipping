# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Shipping',
    'version': '1.0',
    'author': 'servoo',
    'description': """
    """,
    'depends': ['sale_management','servoo_product', 'dyen_base'],
    'data': [
        'security/shipping_security.xml',
        'security/ir.model.access.csv',
        'wizard/shipping_pda_cancel_views.xml',
        'wizard/wizard_delivery_order_view.xml',
        'wizard/wizard_cancel_shipping_file_view.xml',
        'report/shipping_pda_report_templates.xml',
        'report/shipping_pda_report.xml',
        'report/shipping_delivery_order_report_templates.xml',
        'report/shipping_delivery_order_report.xml',
        'views/shipping_pda_template_view.xml',
        'views/shipping_pda_view.xml',
        'views/shipping_menu.xml',
        'views/shipping_file_view.xml',
        'views/shipping_bl_view.xml',
        'views/shipping_delivery_order_view.xml',
        'data/mail_data_various.xml',
        'data/shipping_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
