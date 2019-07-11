# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'connector_vg7',
    'summary': 'Bidirectional connector to/from VG7 software',
    'version': '10.0.0.1.3',
    'category': 'Generic Modules',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': [
        'base',
        'sale',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/country_view.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/account_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/account_tax_view.xml',
        'views/synchro_channel_view.xml',
        'data/synchro_channel.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
}
