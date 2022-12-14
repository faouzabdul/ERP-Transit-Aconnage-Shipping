# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Finance',
    'author': 'servoo',
    'version': '1.0',
    'description': """
    """,
    'depends': ['account', 'hr', 'servoo_transit', 'servoo_logistic', 'servoo_stevedoring', 'th_caisse_externe', 'servoo_purchase'],
    'data': [
        'security/servoo_finance_security.xml',
        'security/ir.model.access.csv',
        'data/servoo_finance_data.xml',
        'report/report_payment_request.xml',
        'report/report_cash_voucher.xml',
        'report/report_cashier_piece.xml',
        'wizard/wizard_payment_request_view.xml',
        'wizard/wizard_cash_voucher_view.xml',
        'wizard/wizard_cashier_piece_view.xml',
        'views/payment_request_view.xml',
        'views/payment_operation_file_view.xml',
        'views/cash_voucher_view.xml',
        'views/cashier_piece_view.xml',
        'views/account_move_view.xml',
        'views/servoo_finance_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}
