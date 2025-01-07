#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "Universal Connector VG7",
    "version": "12.0.0.3.14",
    "category": "Generic Modules",
    "summary": "Add Remote Counterparty VG7 to Universal Connector",
    "author": "SHS-AV s.r.l.",
    "website": "https://www.zeroincombenze.it/crm",
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": [
        "universal_connector_base",
        "universal_connector_by_http",
        "universal_connector_product",
    ],
    "version_depends": ["universal_connector_base>=12.0.0.3.14"],
    "external_dependencies": {
        "python": [
            "python_plus",
        ],
    },
    "version_external_dependencies": ["python_plus>=2.0.12"],
    "data": [
        "data/synchro_identity.xml",
        "data/synchro_backend.xml",
        "data/synchro_partner.xml",
        "data/synchro_country.xml",
        "views/country_view.xml",
    ],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
