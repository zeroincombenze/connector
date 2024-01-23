# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    'name': 'connector_vg7_client',
    'summary': 'Bidirectional connector to/from VG7 software',
    'version': '8.0.0.1.18',
    'category': 'Generic Modules',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': [
        'base',
        'sale',
        'account',
        'project',
        'stock_picking_package_preparation',
        'l10n_it_ddt',
    ],
    'external_dependencies': {
        'python': [
            'python_plus',
            'os0',
            'unidecode',
        ],
    },
    'data': [
        'data/synchro_channel.xml',
        'views/account_view.xml',
        'views/invoice_view.xml',
        'views/user_view.xml',
        'views/project_view.xml',
        'views/sale_order_view.xml',
        'views/synchro_channel_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'development_status': 'Alfa',
}
