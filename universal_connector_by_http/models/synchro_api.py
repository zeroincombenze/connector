#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

import requests
from odoo import models

_logger = logging.getLogger(__name__)


class SynchroApi(models.Model):
    """API for Odoo Backends"""

    _inherit = "synchro.api"

    def https_default(self, backend):
        return ["https", 0, "demo", "admin", "admin", "", ""]

    def http_default(self, backend):
        return ["http", 0, "demo", "admin", "admin", "", ""]

    def get_pypi_name_https(self):
        return "requests"

    def get_pypi_name_http(self):
        return "requests"

    def https_x_connect(self, endpoint, data_endpoint, headers=None, verify=None):
        session = self.init_sesssion(
            login_endpoint=endpoint, data_endpoint=data_endpoint
        )
        try:
            if headers:
                cnx = requests.get(endpoint, headers=headers, verify=verify)
            else:
                cnx = requests.get(endpoint, verify=verify)
        except BaseException as e:  # pragma: no cover
            self.env.cr.rollback()  # pylint: disable=invalid-commit
            self.env["ir.model.synchro.log"].logmsg(
                "error",
                "Error %(e)s opening session on %(ep)s http=%(h)s",
                ctx={
                    "e": e,
                    "h": getattr(cnx, "status_code", "N/A") if cnx else "N/A",
                    "ep": endpoint,
                },
            )
            cnx = False
        if cnx is not False and hasattr(cnx, "status_code"):
            http_status = getattr(cnx, "status_code", "N/A")
            if http_status != 200:
                self.env["ir.model.synchro.log"].logmsg(
                    "error",
                    "Error http=%(h)s opening session on %(ep)s",
                    ctx={"h": str(http_status), "ep": endpoint},
                )
                cnx = False
        session["cnx_lgi"] = cnx
        session["cnx_data"] = cnx
        return session

    def https_connect(self, endpoint, data_endpoint, headers=None):
        return self.https_x_connect(
            endpoint, data_endpoint, headers=headers, verify=True
        )

    def http_connect(self, endpoint, data_endpoint, headers=None):
        return self.https_x_connect(
            endpoint, data_endpoint, headers=headers, verify=False
        )

    def https_login(self, cnx, backend):
        # TODO
        # if backend.client_key:
        #     return cnx, True
        # session = cnx.session()
        cnx["session"] = True
        return cnx

    def http_login(self, cnx, backend):
        return self.https_login(cnx, backend)

    def https_session(self, backend):
        if backend.client_key:
            headers = {"Authorization": "access_token %s" % backend.client_key}
        else:
            headers = None
        return self.https_login(
            self.https_connect(
                backend.counterpart_url, backend.counterpart_data_url, headers=headers
            ),
            backend,
        )

    def http_session(self, backend):
        return self.https_session(backend)

    def get_response_https(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        backend = dir_mapper.synchro_channel_id
        values = []
        if backend.client_key:
            headers = {"Authorization": "access_token %s" % backend.client_key}
        else:
            headers = None
        endpoint = endpoint or backend.counterpart_data_url
        session = self.https_x_connect(endpoint, endpoint, headers=headers, verify=True)
        response = session["cnx_lgi"]
        if (
            response
            and hasattr(response, "status_code")
            and getattr(response, "status_code", "N/A") == 200
        ):
            values = response.json()
        return values

    def get_response_http(
        self, session, dir_mapper, ext_id=False, endpoint=None, fields=None
    ):
        return self.get_response_https(
            self,
            session,
            dir_mapper,
            ext_id=ext_id,
            endpoint=endpoint,
            fields=fields,
        )
