#
# Copyright 2018-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
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
    import odoorpc
except ImportError as err:  # pragma: no cover
    _logger.error(err)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def odoo_jsonrpc_default(self, backend):
        return ["jsonrpc", 8069, "demo", "admin", "admin", "", ""]

    def get_pypi_name_odoo_jsonrpc(self):
        return "odorpc"

    def odoo_jsonrpc_connect(self, hostname, port):
        session = self.init_sesssion()
        try:
            cnx = odoorpc.ODOO(hostname, "jsonrpc", port=port)
            if eval(cnx.version.split(".")[0]) < 10:
                self.env["ir.model.synchro.log"].logmsg(
                    "error",
                    "Unmanageable remote Odoo: please use xmlrpc protocol",
                )
                cnx = False
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "Error %(e)s opening session on %(s)s://%(h)s:%(p)d",
                ctx={"e": e, "h": hostname, "s": "jsonrpc", "p": port},
            )
            cnx = False
        session["cnx_lgi"] = cnx
        session["cnx_data"] = cnx
        return session

    def odoo_jsonrpc_login(self, cnx, database, login, password):
        try:
            cnx["cnx_lgi"].login(db=database, login=login, password=password)
            session = cnx["cnx_lgi"].env.user
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

    def odoo_jsonrpc_session(self, backend):
        return self.odoo_jsonrpc_login(
            self.odoo_jsonrpc_connect(backend.hostname, backend.port),
            backend.database,
            backend.login,
            backend.password,
        )

    def get_response_odoo_jsonrpc(
        self, session, synchro_model, ext_id=False, endpoint=None, fields=None
    ):
        ext_model = synchro_model.counterpart_name
        if ext_id:
            vals = session["cnx_lgi"].env[ext_model].read(ext_id, fields)[0]
            if vals and synchro_model.counterpart_pk not in vals:
                vals[synchro_model.counterpart_pk] = ext_id
            return [vals]
        return session["cnx_lgi"].env[synchro_model.name].search([])

    def get_record_list_odoo_jsonrpc(self, session, synchro_model):
        ext_model = synchro_model.counterpart_name
        try:
            values = session["cnx_lgi"].env[ext_model].search([])
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=synchro_model.synchro_channel_id,
                res_model=ext_model,
                errcode=-13,
                errmsg=e,
            )
            return []
        return values
