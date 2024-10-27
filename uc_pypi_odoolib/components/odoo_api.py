#
# Copyright 2019-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

import logging

from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OdooApiOdoolib(models.AbstractModel):
    _name = "synchro.odoo.api.odoolib"
    _description = "API with JSON RPC and XMLRPC protocols by odoo-client-lib"

    def api_set_env(self, ignore_error=None, backend=None):
        backend.login_endpoint = backend.hostname
        backend.data_endpoint = backend.hostname
        return self

    def api_connect(self, ignore_error=None, backend=None):
        backend.remote_peer = True
        return backend.remote_peer

    def api_remote_login(self, ignore_error=None, backend=None):
        if not backend.remote_peer:
            raise UserError(
                _(
                    "No connection established!"
                )
            )
        try:
            user = backend.pypi.get_connection(
                hostname=backend.hostname,
                database=backend.database,
                protocol=backend.protocol_id.code,
                port=backend.port,
                login=backend.login,
                password=backend.password
            )
        except BaseException:
            raise UserError(
                _(
                    "Remote login failed! DB=%s User=%s" % (self.database, self.login)
                )
            )
        backend.login_endpoint = "%s:%s@%s:%s&db=%s" % (backend.protocol_id.code,
                                                        backend.login,
                                                        backend.hostname,
                                                        backend.port,
                                                        backend.database)
        backend.data_endpoint = "%s:%s:%s&db=%s" % (backend.protocol_id.code,
                                                    backend.hostname,
                                                    backend.port,
                                                    backend.database)
        return user
