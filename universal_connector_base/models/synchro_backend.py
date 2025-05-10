#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os
from datetime import datetime, timedelta
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from python_plus import _u

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class SynchroChannel(models.Model):
    """Odoo Backends"""

    _name = "synchro.backend"
    _description = "Odoo Backend"
    _order = "sequence,name"

    def _default_language(self):  # pragma: no cover
        if self.env.user.lang and self.env.user.lang != "en_US":
            lang = self.env.user.lang
        else:
            lang = (
                self.env.context.get("lang")
                or os.environ.get("LANG", "en_US").split(".")[0]
            )
        lang_ids = self.env["res.lang"].search([("code", "=", lang)])
        if lang_ids:
            return lang_ids[0]
        return self.env["res.lang"].search([("code", "=", "en_US")])[0]

    def selection_for_version(self, identity=None):
        res = []
        for identity in self.env["synchro.identity"].search(
            [("id", "=", identity.id)] if identity else []
        ):
            if identity.remote_sw_version:
                res += [(x, "%s %s" % (identity.code, x))
                        for x in eval(identity.remote_sw_version)]
        return res

    def selection_for_prefix(self):
        # WARNING! Before correct follow list, update prefix field
        Partner = self.env["res.partner"]
        res = []
        for identity in self.env["synchro.identity"].search([]):
            prefix = identity.default_prefix
            if not prefix:
                continue
            for name in sorted([x[: -3] for x in Partner._fields.keys()
                                if x.startswith(prefix) and x.endswith("_id")],
                               reverse=True):
                res.append((name, name))
        return res

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
            ("ready", "Ready"),
            ("run", "Data Transfer"),
            ("failed", "Connection failed"),
        ],
        string="State",
        default="draft",
        copy=False,
    )
    prefix = fields.Selection(
        lambda self: self.selection_for_prefix(),
        "Download Prefix",
        required=True,
        help="Download prefix which counterparty must use to identify itself.\n"
        "Format is [a-zA-Z]{2}[a-zA-Z0-9]+\n"
        "Counterparty have to issue this prefix when calls trigger_one_record();"
        "it has to add this prefix in data dictionary when calls synchro()"
        " to issue its internal field name and field value.\n"
        "Prefix activates the right translation functions of Universal Connector."
        "i.e. with prefix='odoo8'\n"
        "<partner_id> means ID of current Odoo database\n"
        "<odoo8:partner_id> means counterpart partner ID and name\n",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    identity_id = fields.Many2one(
        comodel_name="synchro.identity",
        string="Counterpart identity",
        required=True,
        help="Counterpart identity for specific behavior; i.e. 'Odoo', 'Magento'",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    protocol_id = fields.Many2one(
        comodel_name="synchro.protocol",
        string="Send/Receive protocol",
        required=True,
        help="Communication Protocol to load data from/to remote counterparty",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    method = fields.Char(
        related="protocol_id.code",
        string="Send/Receive method",
        store=True,
        readonly=True,
    )
    load_mode = fields.Selection(
        [
            ("direct", "Load referenced records immediately"),
            ("cron", "Load referenced records by cron"),
        ],
        "Referenced records load mode",
        required=True,
        default="direct",
        help=(
            "Every record to load can have fields that refer to another model, i.e"
            " partner has country reference. These record must be loaded from"
            " counterparty in order to set right field values.\n"
            " Load can be executed inside current web session (default) or by cron\n"
            " Direct mode is immediate but is limited by Odoo parameters.\n"
            " Cron mode is delayed and can load all recursive referenced records.\n"
        ),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    deferred_payload = fields.Selection(
        [
            ("0", "Only for test & debug (Very harmful)"),
            ("1", "High priority (May be harmful)"),
            ("2", "Ordinary priority"),
            ("3", "Low priority"),
        ],
        "Deferred payload",
        required=True,
        default="2",
        help=(
            "When load mode 'cron', every cron event can interrupt CPU."
            " This value, by cron interrupts, impacts on CPU execution.\n"
            " Warning! Do not use 'test' payload! May be dangerous!"
        ),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    remote_sw_version = fields.Selection(
        lambda self: self.selection_for_version(),
        "Counterpart software version",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hostname = fields.Char(
        string="Hostname",
        help="Counterpart host name without protocol; may be an IP address",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    lgi_path = fields.Char(
        "RPC login path",
        help="Counterpart login path when load by rpc over https",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    exchange_path = fields.Char(
        "Exchange directory data path",
        help="Counterpart data path when load by rpc over https"
        " or where file will be read and written when load by csv",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    login = fields.Char(
        string="Username / Client id",
        help="Username to login remote counterparty.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    port = fields.Integer(
        string="Communication Port",
        help="Port to communicate with remote counterparty; Odoo uses 8069",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    database = fields.Char(
        string="Database",
        help="Counterpart Database name",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    client_key = fields.Char(
        "Client key",
        help="Client Key assigned by Counterparty",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    password = fields.Char(
        "Counterpart Password",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    counterpart_url = fields.Char(
        "Counterpart login endpoint",
        help="Counterparty URL to connect;\n"
        "format should be [https://][username@]url[:port]/login_path",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    counterpart_data_url = fields.Char(
        "Counterparty data endpoint",
        help="3th Party Sender URL to get data;\n"
        "format should be [https://][username@]url[:port]/exchange_path",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    auto_reconnect = fields.Boolean(
        string="Automatically reconnect to remote counterparty",
        default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    pylib = fields.Char(
        string="PYPI library",
        readonly=True,
        help="Python library used to communicate with remote counterparty",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.user.company_id.id,
        help="Set company, if specific company backend\n"
        "It is required if counterparty does not manage company.",
    )
    default_lang_id = fields.Many2one(
        comodel_name="res.lang",
        string="Counterparty Language",
        required=True,
        default=_default_language,
    )
    update_only_recent = fields.Boolean(
        string="Update Only Recent",
        default=False,
        states={"draft": [("readonly", False)]},
        help="If active, before update, check for last update date",
    )
    last_counterpart_update = fields.Datetime("Last Update", copy=False, readonly=True)
    product_without_variants = fields.Boolean("Products without variants")
    tracelevel = fields.Selection(
        [
            ("0", "No Trace"),
            ("1", "Error (Only error messages)"),
            ("2", "Warning (Main functions)"),
            ("3", "Info (All functions)"),
            ("4", "Debug (Trace all)"),
        ],
        string="Trace Level",
        default="2",
        help="Trace data in log. Warning! Use this feature with caution; "
        "all sent data will be recorded in the log file."
        "This feature can slow data interchange.",
    )
    model_ids = fields.One2many(
        "synchro.model",
        "backend_id",
        string="Model mapping",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    queue_jobs = fields.Html(
        "Queue Jobs",
        compute=lambda self: self._compute_queue_jobs(),
        help="Current Queue Jobs. Value in this field update in time.",
    )
    import_workflow = fields.Integer("Import Workflow", default=0, help="Import status")
    rec_counter = fields.Integer(
        "Import Counter", default=0, help="Last imported record number"
    )
    workflow_model = fields.Char("Current Workflow Model", readonly=True)
    log_ids = fields.One2many(
        "synchro.log",
        "backend_id",
        string="Logs",
    )

    @api.depends("model", "res_id")
    def _compute_queue_jobs(self):  # pragma: no cover
        que_list = self.env["synchro.cache"].get_que_list(self)
        html = "<table>"
        for que_action, que_model, que_spec, que_values, que_ttl, que_ctx in que_list:
            html += "<tr>"
            html += "<td>" + que_action + "</td>"
            html += "<td>" + que_model + "</td>"
            html += "<td>" + (que_spec if que_spec else "") + "</td>"
            html += "<td>" + str(que_values) + "</td>"
            html += "<td>" + str(que_ttl) + "</td>"
            html += "<td>" + str(que_ctx) + "</td>"
            html += "</tr>"
        html += "</table>"

    @api.model
    def _compute_endpoint(
            self, protocol, hostname, port, db, login, passwd, path, with_path=None):
        endpoint_format = (self.protocol_id.endpoint_format
                           or "protocol,login,passwd,hostname,port,path")
        counterpart_url = re.split(
            r"\W", protocol)[-1] if "protocol" in endpoint_format else ""
        if login and "login" in endpoint_format:
            if counterpart_url:
                counterpart_url += "://" + login
            else:
                counterpart_url = login
            if "passwd" in endpoint_format:
                counterpart_url += ":" + passwd
            counterpart_url += "@"
        if hostname and "hostname" in endpoint_format:
            if not counterpart_url.endswith("@"):
                counterpart_url += "://" + hostname
            else:
                counterpart_url += hostname
        if port and "port" in endpoint_format:
            counterpart_url += ":%d" % port
        if path and "path" in endpoint_format:
            counterpart_url = os.path.join(counterpart_url, path)
        if with_path == "data":
            if counterpart_url != self.counterpart_data_url:
                self.counterpart_data_url = counterpart_url
        elif counterpart_url != self.counterpart_url:
            self.counterpart_url = counterpart_url

    @api.onchange("protocol_id")
    def _onchange_protocol_id(self):  # pragma: no cover
        for param in ("lgi_path", "exchange_path", "port"):
            setattr(self, param, self.get_default_from_protocol(param))
        self.pylib = self.protocol_id.pylib
        if self.protocol_id.secure_protocol:
            if self.counterpart_url.startswith("http:"):
                self.counterpart_url = self.counterpart_url.replace("http", "https", 1)
            if self.counterpart_data_url.startswith("http:"):
                self.counterpart_data_url = self.counterpart_data_url.replace(
                    "http", "https", 1
                )
        else:
            if self.counterpart_url.startswith("https:"):
                self.counterpart_url = self.counterpart_url.replace("https", "http", 1)
            if self.counterpart_data_url.startswith("https:"):
                self.counterpart_data_url = self.counterpart_data_url.replace(
                    "https", "http", 1
                )

    @api.onchange("identity_id")
    def _onchange_identity_id(self):  # pragma: no cover
        for param in (
            "login",
            "password",
            "lgi_path",
            "exchange_path",
            "port",
            "prefix",
        ):
            setattr(self, param, self.get_default_from_identity(param))
        return {
            "domain": {
                "remote_sw_version": self.selection_for_version(
                    identity=self.identity_id
                )
            }
        }

    @api.onchange("counterpart_url")
    def _onchange_login_endpoint(self):
        if not self.counterpart_url:  # pragma: no cover
            return
        prot, hostname, port, database, login, passwd, path = self.parse_endpoint(
            with_path="login",
        )
        if hostname and hostname != self.hostname:
            self.hostname = hostname
        if path != self.lgi_path:
            self.lgi_path = path
        if login and login != self.login:
            self.login = login
        if port != self.port:
            self.port = port
        if database and database != self.database:
            self.database = database

    @api.onchange("counterpart_data_url")
    def _onchange_data_endpoint(self):
        if not self.counterpart_data_url:  # pragma: no cover
            return
        prot, hostname, port, database, login, passwd, path = self.parse_endpoint(
            with_path="data",
        )
        if path != self.exchange_path:
            self.exchange_path = path

    @api.onchange("hostname")
    def _onchange_hostname(self):
        if self.protocol_id:
            protocol, hostname, port, db, login, passwd, path = self.parse_endpoint(
                with_path="login"
            )
            self._compute_endpoint(
                protocol, self.hostname, port, db, login, passwd, path)
            prot, hostname, port, database, login, passwd, path = self.parse_endpoint(
                with_path="data"
            )
            self._compute_endpoint(
                protocol, self.hostname, port, db, login, passwd, path,
                with_path="data")

    @api.onchange("login")
    def _onchange_login(self):
        if self.protocol_id:
            protocol, hostname, port, db, login, passwd, path = self.parse_endpoint(
                with_path="login"
            )
            self._compute_endpoint(
                protocol, hostname, port, db, self.login, passwd, path)
            protocol, hostname, port, db, login, passwd, path = self.parse_endpoint(
                with_path="data"
            )
            self._compute_endpoint(
                protocol, hostname, port, db, self.login, passwd, path,
                with_path="data")

    @api.onchange("port")
    def _onchange_port(self):  # pragma: no cover
        if self.protocol_id:
            protocol, hostname, port, db, login, passwd, path = self.parse_endpoint(
                with_path="login"
            )
            self._compute_endpoint(
                protocol, hostname, self.port, db, login, passwd, path)
            protocol, hostname, port, db, login, passwd, path = self.parse_endpoint(
                with_path="data"
            )
            self._compute_endpoint(
                protocol, hostname, self.port, db, login, passwd, path,
                with_path="data")

    def _synchronize_company(self):
        self.ensure_one()
        dir_mapper = self.get_dir_mapper(model="res.company")
        if dir_mapper.counterpart_name:
            session = self.get_session()
            ext_company_ids = self.env["synchro.api"].get_record_list(session,
                                                                      dir_mapper)
            if not ext_company_ids:
                # No company to synchronize
                return
            loc_ext_id = dir_mapper.get_loc_ext_id()
            loc_ext_ids = [
                getattr(company, loc_ext_id)
                for company in self.env["res.company"].search([])
            ]
            while set(loc_ext_ids) - set(ext_company_ids):
                for ext_company_id in sorted(ext_company_ids):
                    if ext_company_id not in loc_ext_ids:
                        break
                self.env["synchro.cache"].que_push(
                    self,
                    "trigger",
                    dir_mapper.counterpart_name,
                    dir_mapper.model_spec,
                    ext_company_id,
                    2,
                    {},
                    prio=2,
                )
                ids = self.synchro_queue()
                if ids:
                    ext_company_ids = list(set(ext_company_ids) - set([ext_company_id]))
                    loc_ext_ids = [x for x in loc_ext_ids if x and x not in ids]
            if set(loc_ext_ids) - set(ext_company_ids):  # pragma: no cover
                self.env["synchro.log"].logmsg(
                    "error",
                    "No company synchronized!",
                    res_rec=self,
                    errcode=-13,
                )
                self.state = "failed"
            elif not self.company_id:
                self.env["synchro.log"].logmsg(
                    "error",
                    "No company assigned to backend!",
                    res_rec=self,
                    errcode=-13,
                )
                self.state = "failed"

    def _build_models_info(self, dir_mappers, dir_mapper, depth=1):
        if depth > 0 and dir_mapper.name:
            struct = self.env[dir_mapper.name].fields_get()
            if dir_mapper not in dir_mappers:
                dir_mappers[dir_mapper] = {"depends": set()}
            for mapper in dir_mapper.field_ids:
                if not mapper.name or struct.get(mapper.name, {}).get("type") in (
                    "one2many",
                    "many2many",
                ):
                    continue
                comodel = struct.get(mapper.name, {}).get("relation")
                if comodel and comodel != dir_mapper.name:
                    dir_mappers[dir_mapper]["depends"].add(comodel)
            for model in dir_mappers[dir_mapper]["depends"]:
                dir_mapper = self.get_dir_mapper(model=model)
                if dir_mapper and dir_mapper not in dir_mappers:
                    dir_mappers = self._build_models_info(
                        dir_mappers,
                        dir_mapper,
                        depth=depth - 1,
                    )
        return dir_mappers

    def _walk_mapper_tree(self, dir_mappers, managed_models, min_seq_valid=99):
        for dir_mapper in dir_mappers.keys():
            dir_mappers[dir_mapper]["sequence"] = (
                len(dir_mappers[dir_mapper]["depends"]) + 3
            )
        return dir_mappers

    def _set_model_priority(self, managed_models):
        dir_mappers = {}
        for dir_mapper in self.model_ids:
            dir_mappers = self._build_models_info(dir_mappers, dir_mapper, depth=99)
        dir_mappers = self._walk_mapper_tree(dir_mappers, managed_models)
        for dir_mapper, item in dir_mappers.items():
            dir_mapper.sequence = {
                "ir.module.module": 2,
                "res.company": 3,
                "res.users": 3,
            }.get(
                dir_mapper.name,
                96 if dir_mapper.name.startswith("ir.") else item["sequence"],
            )

    @api.multi
    def button_check_connection(self):
        """This function applies for remote login using remote API"""
        self.ensure_one()
        session = self.connect()
        if self.env["synchro.api"].session_is_active(session) and self.state == "ready":
            self.env["synchro.log"].logmsg(
                "info",
                "%(model)s.button_check_connection(ep=%(lgi_ep)s,h=%(host)s)",
                res_rec=self,
                backend=self,
            )
            if not self.model_ids:
                self.button_build_model_map(force=True)
            self.assure_technical_models()
            managed_models = set([x.name for x in self.model_ids])
            for dir_mapper in self.model_ids:
                dir_mapper.build_dir_mapper(
                    self,
                    ext_model=dir_mapper.counterpart_name,
                    model=dir_mapper.name,
                    model_spec=dir_mapper.model_spec,
                )
                dir_mapper.analyze_dir_mapper(managed_models)
            self._set_model_priority(managed_models)
            self._synchronize_company()

    @api.multi
    def assure_technical_models(self):
        self.ensure_one()
        # Technical model "ir.model.data" and "ir.module.module" must be present
        found_models = {
            "ir.model.data": False,
            "ir.module.module": False,
            "res.country": False,
            "res.country.state": False,
            "res.currency": False,
            "res.currency.rate": False,
            "res.lang": False,
            "res.groups": False,
            "res.company": False,
            "res.users": False,
        }
        for dir_mapper in self.model_ids:
            if dir_mapper.name in found_models:
                found_models[dir_mapper.name] = True
        for binding_model, found in found_models.items():
            if not found:
                if self.identity_id.code in ("odoo", "openerp"):
                    raise UserError(_("Missed mapping for %s" % binding_model))
                self.env["synchro.model"].build_dir_mapper(
                    self,
                    ext_model=False,
                    model=binding_model,
                    model_spec=False,
                    force=True,
                )

    @api.multi
    def button_reset_to_draft(self):
        self.ensure_one()
        if self.state != "draft":
            self.env["synchro.log"].logmsg(
                "info",
                "%(model)s.button_reset_to_draft(ep=%(lgi_ep)s,h=%(host)s):",
                res_rec=self,
                backend=self,
            )
            self.write({"state": "draft"})

    @api.multi
    def button_build_model_map(self, force=False):
        """Get remote tables of counterparty"""
        self.ensure_one()
        session = self.get_session()
        if self.env["synchro.api"].session_is_active(session) and self.state == "ready":
            model_list = self.env["synchro.api"].get_model_list(session, self)
            for binding_model, remote_model, model_spec in model_list:
                if binding_model and binding_model not in self.env:
                    continue
                if self.identity_id.code not in ("odoo", "openerp"):
                    remote_model = False
                self.env["synchro.model"].build_dir_mapper(
                    self,
                    ext_model=remote_model,
                    model=binding_model,
                    model_spec=model_spec,
                    force=force,
                )

    @api.multi
    def button_rebuild_model_map(self):
        return self.button_rebuild_model_map(force=True)

    def get_loc_ext_id(self):
        return "%s_id" % self.prefix

    def get_default_from_identity(self, param):
        return (
            getattr(self, param)
            or (self.identity_id and getattr(self.identity_id, "default_%s" % param))
            or ""
        )

    def get_default_from_protocol(self, param):
        return (
            self.get_default_from_identity(param)
            or (self.protocol_id and getattr(self.protocol_id, "default_%s" % param))
            or ""
        )

    def parse_endpoint(self, endpoint=None, with_default=True, with_path=None):
        endpoint = endpoint or self.counterpart_url or ""
        protocol = hostname = database = login = password = path = ""
        port = 0
        if self.protocol_id:
            if self.protocol_id.http_protocol:
                protocol = (
                    self.protocol_id.code if self.protocol_id.http_protocol else ""
                )
                if self.protocol_id.secure_protocol:
                    if endpoint.startswith("http:"):
                        endpoint = endpoint.replace("http", "https", 1)
                    if protocol.startswith("http"):
                        protocol = protocol.replace("http", "https", 1)
                else:
                    if endpoint.startswith("https:"):
                        endpoint = endpoint.replace("https", "http", 1)
                    if protocol.startswith("https"):
                        protocol = protocol.replace("https", "http", 1)
            if not endpoint or with_default:
                hostname = self.hostname or "localhost"
                database = self.database or "demo"
                login = self.get_default_from_identity("login")
                password = self.get_default_from_identity("password")
                if with_path == "data":
                    path = self.get_default_from_protocol("exchange_path")
                else:
                    path = self.get_default_from_protocol("lgi_path")
                port = self.get_default_from_protocol("port")
                port = int(port) if port else 0
            if endpoint:
                parts = urlparse(endpoint, scheme=_u(protocol or "https"))
                if parts.hostname:
                    hostname = parts.hostname
                if parts.username:
                    login = parts.username
                if parts.password:
                    password = parts.password
                if parts.path and with_path != "data":
                    path = parts.path
                if parts.port:
                    port = parts.port
                if parts.fragment.startswith("db="):
                    database = parts.fragment.split("=", 1)[1]
        if path and path.startswith("/"):
            path = path[1:]
        if with_path:
            return protocol, hostname, port, database, login, password, path
        return protocol, hostname, port, database, login, password

    def get_session(self):
        if self.state not in ("ready", "run"):  # pragma: no cover
            return False
        return self.env["synchro.api"].get_session(self)

    def connect(self):
        session = self.env["synchro.api"].get_session(self, force_connect=True)
        if self.env["synchro.api"].session_is_active(session):
            self.state = "ready"
        else:  # pragma: no cover
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! Connection to %(model)s failed!",
                res_rec=self,
                errcode=-13,
            )
            self.state = "failed"
        return session

    def counterpart_vals(self, vals):
        self.ensure_one()
        upd_vals = {}
        if "state" not in vals:
            if "protocol_id" in vals:
                pylib = self.env["synchro.protocol"].browse(vals["protocol_id"]).pylib
            else:
                pylib = self.protocol_id.pylib
            if pylib != self.pylib:
                upd_vals["pylib"] = pylib
        return upd_vals

    @api.model
    def vals_with_jacket(self, vals, prefix=None):
        prefix = prefix or self.prefix
        jvals = {}
        for name in vals:
            if name.startswith(prefix + ":"):
                jvals[name] = vals[name]
            elif name.startswith(":"):
                jvals[name[1:]] = vals[name]
            else:
                jvals["%s:%s" % (prefix, name)] = vals[name]
        return jvals

    @api.model
    def assign_backend(self, vals):
        backend = False
        for ext_ref in list(vals.keys()):
            if ":" not in ext_ref:  # pragma: no cover
                continue
            backend = self.search(
                [
                    ("state", "in", ("ready", "run")),
                    ("prefix", "=", ext_ref.split(":", 1)[0]),
                ]
            )
            if backend:
                backend = backend[0]
                break
        if not backend:  # pragma: no cover
            backend = self.search(
                [("state", "in", ("ready", "run"))], order="sequence, id"
            )
            if backend:
                backend = backend[0]
        return backend

    @api.model
    def get_magic_fields(self):
        Partner = self.env["res.partner"]
        magic_fields = []
        for identity in self.env["synchro.identity"].search([]):
            prefix = identity.default_prefix
            if not prefix:
                continue
            for name in sorted(
                    [x for x in Partner._fields.keys()
                     if x.startswith(prefix) and x.endswith("_id")],
                    reverse=True):
                magic_fields.append(name)
        return magic_fields

    def get_dir_mapper(self, model=None, ext_model=None, spec=None):
        DirMapper = self.env["synchro.model"]
        domain = [("backend_id", "=", self.id)]
        if model:
            if ext_model:
                domain.append("|")
                domain.append(("name", "=", False))
            domain.append(("name", "=", model))
        if ext_model:
            if model:
                domain.append("|")
                domain.append(("counterpart_name", "=", False))
            domain.append(("counterpart_name", "=", ext_model))
        if spec is not None:
            domain.append(("model_spec", "=", spec))
        dir_mapper = DirMapper.search(domain)
        return dir_mapper if len(dir_mapper) == 1 else DirMapper

    @api.model
    def synchro_queue(self, prio=None, max_recs=0, mode=None, commit=False):
        local_ids = []
        if mode and mode != self.load_mode:
            return local_ids
        Cache = self.env["synchro.cache"]

        if self.load_mode == "direct":
            max_ctr = 2048
            max_secs = 180
            commit_rate = 1024
        else:  # pragma: no cover
            # Priority is 1..3 or 0 (debug mode)
            prio = prio or int(self.deferred_payload)
            max_ctr, max_secs = {
                0: (1024, 30),
                1: (64, 30),
                2: (32, 20),
                3: (16, 10),
            }[prio]
            commit_rate = max_ctr
            max_ctr = max_recs or max_ctr

        # In order to test module, load_mode is "direct" and deferred_payload="0"
        if self.load_mode == "direct" and self.deferred_payload == "0":
            max_secs = 270
        time_limit = datetime.now() + timedelta(seconds=max_secs)
        loaded_ctr = 0
        cached_model = False
        while max_ctr > 0:
            if datetime.now() > time_limit:
                break
            max_ctr -= 1
            action, model, spec, values, ttl, ctx = Cache.que_pop(self)
            if not action or not model or not values:
                if Cache.que_waiting_len(self):
                    continue
                break
            if not cached_model:
                cached_model = model
            if action == "synchro":
                id = self.env[model].synchro(
                    values,
                    only_minimal=False,
                    ttl=ttl,
                    running_in_queue=True,
                    jacket=True,
                    model_spec=spec,
                    backend=self,
                    ctx=ctx,
                )
            elif action == "trigger":
                id = self.env["ir.model.synchro"].trigger_one_record(
                    model, self.prefix, values, ttl=ttl, running_in_queue=True, ctx=ctx
                )
            elif action == "pull":
                id = self.env["ir.model.synchro"].pull_1_record(
                    model, self.prefix, values, ttl=ttl, running_in_queue=True, ctx=ctx
                )
            else:
                id = -1
            if id > 0:
                loaded_ctr += 1
                if model == cached_model:
                    local_ids.append(id)
        if self.state == "run":
            self.state = "ready"
        if commit or loaded_ctr > commit_rate:
            self.env.cr.commit()  # pylint: disable=invalid-commit
        return local_ids

    @api.model
    def create(self, vals):
        self.env["synchro.cache"].clean_cache()
        backend = super().create(vals)
        upd_vals = backend.counterpart_vals(vals)
        if upd_vals:
            backend.write(upd_vals)
        return backend

    @api.multi
    def write(self, vals):
        self.env["synchro.cache"].clean_cache()
        res = super().write(vals)
        for backend in self:
            upd_vals = backend.counterpart_vals(vals)
            if upd_vals:
                backend.write(upd_vals)
        return res
