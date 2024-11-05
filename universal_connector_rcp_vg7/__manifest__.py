#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "Universal Connector VG7",
    "version": "12.0.0.3.10",
    "category": "Generic Modules",
    "summary": "Add Remote Counterparty VG7 to Universal Connector",
    "author": "SHS-AV s.r.l.",
    "website": "https://www.zeroincombenze.it/",
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": [
        "universal_connector_base",
        "universal_connector_by_http",
        "account",
        "l10n_it_ddt",
        "purchase",
        "sale",
        "stock",
        "stock_picking_package_preparation",
    ],
    "external_dependencies": {
        "python": [
            "python_plus",
        ],
    },
    "version_external_dependencies": ["python_plus>=2.0.12"],
    "data": [
        "data/synchro_channel.xml",
        "data/synchro_partner.xml",
        "data/synchro_account.xml",
        "data/synchro_country.xml",
        "data/synchro_account_invoice.xml",
        "data/synchro_account_tax.xml",
        "data/synchro_package_preparation.xml",
        "data/synchro_partner_bank.xml",
        "data/synchro_product.xml",
        "data/synchro_purchase_order.xml",
        "data/synchro_sale_order.xml",
    ],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
