# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    'name': 'connector_vg7',
    'summary': 'Connector to/from VG7 software',
    'version': '10.0.0.1.27',
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
    'external_dependencies': {
        'python': [
            'python_plus',
            'odoo_score',
            'os0',
            'clodoo',
            'z0lib',
            'unidecode',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_pull_records_view.xml',
        'views/country_view.xml',
        'views/account_account_view.xml',
        'views/partner_view.xml',
        'views/user_view.xml',
        'views/company_view.xml',
        # 'views/currency_view.xml',
        'views/product_view.xml',
        'views/account_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/account_tax_view.xml',
        'views/payment_term_view.xml',
        'views/picking_view.xml',
        'views/partner_bank_view.xml',
        'views/sequence_view.xml',
        'views/synchro_channel_view.xml',
        'views/model_view.xml',
        'data/synchro_channel.xml',
        'data/synchro_partner.xml',
        'data/synchro_partner_bank.xml',
        'data/synchro_country.xml',
        'data/synchro_account.xml',
        'data/synchro_account_invoice.xml',
        'data/synchro_account_tax.xml',
        'data/synchro_sale_order.xml',
        'data/synchro_picking.xml',
        'data/synchro_product.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'development_status': 'Alfa',
}
