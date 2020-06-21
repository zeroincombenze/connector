# -*- coding: utf-8 -*-
#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
{
    'name': 'connector_vg7_project',
    'summary': 'Bidirectional connector to/from VG7 software (project plug-in)',
    'version': '10.0.0.1.1',
    'category': 'Generic Modules',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': [
        'base',
        'project',
        'connector_vg7',
    ],
    'data': [
        'views/project_view.xml',

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
