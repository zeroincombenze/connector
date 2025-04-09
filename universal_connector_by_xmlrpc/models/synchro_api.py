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

_logger = logging.getLogger(__name__)

try:
    import oerplib3 as oerplib
except ImportError as err:  # pragma: no cover
    _logger.error(err)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

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

    def openerp_xmlrpc_login(self, cnx, database, login, password):
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
        return self.openerp_xmlrpc_login(
            self.openerp_xmlrpc_connect(backend.hostname, backend.port),
            backend.database,
            backend.login,
            backend.password,
        )

    def get_response_openerp_xmlrpc(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        ext_model = dir_mapper.counterpart_name
        if ext_id:
            vals = session["cnx_lgi"].read(ext_model, ext_id, fields)
            if vals and dir_mapper.counterpart_pk not in vals:
                vals[dir_mapper.counterpart_pk] = ext_id
            return [vals]
        return session["cnx_lgi"].env[dir_mapper.name].search([])

    def get_record_list_openerp_xmlrpc(self, session, dir_mapper):
        ext_model = dir_mapper.counterpart_name
        try:
            values = session["cnx_lgi"].search(ext_model, [])
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=dir_mapper.backend_id,
                res_model=ext_model,
                errcode=-13,
                errmsg=e,
            )
            return []
        return values

    def get_ext_id_of_ext_ref_openerp_xmlrpc(self, session, dir_mapper, ext_id):
        ext_model = dir_mapper.counterpart_name
        try:
            values = session["cnx_lgi"].search(
                "ir.model.data", [("model", "=", ext_model), ("res_id", "=", ext_id)]
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=dir_mapper.backend_id,
                res_model=ext_model,
                errcode=-13,
                errmsg=e,
            )
            return []
        return values
