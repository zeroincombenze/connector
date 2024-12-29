#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "Universal Connector: product managemente",
    "version": "12.0.0.3.11",
    "category": "Generic Modules",
    "summary": "Add product models to Universal Connector",
    "author": "SHS-AV s.r.l.",
    "website": "https://www.zeroincombenze.it/",
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": [
        "base",
        "product",
        "stock",
        "universal_connector_base",
    ],
    "external_dependencies": {
        "python": [
            "python_plus",
        ],
    },
    "version_external_dependencies": ["python_plus>=2.0.12"],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
