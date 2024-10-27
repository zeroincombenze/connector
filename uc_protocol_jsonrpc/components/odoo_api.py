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


class OdooApiOdoorpc(models.AbstractModel):
    _name = "synchro.odoo.api.odoorpc"
    _description = "API with JSON RPC protocol by odoorpc"

    def api_set_env(self, ignore_error=None, backend=None):
        backend.login_endpoint = backend.hostname
        backend.data_endpoint = backend.hostname
        return self

    def api_connect(self, ignore_error=None, backend=None):
        backend.remote_peer = backend.pypi.ODOO(
            host=backend.hostname,
            port=backend.port,
            protocol=backend.protocol_id.code,
        )
        if backend.version:
            # Remote peer is Odoo: check if remote version matches required version
            try:
                server_version = backend.remote_peer.version
            except BaseException:
                server_version = "NO VERSION"
            if not server_version.startswith(backend.version):
                raise UserError(
                    _(
                        "Server indicates version %s. Please adapt your configuration"
                        % server_version
                    )
                )
        backend.data_endpoint = "%s:%s:%s" % (backend.protocol_id.code,
                                              backend.hostname,
                                              backend.port)
        backend.login_endpoint = backend.data_endpoint
        return backend.remote_peer

    def api_remote_login(self, ignore_error=None, backend=None):
        if not backend.remote_peer:
            raise UserError(
                _(
                    "No connection established!"
                )
            )
        try:
            user = backend.remote_peer.login(
                db=backend.database,
                login=backend.login,
                password=backend.password,
            )
        except BaseException:
            raise UserError(
                _(
                    "Remote login failed! DB=%s User=%s" % (self.database, self.login)
                )
            )
        if backend.protocol_id.code.startswith("jsonrpc"):
            user = backend.remote_peer.env.user
        if not user:
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

    def api_remote_search(
            self, ignore_error=None, backend=None, remote_model=None, filter=None):
        """Execute the remote search of model.
        This function is inherited by backend, so self is the backend.

        Args:
            self: backend instance from which retrieve connection params
            remote_model (str): remote table to search

        Returns:
            list: remote object list
        """
        return backend.remote_peer.env[remote_model].search(filter or [])
