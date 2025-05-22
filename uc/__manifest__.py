#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    'name': 'universal_connector',
    'summary': 'Odoo universal connector',
    'version': '12.0.1.0.0',
    'category': 'Generic Modules',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'license': 'LGPL-3',
    'depends': [
        "base",
        "connector",
        "connector_base_product",
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
        "data/synchro.connector.protocol.xml",
        "data/synchro.connector.identity.xml",
        "security/connector_odoo_base_security.xml",
        "security/ir.model.access.csv",
        "views/synchro_backend.xml",
        "views/synchro_backend_model.xml",
        "views/odoo_connector_menus.xml",
    ],
    'installable': False,
    'development_status': 'Alpha',
}
