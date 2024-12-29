#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import os

import logging
import re

from datetime import datetime, timedelta
from odoo import api, fields, models
from python_plus import _u

_logger = logging.getLogger(__name__)

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class SynchroChannel(models.Model):
    """Odoo Backends"""

    _name = "synchro.channel"
    _description = "Odoo Backend"
    _order = "sequence,name"

    def _default_hostname(self):
        return self.parse_endpoint(with_default=True)[1]

    def _default_login(self):
        return self.parse_endpoint(with_default=True)[4]

    def _default_port(self):
        return self.parse_endpoint(with_default=True)[2]

    def _default_database(self):
        return self.parse_endpoint(with_default=True)[3]

    def _default_path(self):
        return self.parse_endpoint(with_default=True, with_path="login")[6]

    def _default_exchange_path(self):
        return self.parse_endpoint(with_default=True, with_path="data")[6]

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

    def _remote_sw_selection(self):
        # if self.identity == "odoo":
        return [
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
            ("18.0", "Odoo 18.0 - Python3"),
        ]

    def selection_for_prefix(self):
        # WARNING! Before correct follow list, update prefix field
        return [
            ("oe16", "oe16"),
            ("oe12", "oe12"),
            ("oe10", "oe10"),
            ("oe8", "oe8"),
            ("oe7", "oe7"),
        ]

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
            ("run", "Data downloading/uploading"),
            ("failed", "Connection failed"),
        ],
        string="State",
        default="draft",
        copy=False,
    )
    prefix = fields.Selection(
        [
            ("oe16", "oe16"),
            ("oe12", "oe12"),
            ("oe10", "oe10"),
            ("oe8", "oe8"),
            ("oe7", "oe7"),
        ],
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
    identity = fields.Selection(
        [
            ("generic", "Generic counterparty"),
            ("odoo", "Odoo instance"),
        ],
        "Counterpart identity",
        required=True,
        default="odoo",
        help="Counterpart identity for specific behavior; i.e. 'Odoo', 'Magento'",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    method = fields.Selection(
        [
            ("xmlrpc/https", "By xmlrpc over https"),
            ("xmlrpc/http", "By xmlrpc over http"),
        ],
        "Send/Receive protocol",
        required=True,
        default="xmlrpc/https",
        help="Communication Protocol to load data from/to remote counterparty",
        readonly=True,
        states={"draft": [("readonly", False)]},
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
    odoo_version = fields.Selection(
        _remote_sw_selection,
        "Counterpart software version",
        default="8.0",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    hostname = fields.Char(
        string="Hostname",
        help="Counterpart host name without protocol; may be an IP address",
        default=_default_hostname,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    lgi_path = fields.Char(
        "RPC login path",
        help="Counterpart login path when load by rpc over https",
        default=_default_path,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    exchange_path = fields.Char(
        "Exchange directory data path",
        help="Counterpart data path when load by rpc over https"
        " or where file will be read and written when load by csv",
        default=_default_exchange_path,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    login = fields.Char(
        string="Username / Client id",
        help="Username to login remote counterparty.",
        default=_default_login,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    port = fields.Integer(
        string="Communication Port",
        default=_default_port,
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
    pypi_sign = fields.Char(
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
        "synchro.channel.model",
        "synchro_channel_id",
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
        "ir.model.synchro.log",
        "backend_id",
        string="Logs",
    )

    @api.depends("model", "res_id")
    def _compute_queue_jobs(self):  # pragma: no cover
        que_list = self.env["ir.model.synchro.cache"].get_que_list(self)
        html = "<table>"
        for que_action, que_model, que_values, que_ttl, que_ctx in que_list:
            html += "<tr>"
            html += "<td>" + que_action + "</td>"
            html += "<td>" + que_model + "</td>"
            html += "<td>" + str(que_values) + "</td>"
            html += "<td>" + str(que_ttl) + "</td>"
            html += "<td>" + str(que_ctx) + "</td>"
            html += "</tr>"
        html += "</table>"

    @api.model
    def _compute_counterpart_url(self):
        countepart_url = self.get_login_endpoint(with_port=True, rebuild=True)
        if countepart_url != self.counterpart_url:
            self.counterpart_url = countepart_url

    @api.onchange("method")
    def _onchange_method(self):
        prot = self.get_protocol_from_method(self.method)
        if prot == "http" and self.counterpart_url:
            if self.counterpart_url.startswith("https:"):
                self.counterpart_url = self.counterpart_url.replace("https", "http", 1)
            if self.counterpart_data_url.startswith("https:"):
                self.counterpart_data_url = self.counterpart_data_url.replace(
                    "https", "http", 1
                )
        elif prot == "https" and self.counterpart_url:
            if self.counterpart_url.startswith("http:"):
                self.counterpart_url = self.counterpart_url.replace("http", "https", 1)
            if self.counterpart_data_url.startswith("http:"):
                self.counterpart_data_url = self.counterpart_data_url.replace(
                    "http", "https", 1
                )
        self.init_backend()
        # 10.0 bugfix
        if hasattr(self, "_origin") and self._origin and self._origin.id:
            self.env["ir.model.synchro.cache"].set_attr(
                self._origin.id, "PYPI", self.pypi_sign
            )

    @api.onchange("counterpart_url")
    def _onchange_login_endpoint(self):
        self.init_backend()
        if not self.counterpart_url:
            return
        prot, hostname, port, database, login, passwd, path = self.parse_endpoint(
            with_path="login",
        )
        if prot:
            method = self.get_method_from_protocol(prot)
            if method and method != self.method:
                self.method = method
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
        self.counterpart_data_url = self.get_login_endpoint(
            with_port=True, rebuild=True
        )

    @api.multi
    @api.depends("counterpart_url")
    def _update_login_endpoint(self):  # pragma: no cover
        for backend in self:
            backend._onchange_login_endpoint()

    @api.onchange("hostname")
    def _onchange_hostname(self):
        if self.hostname:
            self._compute_counterpart_url()

    @api.multi
    @api.depends("hostname")
    def _update_hostname(self):  # pragma: no cover
        for backend in self:
            backend._onchange_hostname()

    @api.onchange("login")
    def _onchange_login(self):
        if self.login:
            self._compute_counterpart_url()

    @api.multi
    @api.depends("login")
    def _update_login(self):
        for backend in self:  # pragma: no cover
            backend._onchange_login()

    @api.onchange("port")
    def _onchange_port(self):
        if self.port:
            self._compute_counterpart_url()

    @api.multi
    @api.depends("port")
    def _update_port(self):
        for backend in self:  # pragma: no cover
            backend._onchange_port()

    @api.onchange("odoo_version")
    def _onchange_odoo_version(self):
        if self.odoo_version:
            Api = self.env["synchro.api"]
            login_path, exchange_path = Api.get_default_paths(self)
            if login_path:
                self.lgi_path = login_path
            if exchange_path:
                self.exchange_path = exchange_path
            self._compute_counterpart_url()
            major_version = int(self.odoo_version.split(".")[0])
            candidate = ""
            prefetch = "oe%d" % major_version
            for v, n in self.selection_for_prefix():
                if prefetch == v:
                    candidate = v
                    break
                elif (
                    not candidate and v.startswith("oe") and int(v[2:]) < major_version
                ):
                    candidate = v
            if candidate:
                self.prefix = candidate
            else:
                self.prefix = v

    @api.multi
    @api.depends("odoo_version")
    def _update_odoo_version(self):
        for backend in self:  # pragma: no cover
            backend._onchange_odoo_version()

    def _build_all_indexes(self, cls):
        """Build unique index on table to <gamma>_id for performance"""
        for prefix, _x in self.selection_for_prefix():
            if not hasattr(cls, prefix):
                continue
            table = cls._name.replace(".", "_")
            index_name = "%s_unique_%s" % (table, prefix)
            self._cr.execute(
                "SELECT indexname FROM pg_indexes WHERE indexname = '%s'" % index_name
            )  # pylint: disable=E8103
            if not self._cr.fetchone():
                self._cr.execute(
                    "CREATE UNIQUE INDEX %s on %s (%s_id) "
                    "where %s_id<>0 and %s_id is not null"
                    % (index_name, table, prefix, prefix, prefix)
                )  # pylint: disable=E8103
            self._cr.execute(
                "UPDATE %s set %s_id=NULL where %s_id=0" % (table, prefix, prefix)
            )  # pylint: disable=E8103

    def _synchronize_company(self):
        self.ensure_one()
        dir_mapper = self.get_dir_mapper(model="res.company")
        if dir_mapper.counterpart_name:
            session = self.get_session()
            company_ids = self.env["synchro.api"].get_record_list(session, dir_mapper)
            synchronized = False if len(company_ids) else True
            for company_id in company_ids:
                self.env["ir.model.synchro.cache"].que_push(
                    self,
                    "trigger",
                    dir_mapper.counterpart_name,
                    company_id,
                    2,
                    {},
                    prio=2,
                )
            self.synchro_queue()
            loc_ext_id = dir_mapper.get_loc_ext_id()
            for company in self.env["res.company"].search([]):
                if getattr(company, loc_ext_id) in company_ids:
                    synchronized = True
                    break
            if not synchronized:
                self.env["ir.model.synchro.log"].logmsg(
                    "error",
                    "No company synchronized!",
                    res_model=self._name,
                    id=self.id,
                    errcode=-13,
                )
                self.state = "failed"
        elif not self.company_id:
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "No company assigned to backend!",
                res_model=self._name,
                id=self.id,
                errcode=-13,
            )
            self.state = "failed"

    def _build_models_info(self, dir_mappers, dir_mapper, depth=1):
        if depth > 0 and dir_mapper.name:
            struct = self.env[dir_mapper.name].fields_get()
            if dir_mapper not in dir_mappers:
                dir_mappers[dir_mapper] = {"depends": set()}
            for mapper in dir_mapper.field_ids:
                if not mapper.name or struct[mapper.name]["type"] in (
                    "one2many",
                    "many2many",
                ):
                    continue
                comodel = struct[mapper.name].get("relation")
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
            self.env["ir.model.synchro.log"].logmsg(
                "info",
                "%(model)s[%(id)s].button_check_connection(ep=%(lgi_ep)s,h=%(host)s):",
                res_rec=self,
                backend=self,
            )
            if self.identity == "odoo" and not self.model_ids:
                self.button_build_model_map()
            managed_models = set([x.name for x in self.model_ids])
            for dir_mapper in self.model_ids:
                if self.identity != "odoo":
                    dir_mapper.complete_dir_mapper(
                        self, dir_mapper.counterpart_name, model=dir_mapper.name
                    )
                dir_mapper.analyze_dir_mapper(managed_models)
            self._set_model_priority(managed_models)
            self._synchronize_company()

    @api.multi
    def button_reset_to_draft(self):
        self.ensure_one()
        if self.state != "draft":
            self.env["ir.model.synchro.log"].logmsg(
                "info",
                "%(model)s[%(id)s].button_reset_to_draft(ep=%(lgi_ep)s,h=%(host)s):",
                res_rec=self,
                backend=self,
            )
            self.write({"state": "draft"})

    @api.multi
    def button_build_model_map(self):
        """Get remote tables of counterparty"""
        self.ensure_one()
        session = self.get_session()
        if self.env["synchro.api"].session_is_active(session) and self.state == "ready":
            model_list = self.env["synchro.api"].get_model_list(session, self)
            for binding_model, remote_model in model_list:
                if binding_model and binding_model not in self.env:
                    continue
                if self.identity == "odoo":
                    self.env["synchro.channel.model"].build_odoo_dir_mapper(
                        self, remote_model, model=binding_model
                    )
                else:
                    self.env["synchro.channel.model"].complete_dir_mapper(
                        self, remote_model, model=binding_model
                    )

    def get_loc_ext_id(self):
        return "%s_id" % self.prefix

    def get_method_from_protocol(self, prot):
        return {
            "https": "xmlrpc/https",
            "http": "xmlrpc/http",
        }.get(prot) or False

    def get_protocol_from_method(self, method):
        if method:
            return {
                "xmlrpc/https": method.split("/")[1],
                "xmlrpc/http": method.split("/")[1],
            }.get(method) or False
        return method

    @api.model
    def get_login_endpoint(self, with_port=None, rebuild=False):
        return self.env["synchro.api"].get_login_endpoint(
            self, with_port=with_port, rebuild=rebuild
        )

    @api.model
    def get_data_endpoint(self, exchange_path=None):
        return self.env["synchro.api"].get_data_endpoint(
            self, exchange_path=exchange_path
        )

    def extract_protocol(self, parts):
        return parts.scheme if parts.scheme in ("http", "https") else False

    def parse_endpoint(self, endpoint=None, with_default=True, with_path=None):
        Api = self.env["synchro.api"]
        _x = port = def_port = database = def_db = login = def_login = False
        password = def_pwd = path = hostname = False
        endpoint = endpoint or self.counterpart_url
        # method = self.method or "xmlrpc/https"
        protocol = "https"
        if endpoint:
            if not re.match(r"(\w+:)?//", endpoint):
                endpoint = "https://" + endpoint
            parts = urlparse(endpoint, scheme=_u("https"))
            protocol = self.extract_protocol(parts) or "https"
            if with_default:
                _x, def_port, def_db, def_login, def_pwd, login_path, exchange_path = (
                    Api.get_default(self)
                )
                hostname = self.hostname or "localhost"
                database = self.database or def_db
                login = self.login or def_login
                password = self.password or def_pwd
                if with_path == "data":
                    path = self.exchange_path or exchange_path
                else:
                    path = self.lgi_path or login_path
                port = self.port or def_port
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
        elif with_default:
            if not hostname:
                hostname = "localhost"
            _x, port, database, login, password, path, exchange_path = Api.get_default(
                self
            )
            if with_path == "data":
                path = exchange_path
        if with_path:
            return protocol, hostname, port, database, login, password, path
        return protocol, hostname, port, database, login, password

    @api.multi
    def init_backend(self):
        Api = self.env["synchro.api"]
        for backend in self:
            if not backend.pypi_sign:
                backend.pypi_sign = Api.get_pypi_name(backend)

    def get_session(self):
        if self.state not in ("ready", "run"):  # pragma: no cover
            return False
        return self.env["synchro.api"].get_session(self)

    def connect(self):
        session = self.env["synchro.api"].get_session(self, force_connect=True)
        if self.env["synchro.api"].session_is_active(session):
            self.state = "ready"
        else:  # pragma: no cover
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! Connection to %(model)s[%(id)s] failed!",
                res_model=self._name,
                id=self.id,
                errcode=-13,
            )
            self.state = "failed"
        return session

    def counterpart_vals(self, vals):
        self.ensure_one()
        upd_vals = {}
        if "state" not in vals:
            if (
                "hostname" in vals
                or "login" in vals
                or "port" in vals
                or "lgi_path" in vals
                or "exchange_path" in vals
            ):
                if "counterpart_url" not in vals:
                    counterpart_url = self.get_login_endpoint(with_port=True)
                    if counterpart_url != self.counterpart_url:
                        upd_vals["counterpart_url"] = counterpart_url
                if "counterpart_data_url" not in vals:
                    counterpart_data_url = self.get_data_endpoint()
                    if counterpart_data_url != self.counterpart_data_url:
                        upd_vals["counterpart_data_url"] = counterpart_data_url
            pypi_sign = self.env["synchro.api"].get_pypi_name(
                self, method=vals["method"] if "method" in vals else self.method
            )
            if pypi_sign != self.pypi_sign:
                upd_vals["pypi_sign"] = pypi_sign
            if upd_vals:
                if "counterpart_url" not in upd_vals and "counterpart_url" in vals:
                    upd_vals["counterpart_url"] = vals["counterpart_url"]
                if (
                    "counterpart_data_url" not in upd_vals
                    and "counterpart_data_url" in vals
                ):
                    upd_vals["counterpart_data_url"] = vals["counterpart_data_url"]
                if "pypi_sign" in vals:
                    upd_vals["pypi_sign"] = vals["pypi_sign"]
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
        magic_fields = []
        for backend in self.search([]):
            magic_fields.append(backend.get_loc_ext_id())
        return magic_fields

    def get_dir_mapper(self, model=None, ext_model=None, spec=None):
        DirMapper = self.env["synchro.channel.model"]
        domain = [("synchro_channel_id", "=", self.id)]
        if model:
            domain.append(("name", "=", model))
        if ext_model:
            domain.append(("counterpart_name", "=", ext_model))
        if spec is not None:
            domain.append(("model_spec", "=", spec))
        dir_mapper = DirMapper.search(domain)
        return dir_mapper if len(dir_mapper) == 1 else DirMapper

    @api.model
    def synchro_queue(self, prio=None, max_recs=0, mode=None):
        if mode and mode != self.load_mode:
            return
        Cache = self.env["ir.model.synchro.cache"]

        if self.load_mode == "direct":
            max_ctr = 2048
            max_secs = 180
            commit_rate = 1024
        else:
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
        while max_ctr > 0:
            if datetime.now() > time_limit:
                break
            max_ctr -= 1
            action, model, values, ttl, ctx = Cache.que_pop(self)
            if not action or not model or not values:
                if Cache.que_waiting_len(self):
                    continue
                break
            if action == "synchro":
                id = self.env["ir.model.synchro"].synchro(
                    self.env[model],
                    values,
                    backend=self,
                    only_minimal=False,
                    ttl=ttl,
                    running_in_queue=True,
                    jacket=True,
                    ctx=ctx,
                )
            elif action == "trigger":
                id = self.env["ir.model.synchro"].trigger_one_record(
                    model, self.prefix, values, ttl=ttl, running_in_queue=True, ctx=ctx
                )
            elif action == "push":
                id = self.env["ir.model.synchro"].pull_one_record(
                    model, self.prefix, values, ttl=ttl, running_in_queue=True, ctx=ctx
                )
            else:
                id = -1
            if id > 0:
                loaded_ctr += 1
        if self.state == "run":
            self.state = "ready"
        if loaded_ctr > commit_rate:
            self.env.cr.commit()  # pylint: disable=invalid-commit

    @api.model
    def create(self, vals):
        self.env["ir.model.synchro.cache"].clean_cache()
        backend = super().create(vals)
        upd_vals = backend.counterpart_vals(vals)
        if upd_vals:
            backend.write(upd_vals)
        return backend

    @api.multi
    def write(self, vals):
        self.env["ir.model.synchro.cache"].clean_cache()
        res = super().write(vals)
        for backend in self:
            upd_vals = backend.counterpart_vals(vals)
            if upd_vals:
                backend.write(upd_vals)
        return res
