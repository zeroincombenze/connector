#
# Copyright 2019-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import sys
import logging

from odoo import models

_logger = logging.getLogger(__name__)

try:
    if sys.version_info[0] < 3:
        import oerplib
    else:
        import oerplib3 as oerplib
except ImportError as err:  # pragma: no cover
    _logger.error(err)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def odoo_xmlrpc_default(self, backend):
        return ["xmlrpc", 8069, "demo", "admin", "admin", "", ""]

    def get_pypi_name_odoo_xmlrpc(self):
        if sys.version_info[0] < 3:
            return "oerplib"
        else:
            return "oerplib3"

    def odoo_xmlrpc_connect(self, hostname, port):
        session = self.init_sesssion()
        try:
            cnx = oerplib.OERP(server=hostname, protocol="xmlrpc", port=port)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "Error %(e)s opening session on %(s)s://%(h)s:%(p)d",
                ctx={"e": e, "h": hostname, "s": "xmlrpc", "p": port},
            )
            cnx = False
        session["cnx_lgi"] = cnx
        session["cnx_data"] = cnx
        return session

    def odoo_xmlrpc_login(self, cnx, database, login, password):
        try:
            session = cnx["cnx_lgi"].login(
                database=database, user=login, passwd=password
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "Error %(e)s during login(db=%(db)s, user=%(u)s)",
                ctx={"e": e, "db": database, "u": login},
            )
            session = False
        cnx["session"] = session
        return cnx

    def odoo_xmlrpc_session(self, backend):
        return self.odoo_xmlrpc_login(
            self.odoo_xmlrpc_connect(backend.hostname, backend.port),
            backend.database,
            backend.login,
            backend.password,
        )

    def get_response_odoo_xmlrpc(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        if ext_id:
            vals = (
                session["cnx_lgi"].read(synchro_model.name, ext_id, fields)
                # .__dict__["__data__"]["values"]
            )
            if vals and synchro_model.counterpart_pk not in vals:
                vals[synchro_model.counterpart_pk] = ext_id
            return [vals]
        return session["cnx_lgi"].env[synchro_model.name].search([])
