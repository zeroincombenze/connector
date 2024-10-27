#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    'name': 'Connector Universal - JSON over http',
    'summary': 'Add protocol JSON over http to Universal Connector',
    'version': '12.0.1.0.0',
    'author': 'SHS-AV s.r.l.',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'data': [
        "data/synchro.connector.protocol.xml",
    ],
    'depends': [
        'universal_connector',
    ],
    'website': 'https://www.zeroincombenze.it/',
    'post_init_hook': 'set_available_protocol_post',
    'installable': True,
}
