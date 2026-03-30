# -*- coding: utf-8 -*-
#
# Copyright 2019-26 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
    _name = "synchro.channel"
    _description = "Synchonization Channel"
    _order = "sequence, id"

    name = fields.Char(
        "Backend Name",
        required=True,
        help="Give a unique name for Backend",
    )
    sequence = fields.Integer("Priority", default=16)
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("checked", "Checked"),
            ("production", "In Production"),
        ],
        string="State",
        default="draft",
    )

    prefix = fields.Char(
        "Prefix for field names",
        required=True,
        help="Prefix to add to model field name to recognize "
        "counterpart ID.Format must be [a-zA-Z]{2}[a-zA-Z0-9]+\n"
        "i.e. with prefix='vg7'\n"
        "<partner_id> means ID in Odoo\n"
        "<vg7:partner_id> means counterpart field name and value\n",
        copy=False,
        default="vg7",
    )
    identity = fields.Selection(
        [
            ("generic", "Generic counterpart"),
            ("odoo", "Odoo instance"),
            ("vg7", "VG7 instance"),
        ],
        "Counterpart identity",
        help="This value may activate some specific functions",
        copy=False,
        default="vg7",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        help="Set company, if specific company channel",
        copy=False,
    )
    client_key = fields.Char(
        "Client key", help="Client key assigned by 3th Party Sender or DB name"
    )
    password = fields.Char("Password", copy=False)
    counterpart_url = fields.Char(
        "Counterpart endpoint",
        help="3th Party Sender URL to connect;\n" "format is [username@]url[:port]",
    )
    product_without_variants = fields.Boolean("Products without variants")

    tracelevel = fields.Selection(
        [
            ("0", "No Trace"),
            ("1", "Main functions"),
            ("2", "Main + Inner functions"),
            ("3", "Statements"),
            ("4", "All"),
        ],
        string="Trace Level",
        default=False,
        help="Trace data in log. Warning! Use this feature with caution; "
        "all sent data will be recorded in the log file."
        "This feature must be used only to debug handshake",
    )
    method = fields.Selection(
        [
            ("NO", "No interchange"),
            ("JSON", "By JSON (rpc)"),
            ("XML", "By XML (rpc)"),
            ("PEC", "By mail PEC"),
            ("FTP", "By FTP"),
            ("CSV", "By file CSV"),
        ],
        "Send/Receive method",
        default="JSON",
        help="How data will be sent and received.",
    )
    exchange_path = fields.Char(
        "Exchange directory path",
        help="If method is CSV, path where file will be read and written",
    )
    model_ids = fields.One2many(
        "synchro.channel.model", "synchro_channel_id", string="Model mapping"
    )
    import_workflow = fields.Integer("Import Workflow", default=0, help="Import status")
    rec_counter = fields.Integer(
        "Import Counter", default=0, help="Last imported record number"
    )
    workflow_model = fields.Char("Current Workflow Model", readonly=True)
    odoo_version = fields.Selection(
        [
            ("6.1", "Odoo 6.1 - Python2"),
            ("7.0", "Odoo 7.0 - Python2"),
            ("8.0", "Odoo 8.0 - Python2"),
            ("9.0", "Odoo 9.0 - Python2"),
            ("10.0", "Odoo 10.0 - Python2"),
            ("11.0", "Odoo 11.0 - Python3"),
            ("12.0", "Odoo 12.0 - Python3"),
            ("13.0", "Odoo 13.0 - Python3"),
            ("14.0", "Odoo 14.0 - Python3"),
            ("15.0", "Odoo 15.0 - Python3"),
            ("16.0", "Odoo 16.0 - Python3"),
            ("17.0", "Odoo 17.0 - Python3"),
            # ("18.0", "Odoo 18.0 - Python3"),
        ], "External Odoo version"
    )

    @api.multi
    def button_check_connection(self):
        """This function applies for remote login using remote API"""
        self.ensure_one()
        # self.set_env()
        cnx, session = self.connect()
        if cnx and session:
            self.write({"state": "checked"})

    @api.multi
    def button_reset_to_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    def assign_backend(self, vals):
        backend = False
        for ext_ref in vals.keys():
            refs = ext_ref.split(":")
            if len(refs) == 2:
                prefix = refs[0]
                backend = self.search([("prefix", "=", prefix)])
                if backend:
                    backend = backend[0]
                    break
        if not backend:
            cache = self.env["ir.model.synchro.cache"]
            odoo_prio = 999999
            channel_prio = 999999
            odoo_channel = def_channel = channel_from = False
            channel_ctr = 0
            if not cache.get_channel_list():
                cache.setup_channels(all=True)
            for backend in cache.get_channel_list():
                backend_id = backend.id
                if channel_from:
                    break
                channel_ctr += 1
                pfx_ext = "%s:" % cache.get_attr(backend_id, "PREFIX")
                pfx_depr = "%s_" % cache.get_attr(backend_id, "PREFIX")
                if cache.get_attr(backend_id, "PRIO") < channel_prio:
                    def_channel = backend_id
                    channel_prio = cache.get_attr(backend_id, "PRIO", default=16)
                if (
                    cache.get_attr(backend_id, "IDENTITY") == "odoo"
                    and cache.get_attr(backend_id, "PRIO") < odoo_prio
                ):
                    odoo_channel = backend_id
                    odoo_prio = cache.get_attr(backend_id, "PRIO")
                for ext_ref in vals:
                    if ext_ref.startswith(pfx_ext) or ext_ref.startswith(pfx_depr):
                        channel_from = backend_id
                        break
            if not channel_from:
                if channel_prio < odoo_prio:
                    channel_from = def_channel
                else:
                    channel_from = odoo_channel
            if channel_from:
                backend = self.browse(channel_from)
        return backend

    @api.model
    def find_model_channel(self, model_name=None, ext_model=None):
        if model_name:
            domain = [("name", "=", model_name)]
        elif ext_model:
            domain = [("counterpart_name", "=", ext_model)]
        else:
            return None
        if self.id:
            domain.append(("synchro_channel_id", "=", self.id))
        rec = self.env["synchro.channel.model"].search(domain, order="sequence")
        if rec:
            rec = rec[0]
        return rec

    def default_params(self):
        return "xmlrpc", 8069, "demo", "admin", "admin"

    def parse_endpoint(self, endpoint):
        protocol, def_port, def_db, def_login, def_pwd = self.default_params()
        login = def_login
        port = def_port
        if endpoint:
            if len(endpoint.split("@")) == 2:
                login = endpoint.split("@")[0]
                endpoint = endpoint.split("@")[1]
            else:
                login = self.env.user.login
            if len(endpoint.split(":")) == 2:
                port = int(endpoint.split(":")[1])
                endpoint = endpoint.split(":")[0]
        return protocol, endpoint, port, def_db, login, def_pwd

    def connect_params(self):
        endpoint = self.get_endpoint()
        def_prot, endpoint, port, def_db, login, def_pwd = self.parse_endpoint(endpoint)
        db = self.client_key or def_db
        passwd = self.password or def_pwd
        if self.method in ("JSON", "XMl"):
            protocol = "%srpc" % self.method.lower()
        else:
            protocol = def_prot
        return protocol, endpoint, port, db, login, passwd

    def connect(self, ignore_error=None):
        cache = self.env["ir.model.synchro.cache"]
        cnx = cache.get_attr(self.id, "CNX")
        session = cache.get_attr(self.id, "SESSION")
        method = self.method.lower()
        super_method = "rpc" if self.method in ("XML", "JSON") else "gen"
        endpoint = self.get_endpoint()
        if not cnx or not session:
            for fct in (
                "%s_%s_session" % (self.identity, method),
                "%s_session" % method,
                "%s_%s_session" % (self.identity, super_method),
                "%s_session" % super_method,
            ):
                if hasattr(self, fct):
                    self.env["ir.model.synchro"].logmsg(
                        "debug",
                        ">>> %(model)s.%(fct)s(%(ep)s):",
                        model=self.name,
                        ctx={"fct": fct, "ep": endpoint},
                    )
                    cnx, session = getattr(self, fct)()
                    cache.set_attr(self.id, "CNX", cnx)
                    cache.set_attr(self.id, "SESSION", session)
                    break
        return cnx, session

    def get_endpoint(self):
        if self.method == "CSV":
            endpoint = self.exchange_path
        elif self.method in ("JSON", "XML", "PEC", "FTP"):
            endpoint = self.counterpart_url
        else:
            endpoint = False
        return endpoint

    def csv_session(self):
        """In CSV: dirname -> session"""
        endpoint = self.get_endpoint()
        return True if os.path.isdir(endpoint) else False, endpoint

    def vg7_json_session(self):
        """In JSON: headers -> cnx, endpoint -> session"""
        headers = {"Authorization": "access_token %s" % self.client_key}
        endpoint = self.get_endpoint()
        return headers, endpoint

    def odoo_rpc_session(self):

        def rpc_connect(endpoint, protocol, port):
            try:
                if protocol == "jsonrpc":
                    cnx = odoorpc.ODOO(endpoint, protocol, port)
                elif protocol == "xmlrpc":
                    cnx = oerplib.OERP(server=endpoint, protocol=protocol, port=port)
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["ir.model.synchro"].logmsg(
                    "error",
                    "Error %(e)s opening session on %(ep)s",
                    ctx={"e": e, "ep": endpoint},
                )
                cnx = False
            return cnx

        def rpc_login(cnx, protocol=None, db=None, login=None, passwd=None):
            protocol = protocol or "xmlrpc"
            try:
                if protocol == "jsonrpc":
                    cnx.login(db=db, login=login, password=passwd)
                    session = cnx.env.user
                else:
                    session = cnx.login(database=db, user=login, passwd=passwd)
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["ir.model.synchro"].logmsg(
                    "error",
                    "Error %(e)s during login",
                    ctx={"e": e},
                )
                session = False
            return cnx, session

        protocol, endpoint, port, db, login, passwd = self.connect_params()
        return rpc_login(
            rpc_connect(endpoint, protocol, port),
            protocol=protocol,
            db=db,
            login=login,
            passwd=passwd,
        )

    @api.multi
    def write(self, vals):
        # self.env["ir.model.synchro.cache"].clean_cache()
        return super(SynchroChannel, self).write(vals)


