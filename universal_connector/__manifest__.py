# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "Universal Connector",
    "version": "10.0.0.3.16",
    "category": "Generic Modules",
    "summary": "Universal Connector",
    "author": "SHS-AV s.r.l.",
    "website": "https://www.zeroincombenze.it/",
    "development_status": "Beta",
    "license": "AGPL-3",
    "depends": [
        "account",
        "base",
        "l10n_it_ddt",
        "purchase",
        "sale",
        "stock",
        "stock_picking_package_preparation",
    ],
    "external_dependencies": {
        "python": [
            "python_plus",
            "odoo_score",
            "clodoo",
            "z0lib",
            "unidecode",
            "Levenshtein"
        ]
    },
    "version_external_dependencies": [
        "clodoo>=2.0.16",
        "python_plus>=2.0.18",
        "odoo_score>=2.0.11",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_pull_records_view.xml",
        "views/country_view.xml",
        "views/partner_view.xml",
        "views/product_view.xml",
        "views/stock_view.xml",
        "views/sale_order_view.xml",
        "views/purchase_order_view.xml",
        "views/account_tax_view.xml",
        "views/payment_term_view.xml",
        "views/picking_view.xml",
        "views/partner_bank_view.xml",
        "views/synchro_channel_view.xml",
        "views/model_view.xml",
        "data/synchro_channel.xml",
        "data/synchro_partner.xml",
        "data/synchro_partner_bank.xml",
        "data/synchro_country.xml",
        "data/synchro_account_tax.xml",
        "data/synchro_sale_order.xml",
        "data/synchro_purchase_order.xml",
        "data/synchro_package_preparation.xml",
        "data/synchro_product.xml",
        "data/ir_cron.xml",
    ],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
