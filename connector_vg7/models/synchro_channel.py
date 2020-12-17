# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os
import csv
import requests
import logging
from odoo import api, fields, models
from odoo import release

_logger = logging.getLogger(__name__)
try:
    from clodoo import transodoo
except ImportError as err:
    _logger.error(err)
try:
    import oerplib
except ImportError as err:
    _logger.error(err)
try:
    import odoorpc
except ImportError as err:
    _logger.error(err)

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
    tracelevel = fields.Selection(
        [('0', 'No Trace'),
         ('1', 'Main functions'),
         ('2', 'Main + Inner functions'),
         ('3', 'Statements'),
         ],
        string='Trace Level',
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
    import_workflow = fields.Integer('Import Workflow',
        default=0,
        help='Import status')
    rec_counter = fields.Integer('Import Counter',
        default=0,
        help='Last imported record number')
    workflow_model = fields.Char('Current Workflow Model',
        readonly=True)

    def get_channel_model(self, channel_id, model):
        return self.search([('synchro_channel_id', '=', channel_id),
                            ('name', '=', model)])[0]

    def csv_session(self, endpoint):
        """In CSV: dirname -> session"""
        return False, endpoint

    def vg7_json_session(self, endpoint):
        """In JSON: headers -> cnx, endpoint -> session"""
        headers = {'Authorization': 'access_token %s' % self.client_key}
        return headers, endpoint

    def odoo_rpc_session(self, endpoint):

        def default_params():
            return 'xmlrpc', 8069, 'demo', 'admin', 'admin'

        def parse_endpoint(endpoint):
            protocol, def_port, def_db, def_login, def_pwd = default_params()
            if endpoint:
                if len(endpoint.split('@')) == 2:
                    login = endpoint.split('@')[0]
                    endpoint = endpoint.split('@')[1]
                else:
                    login = self.env.user.login
                if len(endpoint.split(':')) == 2:
                    port = int(endpoint.split(':')[1])
                    endpoint = endpoint.split(':')[0]
                else:
                    port = def_port
            return protocol, port, def_db, login, def_pwd

        def connect_params(endpoint):
            protocol, port, def_db, login, def_pwd = parse_endpoint(endpoint)
            db = self.client_key or def_db
            passwd = self.password or def_pwd
            return protocol, endpoint, port, db, login, passwd

        def rpc_connect(endpoint, protocol, port):
            try:
                if self.method == 'JSON':
                    cnx = odoorpc.ODOO(endpoint,
                                       'jsonrpc',
                                       port)
                elif self.method == 'XML':
                    cnx = oerplib.OERP(server=endpoint,
                                       protocol='xmlrpc',
                                       port=port)
            except BaseException:  # pragma: no cover
                cnx = False
            return cnx

        def rpc_login(cnx, db=None, login=None, passwd=None):
            try:
                session = cnx.login(database=db,
                                    user=login,
                                    passwd=passwd)
            except BaseException:  # pragma: no cover
                session = False
            return cnx, session

        protocol, endpoint, port, db, login, passwd = connect_params(endpoint)
        return rpc_login(
            rpc_connect(endpoint, protocol, port),
            db=db,
            login=login,
            passwd=passwd)

    @api.multi
    def write(self, vals):
        self.env['ir.model.synchro.cache'].clean_cache()
        return super(SynchroChannel, self).write(vals)

    @api.onchange('trace')
    def onchange_trace(self):
        if self.trace:
            self.tracelevel = '2'
        else:
            self.tracelevel = '0'

    @api.onchange('tracelevel')
    def onchange_tracelevel(self):
        # compatobility with old trace flag
        if self.tracelevel == '0':
            self.trace = False
        else:
            self.trace = True


class SynchroChannelModel(models.Model):
    _name = 'synchro.channel.model'
    _description = "Model mapping for Synchonization"
    _order = 'sequence, id'

    name = fields.Char(
        'Odoo model name',
        required=True,
    )
    field_uname = fields.Text(
        'Field for foreign search with unique name',
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
         ('company', 'Company'),
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

    def select_by_domain(self, vals, domain):
        # TODO
        return vals

    def get_csv_response(
            self, cnx, session, ext_id=False, domain=None, mode=None):
        """In CSV session is the dirname"""
        dirname = session
        ext_model = self.counterpart_name
        model = self.name
        file_csv = os.path.expanduser(
            os.path.join(dirname, ext_model + '.csv'))
        self.env['ir.model.synchro'].logmsg('info',
            '>>> %(model)s.get_csv_response(cnx,session,id=%(xid)s,%(csv)s)',
            model=model, ctx={'xid': ext_id, 'csv': file_csv})
        cache = self.env['ir.model.synchro.cache']
        ext_id_name = cache.get_model_attr(
            self.synchro_channel_id.id, model, 'KEY_ID', default='id')
        if not os.path.isfile(file_csv):
            return {} if ext_id else []
        vals = []
        with open(file_csv, 'rb') as fd:
            hdr = False
            reader = csv.DictReader(fd,
                                    fieldnames=[],
                                    restkey='undef_name')
            for line in reader:
                row = line['undef_name']
                if not hdr:
                    row_id = 0
                    hdr = row
                    continue
                row_id += 1
                row_res = {ext_id_name: row_id}
                row_billing = {}
                row_shipping = {}
                row_contact = {}
                for ix, value in enumerate(row):
                    if (isinstance(value, basestring) and
                            value.isdigit() and
                            not value.startswith('0')):
                        value = int(value)
                    elif (isinstance(value, basestring) and
                          value.startswith('[') and
                          value.endswith(']')):
                        value = eval(value)
                    if hdr[ix] == ext_id_name:
                        if not value:
                            continue
                        row_id = value
                    if hdr[ix].startswith('billing_'):
                        row_billing[hdr[ix]] = value
                    elif hdr[ix].startswith('shipping_'):
                        row_shipping[hdr[ix]] = value
                    elif hdr[ix].startswith('contact_'):
                        row_contact[hdr[ix]] = value
                    else:
                        row_res[hdr[ix]] = value
                if row_billing:
                    if model == 'res.partner.invoice':
                        row_res = row_billing
                    else:
                        row_res['billing'] = row_billing
                if row_shipping:
                    if model == 'res.partner.shipping':
                        for nm in ('customer_shipping_id', 'customer_id'):
                            row_shipping[nm] = row_res[nm]
                        row_res = row_shipping
                    else:
                        row_res['shipping'] = row_shipping
                if row_contact:
                    row_res['contact'] = row_contact
                if (ext_id and not mode) and row_res[ext_id_name] != ext_id:
                    continue
                if ext_id:
                    vals = row_res
                    break
                vals.append(row_res)
        return self.select_by_domain(vals, domain)

    def get_vg7_json_response(
            self, cnx, session, ext_id=False, domain=None, mode=None):
        """In JSON cnx contains the headers and session is the endpoint"""
        ext_model = self.counterpart_name
        headers = cnx
        endpoint = session
        if (ext_id and mode) or not ext_id:
            url = os.path.join(endpoint, ext_model)
        else:
            url = os.path.join(endpoint, ext_model, str(ext_id))
        try:
            response = requests.get(url, headers=headers, verify=False)
        except BaseException:
            return getattr(response, 'status_code', 'N/A')
        if response:
            return self.select_by_domain(response.json(), domain)
        return False

    def get_odoo_rpc_response(
            self, cnx, session, ext_id=False, domain=None, mode=None):
        ext_model = self.counterpart_name
        domain = domain or []
        if (ext_id and mode) or not ext_id:
            domain.append((mode, '=', ext_id))
            try:
                vals = cnx.search(ext_model, domain)
            except BaseException:
                vals = []
        else:
            try:
                vals = cnx.browse(ext_model, ext_id)
            except BaseException:
                vals = {}
        return vals

    def get_counterpart_response(self, ext_id=False, domain=None, mode=None):
        """Get data from counterpart
        :param ext_id = counterpart id to read
        :param domain = domain to search for
        :param mode = parent_id field name, if get child records
        """

        def sort_data(datas):
            # Single record
            if not isinstance(datas, (list, tuple)):
                return datas
            ixs = {}
            for item in datas:
                if isinstance(item, dict):
                    id = item.get('id')
                    if not id:
                        return datas
                    ixs[int(id)] = item
            datas = []
            for id in sorted(ixs.keys()):
                datas.append(ixs[id])
            return datas

        cache = self.env['ir.model.synchro.cache']
        cache.open(channel=self.synchro_channel_id, model=self.name)
        if not self.counterpart_name:
            self.env['ir.model.synchro'].logmsg('error',
                'Model %s not managed by external partner!', model=self.name)
            return {}
        channel = self.synchro_channel_id
        if channel.method == 'CSV':
            endpoint = channel.exchange_path
        elif channel.method in ('JSON', 'XML', 'PEC', 'FTP'):
            endpoint = channel.counterpart_url
        else:
            endpoint = False
        if not endpoint:
            self.env['ir.model.synchro'].logmsg('error',
                'Channel %(chid)s without connection parameters!',
                ctx={'chid': channel.id})
            return {}
        cnx = cache.get_attr(channel.id, 'CNX')
        session = cache.get_attr(channel.id, 'SESSION')
        method = channel.method.lower()
        super_method = 'rpc' if channel.method in ('XML', 'JSON') else 'gen'
        if not cnx or not session:
            for fct in (
                    '%s_%s_session' % (channel.identity, method),
                    '%s_session' % method,
                    '%s_%s_session' % (channel.identity, super_method),
                    '%s_session' % super_method,
            ):
                if hasattr(channel, fct):
                    self.env['ir.model.synchro'].logmsg('debug',
                        '>>> %(model)s.%(fct)s(%(ep)s):',
                        model=self.name,
                        ctx={'fct': fct, 'ep': endpoint})
                    cnx, session = getattr(channel, fct)(endpoint)
                    cache.set_attr(channel.id, 'CNX', cnx)
                    cache.set_attr(channel.id, 'SESSION', session)
                    break
        vals = False
        for fct in (
                'get_%s_%s_response' % (channel.identity, method),
                'get_%s_response' % method,
                'get_%s_%s_response' % (channel.identity, super_method),
                'get_%s_response' % super_method,
        ):
            if hasattr(self, fct):
                self.env['ir.model.synchro'].logmsg('debug',
                    '>>> %(model)s.%(fct)s(cnx,session,%(xid)s):',
                    model=self.name,
                    ctx={'fct': fct, 'xid': ext_id})
                vals = getattr(self, fct)(
                    cnx, session, ext_id=ext_id, domain=domain, mode=mode)
                break
        if not isinstance(vals, dict) and not isinstance(vals, (list, tuple)):
            self.env['ir.model.synchro'].logmsg('error',
                'Response error %(sts)s (%(chid)s,%(url)s,%(pfx)s)',
                model=self.name, ctx={
                    'sts': vals,
                    'url': channel.counterpart_url,
                    'pfx': channel.prefix,
                })
            cache.clean_cache(channel_id=channel.id, model=channel.name)
            vals = {} if (ext_id and not mode) else []
        return sort_data(vals)

    def build_odoo_synchro_model(self, channel_id, ext_model, model=None):
        cache = self.env['ir.model.synchro.cache']
        if (cache.get_attr(channel_id, 'IDENTITY') != 'odoo' or
                (ext_model and ext_model.startswith('ir.')) or
                (model and model.startswith('ir.'))):
            return
        ir_synchro_model = self.env['ir.model.synchro']
        ext_odoo_ver = cache.get_attr(channel_id, 'ODOO_FVER')
        if not ext_model and model:
            if self.search([('name', '=', model),
                            ('synchro_channel_id', '=', channel_id)]):
                return
            ext_model = actual_model = model
            if ext_odoo_ver:
                tnldict = ir_synchro_model.get_tnldict(channel_id)
                ext_model = transodoo.translate_from_to(
                    tnldict, 'ir.model', ext_model,
                    ext_odoo_ver, release.major_version,
                    type='model')
                if ext_model == model:
                    ext_model = transodoo.translate_from_to(
                        tnldict, 'ir.model', ext_model,
                        ext_odoo_ver, release.major_version,
                        type='merge')
        else:
            if self.search([('counterpart_name', '=', ext_model),
                            ('synchro_channel_id', '=', channel_id)]):
                return
            actual_model = ext_model
            if ext_odoo_ver:
                tnldict = ir_synchro_model.get_tnldict(channel_id)
                actual_model = transodoo.translate_from_to(
                    tnldict, 'ir.model', ext_model,
                    ext_odoo_ver, release.major_version,
                    type='model')
                if actual_model == ext_model:
                    actual_model = transodoo.translate_from_to(
                        tnldict, 'ir.model', ext_model,
                        ext_odoo_ver, release.major_version,
                        type='model')

        field_uname, skeys = cache.get_default_keys(actual_model)
        vals = {
            'synchro_channel_id': channel_id,
            'name': actual_model,
            'counterpart_name': ext_model,
            'field_uname': field_uname,
            'search_keys': str(skeys),
            'sequence': 16,
        }
        self.create(vals)
        # commit table to avoid another I/O if next operation fails
        self.env.cr.commit()  # pylint: disable=invalid-commit

    @api.multi
    def write(self, vals):
        self.env['ir.model.synchro.cache'].clean_cache()
        return super(SynchroChannelModel, self).write(vals)


class SynchroChannelModelFields(models.Model):
    _name = 'synchro.channel.model.fields'
    _description = "Field mapping for Synchonization"
    _order = 'name'

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
         ('company', 'Company'),
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
