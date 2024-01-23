# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError


class SynchroChannel(models.Model):
    _name = 'synchro.channel'
    _description = "Synchonization Channel"
    _order = 'sequence, id'

    name = fields.Char(
        'Sychronization Channel Name',
        required=True,
        help="Give a unique name for Sychronization Channel")
    prefix = fields.Char(
        'Prefix for field names',
        required=True,
        help="Prefix to add to model field name to recognize "
             "counterpart ID.Format must be [a-zA-Z]{2}[a-zA-Z0-9]+\n"
             "i.e. with prefix='vg7'\n"
             "<partner_id> means ID in Odoo\n"
             "<vg7:partner_id> means counterpart field name and value\n",
        copy=False,
        default='vg7')
    identity = fields.Selection(
        [('generic', 'Generic counterpart'),
         ('odoo', 'Odoo instance'),
         ('vg7', 'VG7 instance'),
         ],
        'Counterpart identity',
        help="This value may activate some specific functions",
        copy=False,
        default='vg7')
    company_id = fields.Many2one(
        'res.company', 'Company',
        help="Set company, if specific company channel",
        copy=False,
        )
    client_key = fields.Char(
        'Client key',
        help="Client key assigned by 3th Party Sender or DB name")
    password = fields.Char('Password', copy=False)
    counterpart_url = fields.Char(
        'Counterpart endpoint',
        help="3th Party Sender URL to connect;\n"
             "format is [username@]url[:port]")
    sequence = fields.Integer('Priority', default=16)
    active = fields.Boolean(string='Active',
                            default=True)
    trace = fields.Boolean(
        string='Trace',
        default=False,
        help="Trace data in log. Warning! Use this feature with caution; "
             "all sent data will be recorded in the log file."
             "This feature must be used only to debug handshake")
    method = fields.Selection(
        [('NO', 'No interchange'),
         ('JSON', 'By JSON (rpc)'),
         ('XML', 'By XML (rpc)'),
         ('PEC', 'By mail PEC'),
         ('FTP', 'By FTP'),
         ('CSV', 'By file CSV'),
        ],
        'Send/Receive method',
        default='JSON',
        help="How data will be sent and received.")
    exchange_path = fields.Char(
        'Exchange directory path',
        help="If method is CSV, path where file will be read and written")
