# -*- coding: utf-8 -*-
#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
{
    'name': 'connector_vg7',
    'summary': 'Bidirectional connector to/from VG7 software',
    'version': '10.0.0.1.13',
    'category': 'Generic Modules',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': [
        'base',
        'sale',
        'account',
        'stock_picking_package_preparation',
        'l10n_it_ddt',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/country_view.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/account_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/account_tax_view.xml',
        'views/payment_term_view.xml',
        'views/picking_view.xml',
        'views/synchro_channel_view.xml',
        'views/model_view.xml',
        'data/synchro_channel.xml',
        'data/synchro_partner.xml',
        'data/synchro_country.xml',
        'data/synchro_account.xml',
        'data/synchro_account_invoice.xml',
        'data/synchro_account_tax.xml',
        'data/synchro_sale_order.xml',
        'data/synchro_picking.xml',
        'data/synchro_product.xml',
        'data/ir_cron.xml',
    ],
    'external_dependencies': {
        'python': [
            'python_plus',
            'os0',
            'unidecode',
        ],
    },
    'installable': True,
}
