#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "Universal Connector Openerp",
    "version": "12.0.1.3.14",
    "category": "Generic Modules",
    "summary": "Manage remote old openerp version",
    "author": "SHS-AV s.r.l.",
    "website": "https://www.zeroincombenze.it/",
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": ["universal_connector_base"],
    "version_depends": ["universal_connector_base>=12.0.1.3.14"],
    "external_dependencies": {
        "python": [
            "python_plus",
        ],
    },
    "version_external_dependencies": ["python_plus>=2.0.12"],
    "data": [
        "data/synchro_identity.xml",
        "data/synchro_backend.xml",
        "views/company_view.xml",
    ],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
