# -*- coding:utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Finance',
    'author': 'servoo',
    'version': '1.0',
    'description': """
    """,
    'depends': ['sale', 'account', 'hr', 'servoo_transit', 'servoo_logistic', 'servoo_stevedoring', 'servoo_purchase'],
    'data': [
        'security/servoo_finance_security.xml',
        'security/ir.model.access.csv',
        'data/servoo_finance_data.xml',
        'report/report_payment_request.xml',
        'report/report_cash_voucher.xml',
        'report/report_cashier_piece.xml',
        'report/report_cash_control.xml',
        'report/report_payment_receipt.xml',
        'wizard/wizard_payment_request_view.xml',
        'wizard/wizard_cash_voucher_view.xml',
        'wizard/wizard_cashier_piece_view.xml',
        'wizard/wizard_cash_control_report_view.xml',
        'wizard/wizard_sale_order_payment_view.xml',
        'wizard/wizard_cash_return_view.xml',
        'wizard/wizard_pda_payment_view.xml',
        'wizard/wizard_account_payment_register_view.xml',
        'views/payment_request_view.xml',
        'views/cash_voucher_view.xml',
        'views/cashier_piece_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/payment_operation_file_view.xml',
        'views/dashboard_views.xml',
        'views/account_cash_control_view.xml',
        'views/servoo_finance_menu.xml',
        'views/account_bank_statement_view.xml',
        'views/sale_order_view.xml',
        'views/shipping_pda_view.xml',
    ],
'assets': {
        'web.assets_backend': [
            'servoo_finance/static/src/scss/style.scss',
            'servoo_finance/static/src/scss/account_asset.scss',
            'servoo_finance/static/lib/bootstrap-toggle-master/css/bootstrap-toggle.min.css',
            'servoo_finance/static/src/js/account_dashboard.js',
            'servoo_finance/static/src/js/account_asset.js',
            'servoo_finance/static/src/js/payment_model.js',
            'servoo_finance/static/src/js/payment_render.js',
            'servoo_finance/static/src/js/payment_matching.js',
            'servoo_finance/static/lib/Chart.bundle.js',
            'servoo_finance/static/lib/Chart.bundle.min.js',
            'servoo_finance/static/lib/Chart.min.js',
            'servoo_finance/static/lib/Chart.js',
            'servoo_finance/static/lib/bootstrap-toggle-master/js/bootstrap-toggle.min.js',

        ],
        'web.assets_qweb': [
            'servoo_finance/static/src/xml/template.xml',
            'servoo_finance/static/src/xml/payment_matching.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
}
