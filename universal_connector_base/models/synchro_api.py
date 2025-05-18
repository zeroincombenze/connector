#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
from python_plus import unicodes

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
    Trick is merging protocol addons and identity addons in order to make available all
    the needing API.
    This model declare generic API; inheritance is implemented with a simple name
    mangling. So a generic API function is overloaded by function name like
    <identity_name>_<protocol_name>_<function_name>
    or <function_name>_<identity_name>_<protocol_name>; if function does not exit a
    function named <protocol_name>_<function_name> or <function_name>_<protocol_name>
    is searched; if function does not yet exit a function named
    <identity_name>_<function_name> or <function_name>_<indent_name> is searched.

    Model methods:
    session(backend): return counterpart session; this function can call connect() and
            authenticate() functions with internal parameters
    get_model_list(session): return list with couple
            (local model, remote table, model spec)
    validate_ext_model_list(session,model_list): validate model list
            against remote structure
    get_field_list(session,model,magic_fields=None):
            return field list of Odoo model that can be synchronized with counterparty
    validate_ext_field_list(session,ext_model,field_list): validate field list
            against remote structure
    get_response(session,dir_mapper,ext_id,endpoint=None,fields=None):
            return remote data from remote table (specific id or all)
    get_record_list(session,dir_mapper): return record list of remote table
    get_xref_of_id(session,dir_mapper,ext_id): return xref of record id
    remote_search(session,ext_model=None,model=None,spec=None,domain=[],fields=None):
            return primitive api to search for (odoo rules) domain
    remote_browse_odoo(session,ext_id,ext_model=None,model=None,spec=None,fields=None):
            return remote record with ext_id
    """

    _name = "synchro.api"
    _description = "API for Odoo Backend"

    def get_overridden_fct(
        self, backend, name, identity=None, method=None, major_version=None
    ):
        """Search for specific function to call"""
        identity = identity or (backend.identity_id and backend.identity_id.code) or ""
        method = (
            method or (backend.protocol_id and backend.protocol_id.code) or ""
        ).replace("/", "_")
        major_version = str(
            major_version
            or (backend.remote_sw_version and backend.remote_sw_version.split(".")[0])
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
            "%s%s_%s" % (identity, major_version, name),
            "%s_%s" % (name, identity),
            "%s_%s" % (identity, name),
        ):
            if hasattr(self, fct):
                return fct
        self.env["synchro.log"].logmsg(
            "debug",
            "No function %(fct)s found!",
            backend=backend,
            ctx={"fct": "%s_%s%s_%s" % (name, identity, major_version, method)},
        )
        return False  # pragma: no cover

    # ----------------------------------------------------
    # Session functions: session will be become an object
    # Dict items are:
    #   cnx_lgi, cnx_data, login_endpoint, data_endpoint,
    #   session(low level), server_version, backend
    # ----------------------------------------------------
    def init_session(self, backend=None, login_endpoint=False, data_endpoint=False):
        """Initialize session with default values"""
        return unicodes({
            "login_endpoint": login_endpoint,
            "data_endpoint": data_endpoint,
            "cnx_lgi": False,
            "cnx_data": False,
            "session": False,
            "server_version": False,
            "backend": backend,
        })

    def session_is_active(self, session):
        # Return True if session is active
        return (
            session
            and session["cnx_lgi"] is not False
            and session["session"] is not False
        )

    def adapt_values(self, values, with_cast=False):
        return unicodes(values)

    # ------------------------------------------------------
    # API methods to be overridden by inherited classes
    # Inheritance method is not standard python inheritance
    # but is based on function name
    # ------------------------------------------------------

    def get_session(self, backend, force_connect=None):
        """Return the current session object, used to communicate with remote
        Based on backend configuration or if requested, can execute a connect()
        """
        Cache = self.env["synchro.cache"]
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
        """Connect to remote counterparty using backend configuration"""
        return self.get_session(backend, force_connect=True)

    def get_model_list(self, session, backend):
        """Return list of (local model, remote model) to manage"""
        fct = self.get_overridden_fct(backend, "get_model_list")
        values = unicodes(getattr(self, fct or "odoo_get_model_list")(session, backend))
        fct = self.get_overridden_fct(backend, "validate_ext_model_list")
        if fct:
            values = unicodes(getattr(self, fct)(session, values))
        self.env["synchro.log"].logmsg(
            "debug",
            "%(model)s[%(id)s].%(fct)s():",
            res_rec=backend,
            backend=backend,
            values=values,
            ctx={"fct": fct},
        )
        return values

    def get_field_list(self, session, backend, model, magic_fields=None):
        """Return field list of Odoo model that can be synchronized with counterparty"""
        fct = self.get_overridden_fct(backend, "get_field_list")
        values = unicodes(
            getattr(self, fct or "odoo_get_field_list")(
                session, backend, model, magic_fields=magic_fields)
        )
        fct = self.get_overridden_fct(backend, "validate_ext_field_list")
        if fct:
            dir_mapper = backend.get_dir_mapper(model=model)
            values = unicodes(getattr(self, fct)(
                session, dir_mapper.counterpart_name, values))
        return values

    def get_record_list(self, session, dir_mapper):
        "Get record list of model from remote counterparty"
        fct = self.get_overridden_fct(dir_mapper.backend_id, "get_record_list")
        if not fct:  # pragma: no cover
            return []
        return getattr(self, fct)(session, dir_mapper)

    def get_response(self, session, dir_mapper, ext_id):
        """Get response from remote counterparty, usually is a remote record
        with specific remote id"""
        fct = self.get_overridden_fct(dir_mapper.backend_id, "get_response")
        if not fct:  # pragma: no cover
            return fct
        ext_model = dir_mapper.counterpart_name
        fields = dir_mapper.get_field_list()
        values = self.adapt_values(
            getattr(self, fct)(session, dir_mapper, ext_id, fields=fields)
        )
        self.env["synchro.log"].logmsg(
            "debug",
            "%(model)s.get_response(%(backend)s,%(xmodel)s,%(xid)s,f=%(f)s)",
            backend=dir_mapper.backend_id,
            values=values,
            ctx={"xmodel": ext_model, "xid": ext_id, "f": fields},
        )
        return values

    def get_ext_xref_from_ext_id(self, session, dir_mapper, ext_id):
        """Return counterpart external reference of counterpart id and model"""
        fct = self.get_overridden_fct(dir_mapper.backend_id, "get_ext_id_of_ext_ref")
        if not fct:  # pragma: no cover
            return False
        xrefs = getattr(self, fct)(session, dir_mapper, ext_id)
        xref = False
        if xrefs:
            xref_dir_mapper = dir_mapper.backend_id.get_dir_mapper(
                model="ir.model.data"
            )
            if xref_dir_mapper:
                xrefs = self.get_response(session, xref_dir_mapper, xrefs[0])
                xref = xrefs[0]["module"] + "." + xrefs[0]["name"]
            else:
                xref = False
        return xref

    # -----------------------------------------------------------
    # Odoo migration translater
    # Function to implement simple translation for Odoo migration
    # path. They have the same purpose of openupgrade but are
    # bidirectional, so the implement the back-migrate
    # -----------------------------------------------------------

    def get_tnldict(self):
        Cache = self.env["synchro.cache"]
        tnldict = Cache.get_attr(1, "TNL")
        if not tnldict:
            tnldict = {}
            transodoo.read_stored_dict(tnldict)
            Cache.set_attr(1, "TNL", tnldict)
        return tnldict

    def odoo_tnl_value_from_loc_to_ext(self, backend, binding_model, source, fld_name):
        return transodoo.translate_from_to(
            self.get_tnldict(),
            binding_model,
            source,
            release.major_version,
            backend.remote_sw_version,
            type="value",
            fld_name=fld_name,
        )

    # def odoo_tnl_value_from_ext_to_loc(
    # self, backend, binding_model, source, fld_name):
    #     return transodoo.translate_from_to(
    #         self.get_tnldict(),
    #         binding_model,
    #         source,
    #         backend.remote_sw_version,
    #         release.major_version,
    #         type="value",
    #         fld_name=fld_name,
    #     )

    def odoo_tnl_xref_from_ext_to_loc(self, backend, xref):
        def maj_ver(version):
            return int(version.split(".", 1)[0])

        if maj_ver(backend.remote_sw_version) <= 10 < maj_ver(release.major_version):
            xref1 = {
                "base.user_root": "base.user_admin",
                "base.partner_admin": "base.partner_root",
            }.get(xref, xref)
            if xref1 != xref:
                return xref1
        elif maj_ver(backend.remote_sw_version) > 10 >= maj_ver(release.major_version):
            xref1 = {
                "base.user_admin": "base.user_root",
                "base.partner_root": "base.partner_admin",
            }.get(xref, xref)
            if xref1 != xref:
                return xref1
        return transodoo.translate_from_to(
            self.get_tnldict(),
            "",
            xref,
            backend.remote_sw_version,
            release.major_version,
            type="xref",
        )

    def odoo_tnl_local_model_to_ext(self, backend, binding_model):
        ext_model = transodoo.translate_from_to(
            self.get_tnldict(),
            "ir.model",
            binding_model,
            release.major_version,
            backend.remote_sw_version,
            ttype="model",
        )
        if ext_model == binding_model:
            ext_model = transodoo.translate_from_to(
                self.get_tnldict(),
                "ir.model",
                binding_model,
                release.major_version,
                backend.remote_sw_version,
                ttype="merge",
            )
        return ext_model

    def odoo_tnl_ext_model_to_local(self, backend, ext_model):  # pragma: no cover
        binding_model = transodoo.translate_from_to(
            self.get_tnldict(),
            "ir.model",
            ext_model,
            backend.remote_sw_version,
            release.major_version,
            ttype="model",
        )
        if ext_model == binding_model:
            binding_model = transodoo.translate_from_to(
                self.get_tnldict(),
                "ir.model",
                ext_model,
                backend.remote_sw_version,
                release.major_version,
                ttype="merge",
            )
        return binding_model

    def odoo_tnl_local_field_to_ext(self, backend, model, fldname):
        ext_name = transodoo.translate_from_to(
            self.get_tnldict(),
            model,
            fldname,
            release.major_version,
            backend.remote_sw_version,
            ttype="field",
        )
        return ext_name

    # -----------------------------------------------------------
    # Specific implementation of API function for odoo identity
    # and json-http protocol, which are integrated in this module
    # Addons module should copy following functions to implement
    # specific identities or new protocols
    # -----------------------------------------------------------

    def remote_browse_odoo_xmlrpc_https(
            self, session, ext_id,
            ext_model=None, model=None, spec=None, fields=None):
        backend = session["backend"]
        fields = fields or backend.ext_model_field_list(
            backend, ext_model=ext_model, model=model, spec=spec)
        try:
            value = session["cnx_data"].execute_kw(
                backend.database,
                session["session"],
                backend.password,
                ext_model,
                "search_read",
                [[("id", "=", ext_id)]],
                {"fields": fields},
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s browse(db=%(db)s, model=%(model)s, %(id)s)",
                backend=backend,
                res_model=ext_model,
                res_id=ext_id,
                errcode=-13,
                errmsg=e,
            )
            return False
        return unicodes(value)

    def remote_search_read_odoo_xmlrpc_https(
            self, session,
            ext_model=None, model=None, spec=None, domain=[], fields=None):
        backend = session["backend"]
        fields = fields or backend.ext_model_field_list(
            backend, ext_model=ext_model, model=model, spec=spec)
        try:
            values = session["cnx_data"].execute_kw(
                backend.database,
                session["session"],
                backend.password,
                ext_model,
                "search_read",
                [domain],
                {"fields": fields},
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s searching(db=%(db)s, model=%(model)s, %(d)s)",
                backend=backend,
                res_model=ext_model,
                errcode=-13,
                errmsg=e,
                ctx={"d": domain},
            )
            return False
        return unicodes(values)

    def remote_search_odoo_xmlrpc_https(
            self, session, ext_model=None, model=None, spec=None, domain=[]):
        backend = session["backend"]
        try:
            values = session["cnx_data"].execute_kw(
                backend.database,
                session["session"],
                backend.password,
                ext_model,
                "search",
                [domain],
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s searching(db=%(db)s, model=%(model)s, %(d)s)",
                backend=backend,
                res_model=ext_model,
                errcode=-13,
                errmsg=e,
                ctx={"d": domain},
            )
            return False
        return values

    def validate_ext_model_list_odoo_xmlrpc_https(self, session, model_list):
        values = [
            x["model"] for x in self.remote_search_read_odoo_xmlrpc_https(
                session,
                ext_model="ir.model",
                domain=[("model", "in", [x[1] for x in model_list])],
                fields=["model"])
        ]
        return [x for x in model_list if x[1] in values]

    def validate_ext_model_list_odoo_xmlrpc_http(self, session, model_list):
        return self.validate_ext_model_list_odoo_xmlrpc_https(session, model_list)

    def validate_ext_field_list_odoo_xmlrpc_https(self, session, ext_model, field_list):
        values = [
            x["name"] for x in self.remote_search_read_odoo_xmlrpc_https(
                session,
                ext_model="ir.model.fields",
                domain=[("model", "=", ext_model)],
                fields=["name"])
        ]
        return [(x[0], x[1] if x[1] in values else False) for x in field_list]

    def validate_ext_field_list_odoo_xmlrpc_http(self, session, ext_model, field_list):
        return self.validate_ext_field_list_odoo_xmlrpc_https(
            session, ext_model, field_list)

    def get_ext_id_of_ext_ref_odoo_xmlrpc_https(self, session, dir_mapper, ext_id):
        ext_model = dir_mapper.counterpart_name
        return self.remote_search_odoo_xmlrpc_https(
            session,
            ext_model="ir.model.data",
            domain=[("model", "=", ext_model), ("res_id", "=", ext_id)])

    def get_ext_id_of_ext_ref_odoo_xmlrpc_http(self, session, dir_mapper, ext_id):
        return self.get_ext_id_of_ext_ref_odoo_xmlrpc_https(session, dir_mapper, ext_id)

    def odoo_xmlrpc_https_connect(
            self, backend=None, login_endpoint=None, data_endpoint=None):
        if not backend and not login_endpoint and not data_endpoint:
            self.env["synchro.log"].logmsg(
                "error",
                "ERROR: No values supplied",
                errcode=-13,
            )
        elif backend and not login_endpoint or not data_endpoint:
            login_endpoint = backend.counterpart_url
            data_endpoint = backend.counterpart_data_url
        session = self.init_session(
            backend, login_endpoint=login_endpoint, data_endpoint=data_endpoint
        )
        try:
            cnx = client.ServerProxy(login_endpoint)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s opening session on %(ep)s",
                errcode=-13,
                backend=backend,
                ctx={"e": e, "ep": login_endpoint},
            )
            cnx = False
        session["cnx_lgi"] = cnx
        if cnx is not False:
            try:
                cnx_data = client.ServerProxy(data_endpoint)
                # cnx = (cnx, cnx_data)
            except BaseException as e:  # pragma: no cover
                self.env.cr.rollback()  # pylint: disable=invalid-commit
                self.env["synchro.log"].logmsg(
                    "error",
                    "!%(E)s ERROR %(e)s opening session on %(ep)s",
                    errcode=-13,
                    backend=backend,
                    ctx={"e": e, "ep": data_endpoint},
                )
                cnx_data = False
            session["cnx_data"] = cnx_data
        return session

    def odoo_xmlrpc_http_connect(
            self, backend=None, login_endpoint=None, data_endpoint=None):
        return self.odoo_xmlrpc_https_connect(
            backend=backend, login_endpoint=login_endpoint, data_endpoint=data_endpoint)

    def odoo_xmlrpc_https_authenticate(
            self, cnx, database=None, login=None, passwd=None):
        backend = cnx["backend"]
        database = database or backend.database
        login = login or backend.login
        passwd = passwd or backend.password
        try:
            session = cnx["cnx_lgi"].authenticate(database, login, passwd, {})
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s during login(db=%(db)s, user=%(u)s)",
                errcode=-7,
                ctx={"e": e, "db": database, "u": login},
            )
            session = False
        cnx["session"] = session
        return cnx

    def odoo_xmlrpc_http_authenticate(
            self, cnx, database=None, login=None, passwd=None):
        return self.odoo_xmlrpc_https_authenticate(
            cnx, database=database, login=login, passwd=passwd)

    def odoo_xmlrpc_https_session(self, backend):  # pragma: no cover
        return self.odoo_xmlrpc_https_authenticate(
            self.odoo_xmlrpc_https_connect(backend),
        )

    def odoo_xmlrpc_http_session(self, backend):
        return self.odoo_xmlrpc_http_authenticate(
            self.odoo_xmlrpc_http_connect(backend),
        )

    def get_response_odoo_xmlrpc_https(self, session, dir_mapper, ext_id, fields=None):
        return self.remote_browse_odoo_xmlrpc_https(
            session,
            ext_id,
            ext_model=dir_mapper.counterpart_name,
            fields=fields
        )

    def get_response_odoo_xmlrpc_http(self, session, dir_mapper, ext_id, fields=None):
        return self.get_response_odoo_xmlrpc_https(
            session, dir_mapper, ext_id, fields=fields
        )

    def odoo_get_model_list(self, session, backend):
        loc_ext_id = backend.get_loc_ext_id()
        Cache = self.env["synchro.cache"]
        SynchroModel = self.env["synchro.model"]
        model_list = []
        for name, model in self.env.items():
            if not Cache.is_manageable(name) or not hasattr(model, loc_ext_id):
                continue
            if SynchroModel.split_binding_model_n_spec(model._name)[0] != model._name:
                continue  # pragma: no cover
            if backend.identity_id.code in ("odoo", "openerp"):
                ext_name = self.odoo_tnl_local_model_to_ext(backend, model._name)
            else:
                ext_name = False
            model_list.append((name, ext_name, False))
        return model_list

    def odoo_get_field_list(self, session, backend, model, magic_fields=None):
        magic_fields = magic_fields or backend.get_magic_fields(system=True)
        loc_ext_id = backend.get_loc_ext_id()
        res = []
        for loc_name in list(self.env[model].fields_get().keys()):
            if loc_name == "id":
                res.append((loc_ext_id, loc_name))
            elif loc_name not in magic_fields:
                if backend.identity_id.code in ("odoo", "openerp"):
                    ext_name = self.odoo_tnl_local_field_to_ext(
                        backend, model, loc_name) or False
                else:
                    ext_name = False
                res.append((loc_name, ext_name))
        return res

    def get_record_list_odoo_xmlrpc_https(self, session, dir_mapper):
        return self.remote_search_odoo_xmlrpc_https(
            session,
            ext_model=dir_mapper.counterpart_name,
            domain=[])

    def get_record_list_odoo_xmlrpc_http(self, session, dir_mapper):
        return self.get_record_list_odoo_xmlrpc_https(session, dir_mapper)
