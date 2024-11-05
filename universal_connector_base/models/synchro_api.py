#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from xmlrpc import client
import logging

from odoo import models
from odoo import release
from python_plus import unicodes, _u

_logger = logging.getLogger(__name__)
try:
    from clodoo import transodoo
except ImportError as err:  # pragma: no cover
    _logger.error(err)


class SynchroApi(models.Model):
    """API for remote counterpart communication
    This model communicates with remote counterparty through backend protocol.
    Each counterparty has its own structure and every protocol has it own handshake
    rules so it is very difficult to manage all counterparties.
    Trick is merging protocol addons and identity addons in order to make avaialble all
    the needing API.
    This model declare generic API; inheritance is implemented by naming. A generic API
    function is overloaded by function name like
    <indent_name>_<protocol_name>_<funcion_name>
    or <funcion_name>_<indent_name>_<protocol_name>; if function does not exit a
    function named <protocol_name>_<funcion_name> or <funcion_name>_<protocol_name>
    is searched; if function does not yet exit a function named
    <indent_name>_<funcion_name> or <funcion_name>_<indent_name> is searched.

    Model methods:
    default(backend): return default values load on backend
    get_data_endpoint(backend, exchange_path=None):
            return exchange endpoint from login endpoint
    get_login_endpoint(backend,with_port=None,rebuild=None)
    get_pypi_name(): return python library name
    session(backend): return counterpart session (connect + login)
    get_list(session,backend): return list with couple (local model, remote table)
    get_response(session,synchro_model,ext_id=None,endpoint=None,fields=None):
            return remote data from remote table (specific id or all)
    Usually session calls connect() and login() functions with internal parameters.
    """

    _name = "synchro.api"
    _description = "API for Odoo Backend"

    def init_sesssion(self, login_endpoint=False, data_endpoint=False):
        # Session object: will be become an object. Dict items are:
        # cnx_lgi, cnx_data, login_endpoint, data_endpoint, session
        return {
            "login_endpoint": login_endpoint,
            "data_endpoint": data_endpoint,
            "cnx_lgi": False,
            "cnx_data": False,
            "session": False,
        }

    def session_is_active(self, session):
        return (
            session
            and session["cnx_lgi"] is not False
            and session["session"] is not False
        )

    def get_overridden_fct(
        self, backend, name, identity=None, method=None, major_version=None
    ):
        identity = identity or backend.identity
        method = (method or backend.method or "").replace("/", "_")
        major_version = str(
            major_version
            or (backend.odoo_version and backend.odoo_version.split(".")[0])
            or "0"
        )
        for fct in (
            "%s_%s%s_%s" % (name, identity, major_version, method),
            "%s%s_%s_%s" % (identity, major_version, method, name),
            "%s_%s_%s" % (name, identity, method),
            "%s_%s_%s" % (identity, method, name),
            "%s_%s" % (name, method),
            "%s_%s" % (method, name),
            "%s_%s%s" % (name, identity, major_version),
            "%s_%s" % (name, identity),
            "%s_%s" % (identity, name),
        ):
            if hasattr(self, fct):
                return fct
        return False  # pragma: no cover

    def simple_cast(self, value):
        if isinstance(value, (list, tuple)):
            new_vals = []
            for i, x in enumerate(value):
                new_vals.append(self.adapt_values(x))
            value = new_vals
        elif isinstance(value, str):
            try:
                if value.isdigit() and not value.startswith("0") and len(value) < 10:
                    value = int(value)
                elif value.startswith("[") and value.endswith("]"):
                    value = self.adapt_values(eval(value))
                elif value.startswith("{") and value.endswith("}"):
                    value = self.adapt_values(eval(value))
            except BaseException:  # pragma: no cover
                pass
        return _u(value)

    def adapt_values(self, values, with_cast=False):
        return unicodes(values)

    def odoo_xmlrpc_https_get_data_endpoint(self, backend, exchange_path=None):
        if backend.counterpart_url:
            return backend.counterpart_url.replace("/common", "/object")
        return False  # pragma: no cover

    def get_data_endpoint(self, backend, exchange_path=None):
        fct = self.get_overridden_fct(backend, "get_data_endpoint")
        if fct:
            return _u(getattr(self, fct)(backend, exchange_path=exchange_path))
        (protocol, hostname, port, database, login, passwd, path) = (
            backend.parse_endpoint(with_path="data")
        )
        endpoint = protocol + "://" + backend.hostname
        if backend.port:
            endpoint += ":%d" % backend.port
        exchange_path = exchange_path or path
        if exchange_path:
            endpoint += exchange_path
        return endpoint

    def odoo_xmlrpc_http_get_data_endpoint(self, backend, exchange_path=None):
        return self.odoo_xmlrpc_https_get_data_endpoint(
            backend, exchange_path=exchange_path
        )

    def odoo6_xmlrpc_https_default(self, backend):
        return [
            "https",
            8069,
            "demo",
            "admin",
            "admin",
            "/xmlrpc/common",
            "/xmlrpc/object",
        ]

    def odoo6_xmlrpc_http_default(self, backend):  # pragma: no cover
        return ["http"] + self.odoo6_xmlrpc_https_default(backend)[1:]

    def odoo7_xmlrpc_https_default(self, backend):  # pragma: no cover
        return self.odoo6_xmlrpc_https_default(backend)

    def odoo7_xmlrpc_http_default(self, backend):
        return self.odoo6_xmlrpc_http_default(backend)

    def odoo8_xmlrpc_https_default(self, backend):  # pragma: no cover
        return self.odoo6_xmlrpc_https_default(backend)

    def odoo8_xmlrpc_http_default(self, backend):
        return self.odoo6_xmlrpc_http_default(backend)

    def odoo_xmlrpc_https_default(self, backend):
        return [
            "https",
            8069,
            "demo",
            "admin",
            "admin",
            "/xmlrpc/2/common",
            "/xmlrpc/2/object",
        ]

    def odoo_xmlrpc_http_default(self, backend):
        return ["http"] + self.odoo_xmlrpc_https_default(backend)[1:]

    def get_default(self, backend):
        # Return default protocol, port, database, login pwd, lgi_path, exchange_path
        fct = self.get_overridden_fct(backend, "default")
        if not fct:  # pragma: no cover
            return False, False, False, False, False, False, False
        return getattr(self, fct)(backend)

    def get_default_prot_port(self, backend):
        return self.get_default(backend)[:2]

    def get_default_login(self, backend):
        return self.get_default(backend)[2:5]

    def get_default_paths(self, backend):
        return self.get_default(backend)[5:]

    def get_pypi_name_odoo_xmlrpc_https(self):  # pragma: no cover
        return "xmlrpc"

    def get_pypi_name_odoo_xmlrpc_http(self):
        return "xmlrpc"

    def get_pypi_name(self, backend, method=None):
        fct = self.get_overridden_fct(backend, "get_pypi_name", method=method)
        if not fct:  # pragma: no cover
            return fct
        self.env["ir.model.synchro.log"].logmsg(
            "debug",
            "%(model)s[%(id)s].%(fct)s():",
            res_rec=backend,
            backend=backend,
            ctx={"fct": fct},
        )
        return _u(getattr(self, fct)())

    def _odoo_xmlrpc_x_connect(self, login_endpoint, data_endpoint):
        session = self.init_sesssion(
            login_endpoint=login_endpoint, data_endpoint=data_endpoint
        )
        try:
            cnx = client.ServerProxy(login_endpoint)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s opening session on %(ep)s",
                errcode=-13,
                ctx={"e": e, "ep": login_endpoint},
            )
            cnx = False
        session["cnx_lgi"] = cnx
        session["cnx_data"] = cnx
        if cnx is not False:
            try:
                cnx_data = client.ServerProxy(data_endpoint)
                # cnx = (cnx, cnx_data)
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["ir.model.synchro.log"].logmsg(
                    "error",
                    "!%(E)s ERROR %(e)s opening session on %(ep)s",
                    errcode=-13,
                    ctx={"e": e, "ep": data_endpoint},
                )
                cnx_data = False
            session["cnx_data"] = cnx_data
        return session

    def odoo_xmlrpc_https_connect(self, backend):  # pragma: no cover
        return self._odoo_xmlrpc_x_connect(
            backend.counterpart_url, backend.counterpart_data_url
        )

    def odoo_xmlrpc_http_connect(self, backend):
        return self._odoo_xmlrpc_x_connect(
            backend.counterpart_url, backend.counterpart_data_url
        )

    def _odoo_xmlrpc_x_login(self, cnx, database, login, passwd):
        try:
            session = cnx["cnx_lgi"].authenticate(database, login, passwd, {})
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s during login(db=%(db)s, user=%(u)s)",
                errcode=-7,
                ctx={"e": e, "db": database, "u": login},
            )
            session = False
        cnx["session"] = session
        return cnx

    def odoo_xmlrpc_https_login(self, cnx, backend):  # pragma: no cover
        return self._odoo_xmlrpc_x_login(
            cnx, backend.database, backend.login, backend.password
        )

    def odoo_xmlrpc_http_login(self, cnx, backend):
        return self._odoo_xmlrpc_x_login(
            cnx, backend.database, backend.login, backend.password
        )

    def odoo_xmlrpc_https_session(self, backend):  # pragma: no cover
        return self.odoo_xmlrpc_https_login(
            self.odoo_xmlrpc_https_connect(backend),
            backend,
        )

    def odoo_xmlrpc_http_session(self, backend):
        return self.odoo_xmlrpc_http_login(
            self.odoo_xmlrpc_http_connect(backend),
            backend,
        )

    def get_session(self, backend, force_connect=None):
        Cache = self.env["ir.model.synchro.cache"]
        session = Cache.get_attr(self.id, "CNX")
        if not force_connect:
            if not self.session_is_active(session) and backend.auto_reconnect:
                force_connect = True
        if force_connect:
            fct = self.get_overridden_fct(backend, "session")
            if not fct:  # pragma: no cover
                session = False
            else:
                session = getattr(self, fct)(backend)
            Cache.set_attr(backend.id, "CNX", session)
            Cache.set_attr(backend.id, "SESSION", session)
        return session

    def connect(self, backend):
        return self.get_session(backend, force_connect=True)

    def get_response_odoo6_xmlrpc_https(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        ext_model = synchro_model.counterpart_name
        cnx_data = session["cnx_data"]
        try:
            ids = cnx_data.execute_kw(
                synchro_model.synchro_channel_id.database,
                session["session"],
                synchro_model.synchro_channel_id.password,
                ext_model,
                "search",
                [[("id", "=", ext_id)]],
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=synchro_model.synchro_channel_id,
                res_model=ext_model,
                id=ext_id,
                errcode=-13,
                errmsg=e,
            )
            return False
        try:
            values = cnx_data.execute_kw(
                synchro_model.synchro_channel_id.database,
                session["session"],
                synchro_model.synchro_channel_id.password,
                ext_model,
                "read",
                ids,
                {"fields": fields},
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=synchro_model.synchro_channel_id,
                res_model=ext_model,
                id=ext_id,
                errcode=-13,
                errmsg=e,
            )
            return False
        if not isinstance(values, (tuple, list)):
            values = [values]
        return values

    def get_response_odoo6_xmlrpc_http(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        return self.get_response_odoo6_xmlrpc_https(
            session, synchro_model, ext_id=ext_id, endpoint=endpoint, fields=fields
        )

    def get_response_odoo7_xmlrpc_https(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):  # pragma: no cover
        return self.get_response_odoo6_xmlrpc_https(
            session, synchro_model, ext_id=ext_id, endpoint=endpoint, fields=fields
        )

    def get_response_odoo7_xmlrpc_http(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        return self.get_response_odoo6_xmlrpc_http(
            session, synchro_model, ext_id=ext_id, endpoint=endpoint, fields=fields
        )

    def get_response_odoo_xmlrpc_https(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        ext_model = synchro_model.counterpart_name
        try:
            values = session["cnx_data"].execute_kw(
                synchro_model.synchro_channel_id.database,
                session["session"],
                synchro_model.synchro_channel_id.password,
                ext_model,
                "search_read",
                [[("id", "=", ext_id)]],
                {"fields": fields},
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=synchro_model.synchro_channel_id,
                res_model=ext_model,
                id=ext_id,
                errcode=-13,
                errmsg=e,
            )
            return False
        return values

    def get_response_odoo_xmlrpc_http(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        return self.get_response_odoo_xmlrpc_https(
            session, synchro_model, ext_id=ext_id, endpoint=None, fields=fields
        )

    def get_response(self, session, synchro_model, ext_id=False, endpoint=None):
        fct = self.get_overridden_fct(synchro_model.synchro_channel_id, "get_response")
        if not fct:  # pragma: no cover
            return fct
        ext_model = synchro_model.counterpart_name
        actual_model = synchro_model.get_actual_model_name(synchro_model.name)
        struct = self.env[actual_model].fields_get()
        fields = []
        for synchro_field in synchro_model.field_ids:
            if synchro_field.counterpart_name and synchro_field.name in struct:
                fields.append(synchro_field.counterpart_name)
        values = self.adapt_values(
            getattr(self, fct)(
                session, synchro_model, ext_id=ext_id, endpoint=endpoint, fields=fields
            )
        )
        self.env["ir.model.synchro.log"].logmsg(
            "debug",
            "%(model)s.get_response(%(backend)s,%(xmodel)s,%(xid)s,ep=%(ep)s,f=%(f)s)",
            backend=synchro_model.synchro_channel_id,
            values=values,
            ctx={"ep": endpoint or "", "xmodel": ext_model, "xid": ext_id, "f": fields},
        )
        return values

    def odoo_get_list(self, session, backend):
        loc_ext_id = backend.get_loc_ext_id()
        Cache = self.env["ir.model.synchro.cache"]
        model_list = []
        for name, model in self.env.items():
            if not Cache.is_manageable(name):
                continue
            if not hasattr(model, loc_ext_id):
                continue
            ext_name = self.odoo_tnl_local_model_to_ext(backend, model._name)
            model_list.append((name, ext_name))
        return model_list

    def get_list(self, session, backend):
        fct = self.get_overridden_fct(backend, "get_list")
        if not fct:  # pragma: no cover
            return []
        values = unicodes(getattr(self, fct)(session, backend))
        self.env["ir.model.synchro.log"].logmsg(
            "debug",
            "%(model)s[%(id)s].%(fct)s():",
            res_rec=backend,
            backend=backend,
            values=values,
            ctx={"fct": fct},
        )
        return values

    def get_login_endpoint_odoo_https(self, backend, with_port=None, rebuild=False):
        if not rebuild and backend.counterpart_url and not backend.hostname:
            endpoint = backend.counterpart_url
        elif backend.hostname:
            endpoint = backend.get_protocol_from_method(backend.method) or ""
            endpoint += "://" + backend.hostname
            if with_port and backend.port:
                endpoint += ":%d" % backend.port
            if backend.lgi_path:
                endpoint += backend.lgi_path
        else:
            endpoint = ""
        return endpoint

    def get_login_endpoint_odoo_http(self, backend, with_port=None, rebuild=False):
        return self.get_login_endpoint_odoo_https(
            backend, with_port=with_port, rebuild=rebuild
        )

    def get_login_endpoint(self, backend, with_port=None, rebuild=False):
        fct = self.get_overridden_fct(backend, "get_login_endpoint")
        if fct:  # pragma: no cover
            return _u(getattr(self, fct)(backend, with_port=with_port, rebuild=rebuild))
        if not rebuild and backend.counterpart_url and not backend.hostname:
            endpoint = backend.counterpart_url
        elif backend.hostname:
            endpoint = backend.get_protocol_from_method(backend.method) or ""
            if backend.login:
                endpoint += "://" + backend.login + "@" + backend.hostname
            else:
                endpoint += "://" + backend.hostname
            if with_port and backend.port:
                endpoint += ":%d" % backend.port
            if backend.lgi_path:
                endpoint += backend.lgi_path
        else:
            endpoint = ""
        return endpoint

    def odoo_get_field_list(self, session, backend, model, magic_fields=None):
        magic_fields = magic_fields or []
        loc_ext_id = backend.get_loc_ext_id()
        res = []
        for loc_name in list(self.env[model].fields_get().keys()):
            if loc_name == "id":
                res.append((loc_ext_id, loc_name))
            elif loc_name not in magic_fields:
                ext_name = self.odoo_tnl_local_field_to_ext(backend, model, loc_name)
                res.append((loc_name, ext_name))
        return res

    def get_field_list(self, session, backend, model, magic_fields=None):
        fct = self.get_overridden_fct(backend, "get_field_list")
        if not fct:  # pragma: no cover
            return []
        return unicodes(
            getattr(self, fct)(session, backend, model, magic_fields=magic_fields)
        )

    def get_tnldict(self):
        Cache = self.env["ir.model.synchro.cache"]
        tnldict = Cache.get_attr(1, "TNL")
        if not tnldict:
            tnldict = {}
            transodoo.read_stored_dict(tnldict)
            Cache.set_attr(1, "TNL", tnldict)
        return tnldict

    def odoo_tnl_value_from_to(self, backend, actual_model, source, fld_name):
        return transodoo.translate_from_to(
            self.get_tnldict(),
            actual_model,
            source,
            release.major_version,
            backend.odoo_version,
            type="value",
            fld_name=fld_name,
        )

    def odoo_tnl_local_model_to_ext(self, backend, actual_model):
        ext_model = transodoo.translate_from_to(
            self.get_tnldict(),
            "ir.model",
            actual_model,
            release.major_version,
            backend.odoo_version,
            ttype="model",
        )
        if ext_model == actual_model:
            ext_model = transodoo.translate_from_to(
                self.get_tnldict(),
                "ir.model",
                actual_model,
                release.major_version,
                backend.odoo_version,
                ttype="merge",
            )
        return ext_model

    def odoo_tnl_ext_model_to_local(self, backend, ext_model):
        actual_model = transodoo.translate_from_to(
            self.get_tnldict(),
            "ir.model",
            ext_model,
            backend.odoo_version,
            release.major_version,
            ttype="model",
        )
        if ext_model == actual_model:
            actual_model = transodoo.translate_from_to(
                self.get_tnldict(),
                "ir.model",
                ext_model,
                backend.odoo_version,
                release.major_version,
                ttype="merge",
            )
        return actual_model

    def odoo_tnl_local_field_to_ext(self, backend, model, fldname):
        ext_name = transodoo.translate_from_to(
            self.get_tnldict(),
            model,
            fldname,
            release.major_version,
            backend.odoo_version,
            ttype="field",
        )
        # if ext_name == fldname:
        #     ext_name = transodoo.translate_from_to(
        #         self.get_tnldict(),
        #         model,
        #         fldname,
        #         release.major_version,
        #         backend.odoo_version,
        #         ttype="merge",
        #     )
        return ext_name
