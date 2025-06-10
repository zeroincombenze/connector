#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "Universal Connector Base",
    "version": "12.0.1.3.16",
    "category": "Generic Modules",
    "summary": "Basic features for Universal Connector",
    "author": "SHS-AV s.r.l.",
    "website": "https://www.zeroincombenze.it/",
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": [
        "base",
        "base_vat",
    ],
    "external_dependencies": {
        "python": [
            "python_plus",
            "odoo_score",
            "clodoo",
            "z0lib",
            "unidecode",
            "Levenshtein",
        ],
    },
    "version_external_dependencies": [
        "clodoo>=2.0.11",
        "python_plus>=2.0.12",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/synchro_protocol.xml",
        "data/synchro_identity.xml",
        "data/synchro_scope.xml",
        "data/synchro_backend.xml",
        "data/synchro_wrap.xml",
        "wizard/wizard_pull_record_view.xml",
        "views/synchro_menu.xml",
        "views/synchro_scope_view.xml",
        "views/synchro_identity_view.xml",
        "views/synchro_protocol_view.xml",
        "views/synchro_backend_view.xml",
        "views/synchro_model_view.xml",
        "views/synchro_log_view.xml",
        "views/country_view.xml",
        "views/currency_view.xml",
        "views/partner_view.xml",
        "views/company_view.xml",
        "views/user_view.xml",
    ],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
