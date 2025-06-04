#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from odoo import models
from python_plus import unicodes

_logger = logging.getLogger(__name__)

try:
    import odoorpc
except ImportError as err:  # pragma: no cover
    _logger.error(err)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def remote_browse_odoo_jsonrpc(
            self, session, ext_id,
            ext_model=None, model=None, spec=None, fields=None):
        backend = session["backend"]
        fields = fields or backend.ext_model_field_list(
            backend, ext_model=ext_model, model=model, spec=spec)
        values = session["cnx_lgi"].env[ext_model].read(ext_id, fields)[0]
        return unicodes(values)

    def remote_search_read_odoo_jsonrpc(
            self, session,
            ext_model=None, model=None, spec=None, domain=[], fields=None):
        backend = session["backend"]
        fields = fields or backend.ext_model_field_list(
            backend, ext_model=ext_model, model=model, spec=spec)
        values = session["cnx_lgi"].env[ext_model].search_read(domain, fields=fields)
        return unicodes(values)

    def remote_search_odoo_jsonrpc(
            self, session,
            ext_model=None, model=None, spec=None, domain=[], fields=None):
        return session["cnx_lgi"].env[ext_model].search(domain)

    def validate_ext_model_list_odoo_jsonrpc(self, session, model_list):
        values = [
            x["model"] for x in self.remote_search_read_odoo_jsonrpc(
                session,
                ext_model="ir.model",
                domain=[("model", "in", [x[1] for x in model_list])],
                fields=["model"])
        ]
        return [x for x in model_list if x[1] in values]

    def validate_ext_field_list_odoo_jsonrpc(self, session, ext_model, field_list):
        values = [
            x["name"] for x in self.remote_search_read_odoo_jsonrpc(
                session,
                ext_model="ir.model.fields",
                domain=[("model", "=", ext_model)],
                fields=["name"])
        ]
        return [(x[0], x[1] if x[1] in values else False, x[2]) for x in field_list]

    def get_ext_id_of_ext_ref_odoo_jsonrpc(self, session, dir_mapper, ext_id):
        ext_model = dir_mapper.counterpart_name
        return self.remote_search_odoo_jsonrpc(
            session,
            ext_model="ir.model.data",
            domain=[("model", "=", ext_model), ("res_id", "=", ext_id)])

    def odoo_jsonrpc_connect(self, hostname, port):
        session = self.init_session()
        try:
            cnx = odoorpc.ODOO(hostname, "jsonrpc", port=port)
            if eval(cnx.version.split(".")[0]) < 10:
                self.env["synchro.log"].logmsg(
                    "error",
                    "Unmanageable remote Odoo: please use xmlrpc protocol",
                )
                cnx = False
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "Error %(e)s opening session on %(s)s://%(h)s:%(p)d",
                ctx={"e": e, "h": hostname, "s": "jsonrpc", "p": port},
            )
            cnx = False
        session["cnx_lgi"] = cnx
        session["cnx_data"] = cnx
        session["server_version"] = cnx.version if cnx else False
        return session

    def odoo_jsonrpc_authenticate(self, cnx, database, login, password):
        try:
            cnx["cnx_lgi"].login(db=database, login=login, password=password)
            session = cnx["cnx_lgi"].env.user
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "Error %(e)s during login(db=%(db)s, user=%(u)s)",
                ctx={"e": e, "db": database, "u": login},
            )
            session = False
        cnx["session"] = session
        return cnx

    def odoo_jsonrpc_session(self, backend):
        return self.odoo_jsonrpc_authenticate(
            self.odoo_jsonrpc_connect(backend.hostname, backend.port),
            backend.database,
            backend.login,
            backend.password,
        )

    def get_response_odoo_jsonrpc(self, session, dir_mapper, ext_id, fields=None):
        values = self.remote_browse_odoo_jsonrpc(
            session,
            ext_id,
            ext_model=dir_mapper.counterpart_name,
            fields=fields
        )
        if values and dir_mapper.counterpart_pk not in values:
            values[dir_mapper.counterpart_pk] = ext_id
        return [values]

    def get_record_list_odoo_jsonrpc(self, session, dir_mapper):
        return self.remote_search_odoo_jsonrpc(
            session,
            ext_model=dir_mapper.counterpart_name,
            domain=[])
