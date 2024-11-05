#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
    """Model for Odoo Backends"""

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

    def _default_data_path(self):
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
            ("checked", "Checked"),
            ("production", "In Production"),
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
        "Prefix for field names",
        required=True,
        help="Prefix to add to model field name to recognize "
        "counterpart ID.Format must be [a-zA-Z]{2}[a-zA-Z0-9]+\n"
        "i.e. with prefix='oe10'\n"
        "<partner_id> means ID in Odoo\n"
        "<oe10:partner_id> means counterpart field name and value\n",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    identity = fields.Selection(
        [
            ("generic", "Generic counterparty"),
            ("odoo", "Odoo instance"),
        ],
        "Counterpart identity",
        required=True,
        default="odoo",
        help="Remote identity like Odoo or Magento or others",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    method = fields.Selection(
        [
            ("xmlrpc/https", "By xmlrpc over https"),
            ("xmlrpc/http", "By xmlrpc over http"),
        ],
        "Send/Receive protocol",
        required=True,
        default="xmlrpc/https",
        help="Communication Protocol to load data from remote counterparty",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
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
            " counterparty in order to set all field values.\n"
            " Load can be executed inside current web session (default) or by cron\n"
            " Direct mode is immediate but is limited by Odoo parameters.\n"
            " Cron mode is delayed and can all recursive referenced records.\n"
        ),
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    deferred_payload = fields.Selection(
        [
            ("0", "Suspended"),
            ("1", "High priority"),
            ("2", "Ordinary priority"),
            ("3", "Low priority"),
        ],
        "Deferred payload",
        required=True,
        default="2",
        help=(
            "When load mode 'cron', every cron event can interrupt CPU."
            " This value ste how the cron interrupt is heavy on CPU execution.\n"
            " Warning! Suspended payload disables cron load!"
        ),
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    odoo_version = fields.Selection(
        _remote_sw_selection,
        "Counterpart software version",
        default="8.0",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    hostname = fields.Char(
        string="Hostname",
        help="Host name without protocol; may be an IP address",
        default=_default_hostname,
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    exchange_path = fields.Char(
        "Exchange directory path",
        help="Login path when load by rpc over https\n"
        "or where file will be read and written when load by csv",
        default=_default_path,
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    data_path = fields.Char(
        "rpc over https data path",
        help="Data path when load by rpc over https",
        default=_default_data_path,
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    login = fields.Char(
        string="Username / Client id",
        help="Username to login remote counterpart or Client ID.",
        default=_default_login,
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    port = fields.Integer(
        string="Communication Port",
        default=_default_port,
        help="Port to comunicate with remote counterparty; Odoo uses 8069",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    database = fields.Char(
        string="Database",
        help="Database name",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    client_key = fields.Char(
        "Client key",
        help="Client key assigned by 3th Party Sender",
        copy=False,
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    password = fields.Char(
        "Password",
        copy=False,
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    counterpart_url = fields.Char(
        "Counterpart login endpoint",
        help="3th Party Sender URL to connect;\n"
        "format should be [https://][username@]url[:port]/login_path",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    counterpart_data_url = fields.Char(
        "Counterpart data endpoint",
        help="3th Party Sender URL to get data;\n"
        "format should be [https://][username@]url[:port]/data_path",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    auto_reconnect = fields.Boolean(
        string="Automatically reconnnect to remote counterpaty",
        default=True,
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
    )
    pypi_sign = fields.Char(
        string="PYPI library",
        readonly=True,
        help="Python library used to communicate with remote counterparty",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        help="Set company, if specific company backend",
    )
    default_lang_id = fields.Many2one(
        comodel_name="res.lang",
        string="Default Language",
        required=True,
        default=_default_language,
    )
    product_without_variants = fields.Boolean("Products without variants")
    tracelevel = fields.Selection(
        [
            ("0", "No Trace"),
            ("1", "Error (Only error messages)"),
            ("2", "Info (Main functions)"),
            ("3", "Warning (All functions)"),
            ("4", "Debug (Trace all)"),
        ],
        string="Trace Level",
        default="0",
        help="Trace data in log. Warning! Use this feature with caution; "
        "all sent data will be recorded in the log file."
        "This feature must be used only to debug handshake",
    )
    model_ids = fields.One2many(
        "synchro.channel.model",
        "synchro_channel_id",
        string="Model mapping",
        states={"checked": [("readonly", True)], "production": [("readonly", True)]},
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

    @api.model
    def _compute_counterpart_url(self):
        countepart_url = self.get_login_endpoint(with_port=True, rebuild=True)
        if countepart_url != self.counterpart_url:
            self.counterpart_url = countepart_url

    @api.onchange("method")
    def _onchange_method(self):
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
        if path != self.exchange_path:
            self.exchange_path = path
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
            login_path, data_path = Api.get_default_paths(self)
            if login_path:
                self.exchange_path = login_path
            if data_path:
                self.data_path = data_path
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
        """Build unique index on table to <vg7>_id for performance"""
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

    @api.multi
    def button_check_connection(self):
        """This function applies for remote login using remote API"""
        self.ensure_one()
        session = self.connect()
        if (
            self.env["synchro.api"].session_is_active(session)
            and self.state == "checked"
        ):
            self.env["ir.model.synchro.log"].logmsg(
                "info",
                "%(model)s[%(id)s].button_check_connection(ep=%(lgi_ep)s,h=%(host)s):",
                res_rec=self,
                backend=self,
            )
            if self.identity == "odoo" and not self.model_ids:
                self.button_build_model_map()
            for synchro_model in self.model_ids:
                synchro_model.analyze_synchro_model()

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
        if (
            self.env["synchro.api"].session_is_active(session)
            and self.state == "checked"
        ):
            remote_list = self.env["synchro.api"].get_list(session, self)
            for actual_model, remote_model in remote_list:
                if actual_model and actual_model not in self.env:
                    continue
                self.env["synchro.channel.model"].build_odoo_synchro_model(
                    self, remote_model, model=actual_model
                )

    def get_loc_ext_id(self):
        return "%s_id" % self.prefix

    def get_method_from_protocol(self, prot):
        return {
            "sftp": "FTP",
            "ftps": "FTP",
        }.get(prot) or False

    def get_protocol_from_method(self, method):
        if method:
            return {
                "xmlrpc/https": method.split("/")[1],
                "xmlrpc/http": method.split("/")[1],
                "FTP": "sftp",
            }.get(method) or False
        return method

    @api.model
    def get_login_endpoint(self, with_port=None, rebuild=False):
        return self.env["synchro.api"].get_login_endpoint(
            self, with_port=with_port, rebuild=rebuild
        )

    @api.model
    def get_data_endpoint(self, data_path=None):
        return self.env["synchro.api"].get_data_endpoint(self, data_path=data_path)

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
                _x, def_port, def_db, def_login, def_pwd, login_path, data_path = (
                    Api.get_default(self)
                )
                hostname = self.hostname or "localhost"
                database = self.database or def_db
                login = self.login or def_login
                password = self.password or def_pwd
                if with_path == "data":
                    path = self.data_path or data_path
                else:
                    path = self.exchange_path or login_path
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
            _x, port, database, login, password, path, data_path = Api.get_default(self)
            if with_path == "data":
                path = data_path
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
        if self.state not in ("checked", "production"):  # pragma: no cover
            return False
        return self.env["synchro.api"].get_session(self)

    def connect(self):
        session = self.env["synchro.api"].get_session(self, force_connect=True)
        if self.env["synchro.api"].session_is_active(session):
            self.state = "checked"
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
        if (
            "hostname" in vals
            or "login" in vals
            or "port" in vals
            or "exchange_path" in vals
            or "data_path" in vals
        ):
            if "counterpart_url" not in vals:
                counterpart_url = self.get_login_endpoint(with_port=True)
                if counterpart_url != self.counterpart_url:
                    upd_vals["counterpart_url"] = counterpart_url
            if "counterpart_data_url" not in vals:
                counterpart_data_url = self.get_data_endpoint()
                if counterpart_data_url != self.counterpart_data_url:
                    upd_vals["counterpart_data_url"] = counterpart_data_url
        if not self.pypi_sign:
            if "method" in vals:
                vals["pypi_sign"] = self.env["synchro.api"].get_pypi_name(
                    self, method=vals["method"]
                )
            elif self.method:
                vals["pypi_sign"] = self.env["synchro.api"].get_pypi_name(
                    self, method=self.method
                )
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

    def assign_backend(self, vals):
        backend = False
        for ext_ref in list(vals.keys()):
            if ":" not in ext_ref:  # pragma: no cover
                continue
            backend = self.search(
                [
                    ("state", "in", ("checked", "production")),
                    ("prefix", "=", ext_ref.split(":", 1)[0]),
                ]
            )
            if backend:
                backend = backend[0]
                break
        if not backend:  # pragma: no cover
            backend = self.search(
                [("state", "in", ("checked", "production"))], order="sequence, id"
            )
            if backend:
                backend = backend[0]
        return backend

    @api.model
    def synchro_queue(self, prio=None, max_recs=0, mode=None):
        if mode and mode != self.load_mode:
            return
        SynchroLog = self.env["ir.model.synchro.log"]
        Cache = self.env["ir.model.synchro.cache"]

        if self.load_mode == "direct":
            max_ctr = 1024
            max_secs = 120
        else:
            # Priority is 1..3 or 0 (stopped)
            prio = prio or int(self.deferred_payload)
            max_ctr, max_secs = {
                0: (0, 0),
                1: (64, 30),
                2: (32, 20),
                3: (16, 10),
            }[prio]
            max_ctr = max_recs or max_ctr
        max_ctr = min(max_ctr, Cache.que_waiting_len(self))
        if max_ctr > 0:
            SynchroLog.logmsg(
                "info",
                "synchro_queue(%(backend)s)",
                backend=self,
                values={"max_ctr": max_ctr, "max_secs": max_secs},
            )
        time_limit = datetime.now() + timedelta(max_secs)
        loaded_ctr = 0
        while max_ctr > 0:
            if datetime.now() > time_limit:
                break
            max_ctr -= 1
            action, model, values, ttl = Cache.que_pop(self)
            if not action or not model or not values:
                continue
            if action == "synchro":
                id = self.env["ir.model.synchro"].generic_synchro(
                    self.env[model],
                    values,
                    jacket=True,
                    backend=self,
                    only_minimal=False,
                    ttl=ttl,
                )
            elif action == "trigger":
                id = self.env["ir.model.synchro"].trigger_one_record(
                    model, self.prefix, values, ttl=ttl
                )
            else:
                id = -1
            # if id < 1:
            #     break
            if id > 0:
                loaded_ctr += 1
        if loaded_ctr > 0:
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
