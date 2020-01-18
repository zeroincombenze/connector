# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import api, fields, models

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
        help="3th Party Sender URL to connect; may be prefixed by username")
    product_without_variants = fields.Boolean('Products without variants')
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
    model_ids = fields.One2many(
        'synchro.channel.model', 'synchro_channel_id',
        string='Model mapping'
    )

    @api.multi
    def write(self, vals):
        self.env['ir.model.synchro.cache'].clean_cache()
        return super(SynchroChannel, self).write(vals)


class SynchroChannelModel(models.Model):
    _name = 'synchro.channel.model'
    _description = "Model mapping for Synchonization"
    _order = 'sequence, id'

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
    model_spec = fields.Selection(
        [('delivery', 'Delivery Address'),
         ('invoice', 'Invoice Address'),
         ('customer', 'Customer'),
         ('supplier', 'Supplier'),
         ],
        string='Specific search',
    )
    field_2complete = fields.Char('Model to complete asynchronously')
    sequence = fields.Integer('Priority', default=16)
    synchro_channel_id = fields.Many2one('synchro.channel')
    field_ids = fields.One2many(
        'synchro.channel.model.fields', 'model_id',
        string='Model mapping'
    )

    @api.multi
    def write(self, vals):
        self.env['ir.model.synchro.cache'].clean_cache()
        return super(SynchroChannelModel, self).write(vals)


class SynchroChannelModelFields(models.Model):
    _name = 'synchro.channel.model.fields'
    _description = "Field mapping for Synchonization"

    name = fields.Char('Odoo field name')
    counterpart_name = fields.Char('Counterpart field name')
    apply = fields.Char(
        string='Function to apply for supply value or default value.',
        help='Function are in format "name()".\n'
             'Some avaiable functions are:\n'
             'vat(), upper(), lower(), street_number(), bool()\n'
             'person(), journal(), account(), uom(), tax()\n',
        default='',
    )
    spec = fields.Selection(
        [('delivery', 'Delivery Address'),
         ('invoice', 'Invoice Address'),
         ('customer', 'Customer'),
         ('supplier', 'Suplier'),
         ],
        string='Specific search',
    )
    protect = fields.Selection(
        [('0', 'Always Update'),
         ('1', 'But new value not empty'),
         ('2', 'But current value is empty'),
         ('3', 'Protected field'),
         ],
        string='Protect field against update',
        default='0',
    )
    required = fields.Boolean('Required field',
                              default=False)
    model_id = fields.Many2one(
        'synchro.channel.model'
    )

    @api.multi
    def write(self, vals):
        self.env['ir.model.synchro.cache'].clean_cache()
        return super(SynchroChannelModelFields, self).write(vals)


class SynchroChannelDomainTnl(models.Model):
    _name = 'synchro.channel.domain.translation'
    _description = "Field translation for field"

    model = fields.Char('Odoo model name')
    key = fields.Char('Odoo field name')
    odoo_value = fields.Char('Odoo field value')
    ext_value = fields.Char('External field value')