class SynchroChannelModel(models.Model):
    _name = "synchro.channel.model"
    _description = "Model mapping for Synchronization"
    _order = "sequence, id"

    name = fields.Char("Odoo model name", required=True)
    field_uname = fields.Text("Field for foreign search with unique name")
    search_keys = fields.Char(
        "Pythonic key search sequence",
        required=True,
        help="Sequence to use in search record when not yet synchronized\n"
        'i.e. (["name","company_id"],["name"])\n'
        "will search for record with name and company keys; if not found"
        "search for record just with name",
    )
    counterpart_name = fields.Char("Counterpart model name")
    model_spec = fields.Selection(
        [
            ("delivery", "Delivery Address"),
            ("invoice", "Invoice Address"),
            ("address", "Generic Address"),
            ("customer", "Customer"),
            ("supplier", "Supplier"),
            ("company", "Company"),
        ],
        string="Specific search domain",
    )
    cron_sync = fields.Char("Model to complete asynchronously",
                            oldname="field_2complete")
    sequence = fields.Integer("Priority", default=16)
    synchro_channel_id = fields.Many2one("synchro.channel")
    field_ids = fields.One2many(
        "synchro.channel.model.fields", "model_id", string="Model mapping"
    )
    rec_counter = fields.Integer(
        "Import Counter", default=0, help="Last imported record number"
    )

    def get_csv_response(self, cnx, session, ext_id=False, domain=None, mode=None):
        """In CSV session is the dirname"""
        dirname = session
        ext_model = self.counterpart_name
        model = self.name
        file_csv = os.path.expanduser(os.path.join(dirname, ext_model + ".csv"))
        self.env["ir.model.synchro"].logmsg(
            "warning",
            "%(model)s.get_csv_response(cnx,session,id=%(xid)s,%(csv)s)",
            model=model,
            ctx={"xid": ext_id, "csv": file_csv},
        )
        cache = self.env["ir.model.synchro.cache"]
        counterpart_pk = cache.get_model_attr(
            self.synchro_channel_id.id, model, "KEY_ID", default="id"
        )
        if not os.path.isfile(file_csv):
            return {} if ext_id else []
        vals = []
        with open(file_csv, "rb") as fd:
            hdr = False
            reader = csv.DictReader(fd, fieldnames=[], restkey="undef_name")
            for line in reader:
                row = line["undef_name"]
                if not hdr:
                    row_id = 0
                    hdr = row
                    continue
                row_id += 1
                row_res = {counterpart_pk: row_id}
                row_billing = {}
                row_shipping = {}
                row_contact = {}
                for ix, value in enumerate(row):
                    if isinstance(value, basestring):
                        if value.isdigit() and not value.startswith("0"):
                            value = int(value)
                        elif value.startswith("[") and value.endswith("]"):
                            value = eval(value)
                        elif value.startswith("{") and value.endswith("}"):
                            value = eval(value)
                        elif value == "False":
                            value = False
                        elif value in ("None", r"\N"):
                            value = None
                    if hdr[ix] == counterpart_pk:
                        if not value:
                            continue
                        row_id = value
                    if hdr[ix].startswith("billing_"):
                        row_billing[hdr[ix]] = value
                    elif hdr[ix].startswith("shipping_"):
                        row_shipping[hdr[ix]] = value
                    elif hdr[ix].startswith("contact_"):
                        row_contact[hdr[ix]] = value
                    elif value is not None:
                        row_res[hdr[ix]] = value
                if row_billing:
                    if model == "res.partner.invoice":
                        row_res = row_billing
                    else:
                        row_res["billing"] = row_billing
                if row_shipping:
                    if model == "res.partner.shipping":
                        for nm in ("customer_shipping_id", "customer_id"):
                            row_shipping[nm] = row_res[nm]
                        row_res = row_shipping
                    else:
                        row_res["shipping"] = row_shipping
                if row_contact:
                    row_res["contact"] = row_contact
                if (ext_id and not mode) and row_res[counterpart_pk] != ext_id:
                    continue
                if ext_id:
                    vals = row_res
                    break
                vals.append(row_res)
        return vals

    def get_vg7_json_response(self, cnx, session, ext_id=False, domain=None, mode=None):
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
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro"].logmsg(
                "error",
                "Error %(e)s in json request",
                ctx={"e": e},
            )
            return getattr(response, "status_code", "N/A")
        if response:
            return response.json()
        return False

    def browse_odoo_rec(self, cnx, ext_model, ext_id, method="json"):
        def expand_many(rec, ext_field, vals):
            try:
                vals[ext_field] = [x.id for x in rec[ext_field]]
            except BaseException:  # pragma: no cover
                if ext_field in vals:
                    del vals[ext_field]
            return vals

        if method == "xml":
            try:
                rec = cnx.browse(ext_model, ext_id)
            except BaseException:  # pragma: no cover
                rec = False
        else:
            Model = cnx.env[ext_model]
            try:
                rec = Model.browse(ext_id)
            except BaseException:  # pragma: no cover
                rec = False
        cache = self.env["ir.model.synchro.cache"]
        actual_model = self.name
        vals = {}
        if rec:
            for ext_field in cache.get_model_attr(
                self.synchro_channel_id.id, ext_model, "EXT_FIELDS"
            ):
                if not hasattr(rec, ext_field):
                    continue
                loc_name = cache.get_model_field_attr(
                    self.synchro_channel_id.id,
                    ext_model,
                    ext_field,
                    "EXT_FIELDS",
                    default=ext_field,
                )
                if loc_name.startswith("."):
                    loc_name = ""
                if not loc_name:
                    continue
                if isinstance(rec[ext_field], (bool, int, long)):
                    vals[ext_field] = rec[ext_field]
                elif (
                    cache.get_struct_model_field_attr(actual_model, loc_name, "ttype")
                    == "many2one"
                ):
                    try:
                        vals[ext_field] = rec[ext_field].id
                    except BaseException:
                        vals[ext_field] = rec[ext_field]
                elif cache.get_struct_model_field_attr(
                    actual_model, loc_name, "ttype"
                ) in ("one2many", "many2many"):
                    vals = expand_many(rec, ext_field, vals)
                elif isinstance(rec[ext_field], basestring):
                    vals[ext_field] = rec[ext_field].encode("utf-8").decode("utf-8")
                else:
                    vals[ext_field] = rec[ext_field]
            if vals:
                vals["id"] = ext_id
        return vals

    def get_odoo_json_response(
            self, cnx, session, ext_id=False, domain=None, mode=None):
        ext_model = self.counterpart_name
        Model = cnx.env[ext_model]
        domain = domain or []
        if ext_id and mode:
            domain.append((mode, "=", ext_id))
        if not ext_id or mode:
            try:
                vals = Model.search(domain)
            except BaseException:  # pragma: no cover
                vals = []
        else:
            vals = self.browse_odoo_rec(cnx, ext_model, ext_id)
        return vals

    def get_odoo_xml_response(self, cnx, session, ext_id=False, domain=None, mode=None):
        ext_model = self.counterpart_name
        domain = domain or []
        if ext_id and mode:
            domain.append((mode, "=", ext_id))
        if not ext_id or mode:
            try:
                vals = cnx.search(ext_model, domain)
            except BaseException:  # pragma: no cover
                vals = []
        else:
            vals = self.browse_odoo_rec(cnx, ext_model, ext_id, method="xml")
        return vals

    def get_counterpart_response(self, ext_id=False, domain=None, mode=None):
        """Get data from counterpart
        :param ext_id = counterpart id to read
        :param domain = domain to search for
        :param mode = parent_id field name, if get child records
        """

        def sort_data(datas):
            if not isinstance(datas, (list, tuple)):
                # Single record
                return datas
            ixs = {}
            for item in datas:
                if isinstance(item, dict):
                    id = item.get("id")
                    if not id:
                        return datas
                    ixs[int(id)] = item
                elif not isinstance(item, (int, long)):
                    return datas
                    break
            if not ixs:
                return sorted(datas)
            datas = []
            for id in sorted(ixs.keys()):
                datas.append(ixs[id])
            return datas

        Cache = self.env["ir.model.synchro.cache"]
        Cache.open(backend=self.synchro_channel_id, model=self.name)
        if not self.counterpart_name:
            return {}
        channel = self.synchro_channel_id
        endpoint = channel.get_endpoint()
        if not endpoint:
            self.env["ir.model.synchro"].logmsg(
                "error",
                "Channel %(chid)s without connection parameters!",
                ctx={"chid": channel.id},
            )
            return {}
        cnx = Cache.get_attr(channel.id, "CNX")
        session = Cache.get_attr(channel.id, "SESSION")
        method = channel.method.lower()
        super_method = "rpc" if channel.method in ("XML", "JSON") else "gen"
        if not cnx or not session:
            for fct in (
                "%s_%s_session" % (channel.identity, method),
                "%s_session" % method,
                "%s_%s_session" % (channel.identity, super_method),
                "%s_session" % super_method,
            ):
                if hasattr(channel, fct):
                    self.env["ir.model.synchro"].logmsg(
                        "debug",
                        ">>> %(model)s.%(fct)s(%(ep)s):",
                        model=self.name,
                        ctx={"fct": fct, "ep": endpoint},
                    )
                    cnx, session = getattr(channel, fct)()
                    Cache.set_attr(channel.id, "CNX", cnx)
                    Cache.set_attr(channel.id, "SESSION", session)
                    break
        vals = False
        for fct in (
            "get_%s_%s_response" % (channel.identity, method),
            "get_%s_response" % method,
            "get_%s_%s_response" % (channel.identity, super_method),
            "get_%s_response" % super_method,
        ):
            if hasattr(self, fct):
                self.env["ir.model.synchro"].logmsg(
                    "debug",
                    ">>> %(model)s.%(fct)s(cnx,session,%(xid)s):",
                    model=self.name,
                    ctx={"fct": fct, "xid": ext_id},
                )
                vals = getattr(self, fct)(
                    cnx, session, ext_id=ext_id, domain=domain, mode=mode
                )
                break

        if isinstance(vals, dict):
            for name in vals.copy().keys():
                if vals[name] is None:
                    del vals[name]
            if vals.keys() == ["id"]:
                vals = {}
        elif isinstance(vals, (list, tuple)):
            vals_list = vals
            new_vals = []
            for vals in vals_list:
                for name in vals.copy().keys():
                    if vals[name] is None:
                        del vals[name]
                if vals.keys() == ["id"]:
                    vals = {}
                if vals:
                    new_vals.append(vals)
            vals = new_vals

        if not isinstance(vals, dict) and not isinstance(vals, (list, tuple)):
            self.env["ir.model.synchro"].logmsg(
                "error",
                "Response error %(sts)s (%(chid)s,%(url)s,%(pfx)s)",
                model=self.name,
                ctx={
                    "sts": vals,
                    "url": channel.counterpart_url,
                    "pfx": channel.prefix,
                },
            )
            Cache.clean_cache(backend_id=channel.id, model=channel.name)
            vals = {} if (ext_id and not mode) else []
        return sort_data(vals)

    def build_odoo_synchro_model(self, backend_id, ext_model, model=None):
        cache = self.env["ir.model.synchro.cache"]
        if (
            cache.get_attr(backend_id, "IDENTITY") != "odoo"
            or (ext_model and ext_model.startswith("ir.")
                and ext_model != "ir.module.module")
            or (model and model.startswith("ir.") and model != "ir.module.module")
        ):
            return False
        ir_synchro_model = self.env["ir.model.synchro"]
        ext_odoo_ver = cache.get_attr(backend_id, "ODOO_FVER")
        if not ext_model and model:
            if self.search(
                [("name", "=", model), ("synchro_channel_id", "=", backend_id)]
            ):
                return True
            ext_model = actual_model = model
            if ext_odoo_ver:
                tnldict = ir_synchro_model.get_tnldict(backend_id)
                ext_model = transodoo.translate_from_to(
                    tnldict,
                    "ir.model",
                    ext_model,
                    ext_odoo_ver,
                    release.major_version,
                    type="model",
                )
                if ext_model == model:
                    ext_model = transodoo.translate_from_to(
                        tnldict,
                        "ir.model",
                        ext_model,
                        ext_odoo_ver,
                        release.major_version,
                        type="merge",
                    )
        else:
            if self.search(
                [
                    ("counterpart_name", "=", ext_model),
                    ("synchro_channel_id", "=", backend_id),
                ]
            ):
                return True
            actual_model = ext_model
            if ext_odoo_ver:
                tnldict = ir_synchro_model.get_tnldict(backend_id)
                actual_model = transodoo.translate_from_to(
                    tnldict,
                    "ir.model",
                    ext_model,
                    ext_odoo_ver,
                    release.major_version,
                    type="model",
                )
                if actual_model == ext_model:
                    actual_model = transodoo.translate_from_to(
                        tnldict,
                        "ir.model",
                        ext_model,
                        ext_odoo_ver,
                        release.major_version,
                        type="model",
                    )

        field_uname, skeys = cache.get_default_keys(actual_model)
        if field_uname and skeys:
            vals = {
                "synchro_channel_id": backend_id,
                "name": actual_model,
                "counterpart_name": ext_model,
                "field_uname": field_uname,
                "search_keys": str(skeys),
                "sequence": 16,
            }
            try:
                self.create(vals)
                # commit table to avoid another I/O if next operation fails
                self.env.cr.commit()  # pylint: disable=invalid-commit
                return True
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["ir.model.synchro"].logmsg(
                    "warning",
                    "Error %(e) creating %(model)s",
                    model=self.__name__,
                    ctx={"e": e},
                )
        else:
            cache.set_unmanageable(actual_model)
        return False

    @api.multi
    def write(self, vals):
        # self.env["ir.model.synchro.cache"].clean_cache()
        return super(SynchroChannelModel, self).write(vals)


