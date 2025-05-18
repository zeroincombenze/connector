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
    import oerplib3 as oerplib
except ImportError as err:  # pragma: no cover
    _logger.error(err)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def remote_browse_openerp_xmlrpc(
            self, session, ext_id,
            ext_model=None, model=None, spec=None, fields=None):
        backend = session["backend"]
        fields = fields or backend.ext_model_field_list(
            backend, ext_model=ext_model, model=model, spec=spec)
        values = session["cnx_lgi"].read(ext_model, ext_id, fields)
        return unicodes(values)

    def remote_search_openerp_xmlrpc(
            self, session,
            ext_model=None, model=None, spec=None, domain=[], fields=None):
        backend = session["backend"]
        fields = fields or backend.ext_model_field_list(
            backend, ext_model=ext_model, model=model, spec=spec)
        if [fields] == ["id"]:
            return session["cnx_lgi"].search(ext_model, domain)
        values = []
        for id in session["cnx_lgi"].search(ext_model, domain):
            values.append(session["cnx_lgi"].read(ext_model, id, fields=fields))
        return unicodes(values)

    def validate_ext_model_list_openerp_xmlrpc(self, session, model_list):
        values = [
            x["model"] for x in self.remote_search_openerp_xmlrpc(
                session,
                ext_model="ir.model",
                domain=[("model", "in", [x[1] for x in model_list])],
                fields=["model"])
        ]
        return [x for x in model_list if x[1] in values]

    def validate_ext_field_list_openerp_xmlrpc(self, session, ext_model, field_list):
        values = [
            x["name"] for x in self.remote_search_openerp_xmlrpc(
                session,
                ext_model="ir.model.fields",
                domain=[("model", "=", ext_model)],
                fields=["name"])
        ]
        return [(x[0], x[1] if x[1] in values else False) for x in field_list]

    def get_ext_id_of_ext_ref_openerp_xmlrpc(self, session, dir_mapper, ext_id):
        ext_model = dir_mapper.counterpart_name
        return [
            x["id"] for x in self.remote_search_openerp_xmlrpc(
                session,
                ext_model="ir.model.data",
                domain=[("model", "=", ext_model), ("res_id", "=", ext_id)],
                fields=["id"])
        ]

    def openerp_xmlrpc_connect(self, hostname, port):
        session = self.init_session()
        try:
            cnx = oerplib.OERP(server=hostname, protocol="xmlrpc", port=port)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "Error %(e)s opening session on %(s)s://%(h)s:%(p)d",
                ctx={"e": e, "h": hostname, "s": "xmlrpc", "p": port},
            )
            cnx = False
        session["cnx_lgi"] = cnx
        session["cnx_data"] = cnx
        session["server_version"] = cnx.db.server_version() if cnx else False
        return session

    def openerp_xmlrpc_authenticate(self, cnx, database, login, password):
        try:
            session = cnx["cnx_lgi"].login(
                database=database, user=login, passwd=password
            )
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

    def openerp_xmlrpc_session(self, backend):
        return self.openerp_xmlrpc_authenticate(
            self.openerp_xmlrpc_connect(backend.hostname, backend.port),
            backend.database,
            backend.login,
            backend.password,
        )

    def get_response_openerp_xmlrpc(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        values = self.remote_browse_openerp_xmlrpc(
            session,
            ext_id,
            ext_model=dir_mapper.counterpart_name,
            fields=fields
        )
        if values and dir_mapper.counterpart_pk not in values:
            values[dir_mapper.counterpart_pk] = ext_id
        return [values]

    def get_record_list_openerp_xmlrpc(self, session, dir_mapper):
        return [
            x["id"] for x in self.remote_search_openerp_xmlrpc(
                session,
                ext_model=dir_mapper.counterpart_name,
                domain=[],
                fields=["id"])
        ]
