# -*- coding: utf-8 -*-
#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
{
    'name': 'connector_vg7_conai',
    'summary': 'Bidirectional connector to/from VG7 software (CONAI plug-in)',
    'version': '10.0.0.1.13',
    'category': 'Generic Modules',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': [
        'base',
        'sale',
        'account',
        'l10n_it_ddt',
        'l10n_it_conai',
        'connector_vg7',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/conai_view.xml',
        'data/synchro_conai.xml',
        'data/synchro_picking.xml',
        'data/synchro_partner.xml',
        'data/synchro_product.xml',
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