class SynchroChannelModelFields(models.Model):
    _name = "synchro.channel.model.fields"
    _description = "Field mapping for Synchonization"
    _order = "name"

    name = fields.Char("Odoo field name")
    counterpart_name = fields.Char("Counterpart field name")
    apply = fields.Char(
        string="Function to apply for supply value or default value.",
        help='Function are in format "name()".\n'
        "Some avaiable functions are:\n"
        "vat(), upper(), lower(), street_number(), bool()\n"
        "person(), journal(), account(), uom(), tax()\n",
        default="",
    )
    spec = fields.Selection(
        [
            ("delivery", "Delivery Address"),
            ("invoice", "Invoice Address"),
            ("customer", "Customer"),
            ("supplier", "Suplier"),
            ("company", "Company"),
        ],
        string="Specific search",
    )
    protect_update = fields.Selection(
        [
            ("0", "Always Update"),
            ("1", "But new value not empty"),
            ("2", "But current value is empty"),
            ("3", "Protected field"),
            ("4", "Max counter"),
        ],
        string="Protect field against update",
        default="0",
    )
    required = fields.Boolean("Required field", default=False)
    model_id = fields.Many2one("synchro.channel.model")

    @api.multi
    def write(self, vals):
        # self.env["ir.model.synchro.cache"].clean_cache()
        return super(SynchroChannelModelFields, self).write(vals)


class SynchroChannelDomainTnl(models.Model):
    _name = "synchro.channel.domain.translation"
    _description = "Field translation for field"

    model = fields.Char("Odoo model name")
    key = fields.Char("Odoo field name")
    odoo_value = fields.Char("Odoo field value")
    ext_value = fields.Char("External field value")
