# -*- coding: utf-8 -*-
# Copyright 2019 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'connector_vg7',
    'summary': 'Bidirectional connector to/from VG7 software',
    'version': '10.0.0.1.0',
    'category': 'Generic Modules',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': ['base',
                'sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/account_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/account_tax_view.xml',
    ],
    'installable': True,
}
