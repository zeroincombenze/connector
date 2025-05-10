#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import models


class SynchroApi(models.Model):
    _inherit = "synchro.api"

    def openerp_xmlrpc_https_session(self, backend):  # pragma: no cover
        return self.odoo_xmlrpc_https_login(
            self.odoo_xmlrpc_https_connect(backend),
            backend,
        )

    def openerp_xmlrpc_http_session(self, backend):
        return self.odoo_xmlrpc_http_login(
            self.odoo_xmlrpc_http_connect(backend),
            backend,
        )

    def get_response_openerp_xmlrpc_https(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        ext_model = dir_mapper.counterpart_name
        cnx_data = session["cnx_data"]
        try:
            ids = cnx_data.execute_kw(
                dir_mapper.backend_id.database,
                session["session"],
                dir_mapper.backend_id.password,
                ext_model,
                "search",
                [[("id", "=", ext_id)]],
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=dir_mapper.backend_id,
                res_model=ext_model,
                res_id=ext_id,
                errcode=-13,
                errmsg=e,
            )
            return False
        try:
            values = cnx_data.execute_kw(
                dir_mapper.backend_id.database,
                session["session"],
                dir_mapper.backend_id.password,
                ext_model,
                "read",
                ids,
                {"fields": fields},
            )
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["synchro.log"].logmsg(
                "error",
                "!%(E)s! ERROR %(e)s reading(db=%(db)s, model=%(model)s, id=%(id)s)",
                backend=dir_mapper.backend_id,
                res_model=ext_model,
                res_id=ext_id,
                errcode=-13,
                errmsg=e,
            )
            return False
        if not isinstance(values, (tuple, list)):
            values = [values]
        return values

    def get_response_openerp_xmlrpc_http(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        return self.get_response_openerp_xmlrpc_https(
            session, dir_mapper, ext_id=ext_id, endpoint=endpoint, fields=fields
        )

    def openerp_get_model_list(self, session, backend):
        return self.odoo_get_model_list(session, backend)

    def openerp_get_field_list(self, session, backend, model, magic_fields=None):
        return self.odoo_get_field_list(
            session, backend, model, magic_fields=magic_fields
        )

    def get_record_list_openerp_xmlrpc_https(self, session, dir_mapper):
        return self.get_record_list_odoo_xmlrpc_https(
            session, dir_mapper)    # pragma: no cover

    def get_record_list_openerp_xmlrpc_http(self, session, dir_mapper):
        return self.get_record_list_odoo_xmlrpc_http(session, dir_mapper)

    def get_ext_id_of_ext_ref_openerp_xmlrpc_https(self, session, dir_mapper, ext_id):
        return self.get_ext_id_of_ext_ref_odoo_xmlrpc_https(
            session, dir_mapper, ext_id)     # pragma: no cover

    def get_ext_id_of_ext_ref_openerp_xmlrpc_http(self, session, dir_mapper, ext_id):
        return self.get_ext_id_of_ext_ref_odoo_xmlrpc_http(session, dir_mapper, ext_id)
