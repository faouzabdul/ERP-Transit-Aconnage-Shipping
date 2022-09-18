# -*- coding: utf-8 -*-
# Author: Marius YENKE MBEUYO

{
    'name': 'Dyen fleet',
    'version': '1.0',
    'category': 'Fleet addons',
    'description': 'Addons for standard fleet module',
    'author': 'Dyen',
    'depends': ['fleet'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/fleet_filling_fuel_tank_wizard_views.xml',
        'views/fleet_fuel_tank_views.xml',
        'views/fleet_vehicle_log_fuel_views.xml',
        'data/fleet_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
