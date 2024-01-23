#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    'name': 'Universal Connector Tests',
    'summary': 'Tests for Universal connector',
    'version': '12.0.1.0.0',
    'author': 'SHS-AV s.r.l.',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'data': [
        "data/synchro.backend.xml",
    ],
    'depends': [
        'universal_connector',
        'universal_connector_protocol_xmlrpc',
        'universal_connector_librerp',
        'universal_connector_powerp',
        'universal_connector_vg7',
        'universal_connector_zeroincombenze',
    ],
    'website': 'https://www.zeroincombenze.it/',
    'installable': True,
}
