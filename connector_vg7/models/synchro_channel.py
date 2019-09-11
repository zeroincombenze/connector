# -*- coding: utf-8 -*-
# Copyright 2016 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class SynchroChannel(models.Model):
    _name = 'synchro.channel'
    _description = "Synchonization Channel"

    name = fields.Char(
        'Sychronization Channel Name',
        required=True,
        help="Give a unique name for Sychronization Channel")
    prefix = fields.Char(
        'Prefix for field names',
        required=True,
        help="Prefix to add to model field name to recognize "
             "counterpart ID.Format must be [a-zA-Z]{2}[a-zA-Z0-9]\n"
             "i.e. with prefix='vg7'\n"
             "<partner_id> means ID in Odoo\n"
             "<vg7_partner_id> means ID in counterpart\n",
        copy=False,
        default='vg7')
    identity = fields.Selection(
        [('generic', 'Generic counterpart'),
         ('odoo', 'Odoo instance'),
         ('vg7', 'VG7 instance'),
         ],
        'Counterpart identity',
        help="May activate some specific functions",
        copy=False,
        default='vg7')
    company_id = fields.Many2one(
        'res.company', 'Company',
        help="Set company, if specific company channel",
        copy=False,
        )
    client_key = fields.Char(
        'Client key',
        help="Client key assigned by 3th Party Sender")
    password = fields.Char('Password', copy=False)
    counterpart_url = fields.Char(
        'Counterpart url',
        help="3th Party Sender URL to connect")
    produtc_without_variants = fields.Boolean('Products without variants')
    sequence = fields.Integer('Priority', default=16)
    active = fields.Boolean(string='Active',
                            default=True)
    trace = fields.Boolean(
        string='Trace',
        default=False,
        help="Trace data in log. Warning! Use this feature with caution; "
             "all sent data will be recorded in the log file."
             "This feature must be used only to debug handshake")
    model_ids = fields.One2many(
        'synchro.channel.model', 'synchro_channel_id',
        string='Model mapping'
    )


class SynchroChannelModel(models.Model):
    _name = 'synchro.channel.model'
    _description = "Model mapping for Synchonization"

    name = fields.Char(
        'Odoo model name',
        required=True,
    )
    field_uname = fields.Text(
        'Field for search with unique name',
        required=True,
    )
    search_keys = fields.Char(
        'Pythonic key search sequence',
        required=True,
        help='Sequence to use in search record when not yet synchronized\n'
             'i.e. (["name","compandy_id"],["name"])\n'
             'will search for record with name and company keys; if not found'
             'search for record just with name'
    )
    counterpart_name = fields.Char('Counterpart model name')
    field_2complete = fields.Char('Model to complete asynchronously')
    sequence = fields.Integer('Priority', default=16)
    synchro_channel_id = fields.Many2one('synchro.channel')
    field_ids = fields.One2many(
        'synchro.channel.model.fields', 'model_id',
        string='Model mapping'
    )


class SynchroChannelModelFields(models.Model):
    _name = 'synchro.channel.model.fields'
    _description = "Field mapping for Synchonization"

    name = fields.Char('Odoo field name')
    counterpart_name = fields.Char('Counterpart field name')
    apply = fields.Char(
        string='Function to apply for supply value or default value.',
        help='Function are in format "name()".\n'
             'Avaiable functions are:\n'
             'vat(), upper(), lower(), street_number(), bool()\n'
             'person(), journal(), account(), uom(), tax()\n',
        default='',
    )
    protect = fields.Selection(
        [('0', 'Updatable'),
         ('1', 'If empty'),
         ('2', 'Protected'),
         ],
        string='Protect field against update',
        default='0',
    )
    model_id = fields.Many2one(
        'synchro.channel.model'
    )


class SynchroChannelDomainTnl(models.Model):
    _name = 'synchro.channel.domain.translation'
    _description = "Field translation for field"

    model = fields.Char('Odoo model name')
    key = fields.Char('Odoo field name')
    odoo_value = fields.Char('Odoo field value')
    ext_value = fields.Char('External field value')
