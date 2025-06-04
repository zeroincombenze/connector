#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import models
from python_plus import unicodes


class SynchroApi(models.Model):
    _inherit = "synchro.api"

    def remote_browse_openerp_xmlrpc_https(
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
                "read",
                [ext_id],
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

    def remote_search_read_openerp_xmlrpc_https(
            self, session,
            ext_model=None, model=None, spec=None, domain=[], fields=None):
        backend = session["backend"]
        fields = fields or backend.ext_model_field_list(
            backend, ext_model=ext_model, model=model, spec=spec)
        ids = self.remote_search_openerp_xmlrpc_https(
            session, ext_model=ext_model, model=model, spec=spec, domain=domain)
        values = []
        for ext_id in ids:
            value = self.remote_browse_openerp_xmlrpc_https(
                session, ext_id,
                ext_model=ext_model,
                model=model,
                spec=spec,
                fields=fields)
            if not value:
                break
            values.append(value)
        return unicodes(values)

    def remote_search_openerp_xmlrpc_https(
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
            return []
        return values

    def validate_ext_model_list_openerp_xmlrpc_https(self, session, model_list):
        values = [
            x["model"] for x in self.remote_search_read_openerp_xmlrpc_https(
                session,
                ext_model="ir.model",
                domain=[("model", "in", [x[1] for x in model_list])],
                fields=["model"])
        ]
        return [x for x in model_list if x[1] in values]

    def validate_ext_model_list_openerp_xmlrpc_http(self, session, model_list):
        return self.validate_ext_model_list_openerp_xmlrpc_https(session, model_list)

    def validate_ext_field_list_openerp_xmlrpc_https(
            self, session, ext_model, field_list):
        values = [
            x["name"] for x in self.remote_search_read_openerp_xmlrpc_https(
                session,
                ext_model="ir.model.fields",
                domain=[("model", "=", ext_model)],
                fields=["name"])
        ]
        return [(x[0], x[1] if x[1] in values else False, x[2]) for x in field_list]

    def validate_ext_field_list_openerp_xmlrpc_http(
            self, session, ext_model, field_list):
        return self.validate_ext_field_list_openerp_xmlrpc_https(
            session, ext_model, field_list)

    def get_ext_id_of_ext_ref_openerp_xmlrpc_https(self, session, dir_mapper, ext_id):
        ext_model = dir_mapper.counterpart_name
        return self.remote_search_openerp_xmlrpc_https(
            session,
            ext_model="ir.model.data",
            domain=[("model", "=", ext_model), ("res_id", "=", ext_id)])

    def get_ext_id_of_ext_ref_openerp_xmlrpc_http(self, session, dir_mapper, ext_id):
        return self.get_ext_id_of_ext_ref_openerp_xmlrpc_https(
            session, dir_mapper, ext_id)

    def openerp_xmlrpc_https_session(self, backend):
        # This function uses same odoo_xmlrpc_https_authenticate and connect
        return self.odoo_xmlrpc_https_authenticate(
            self.odoo_xmlrpc_https_connect(backend),
        )

    def openerp_xmlrpc_http_session(self, backend):
        return self.odoo_xmlrpc_http_authenticate(
            self.odoo_xmlrpc_http_connect(backend),
            )

    def get_response_openerp_xmlrpc_https(
            self, session, dir_mapper, ext_id, fields=None):
        return [self.remote_browse_openerp_xmlrpc_https(
            session,
            ext_id,
            ext_model=dir_mapper.counterpart_name,
            fields=fields
        )]

    def get_response_openerp_xmlrpc_http(
            self, session, dir_mapper, ext_id, fields=None):
        return self.get_response_openerp_xmlrpc_https(
            session, dir_mapper, ext_id, fields=fields
        )

    def get_record_list_openerp_xmlrpc_https(self, session, dir_mapper):
        return self.remote_search_openerp_xmlrpc_https(
            session,
            ext_model=dir_mapper.counterpart_name,
            domain=[])

    def get_record_list_openerp_xmlrpc_http(self, session, dir_mapper):
        return self.get_record_list_openerp_xmlrpc_https(session, dir_mapper)
