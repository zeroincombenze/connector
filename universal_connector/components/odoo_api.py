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


class AbstractOdooAPI(models.AbstractModel):
    _name = "abstract.odoo.api"
    _description = "Common logic for connector API"

    def set_env(self, ignore_error=None):
        """Load python library or PYPI library needed and initialize it.
        Create and set library environment in order to manage the backend connection.
        python library and PYPI library could be used by different backends.
        This function is inherited by backend, so self is the backend.
        Before return it calls specific library set_env function.

        Args:
            self: backend instance from which retrieve connection params

        Returns:
            Obj: self if PYPI library loaded else return None
        """
        if not hasattr(self, "_name") or self._name != "synchro.backend":
            raise UserError(
                _("Internal error!\n" "set_env called without backend instance!\n")
            )
        self.pypi = None
        self.pypi_sign = None
        self.remote_peer = None
        self.api_model = None
        if self.protocol_id:
            # Search for first PYPI installed to use
            pylibs = self.protocol_id.pylib.split(",")
            for pylib in pylibs:
                try:
                    self.pypi = __import__(pylib)
                    ix = pylibs.index(pylib)
                    # Store PYPI library name in backend
                    self.pypi_sign = self.protocol_id.pylib_name.split(",")[ix]
                    self.api_model = "synchro.odoo.api.%s" % pylib
                    break
                except ModuleNotFoundError:
                    # Package <pylib> non installed
                    continue
        if not self.pypi:
            if ignore_error:
                return None
            raise UserError(
                _(
                    "No python neither RCP library found!\n"
                    "Please install %s"
                    % (self.protocol_id.pylib_name.replace(",", " or ") or "odoorpc")
                )
            )
        if self.api_model not in self.env:
            raise UserError(
                _(
                    "The protocol driver %s is incomplete or corrupt!\n"
                    "Model %s is not defined by protocol driver!\n"
                )
            )
        return self.env[self.api_model].api_set_env(
            ignore_error=ignore_error, backend=self
        )

    def get_env(self, no_check_connect=None):
        if not self.pypi and self.api_model:
            pylib = self.api_model.split(".")[-1]
            self.pypi = __import__(pylib)
            if (
                not no_check_connect
                and not self.remote_peer
                and self.state in ("checked", "production")
            ):
                self.connect()

    def connect(self, ignore_error=None):
        """Call specific python library or PYPI library to set connection with
        remote peer.
        This function is inherited by backend, so self is the backend.

        Args:
            self: backend instance from which retrieve connection params

        Returns:
            Obj: connection
        """
        self.get_env(no_check_connect=True)
        self.remote_peer = self.env[self.api_model].api_connect(
            ignore_error=ignore_error, backend=self,
        )
        return self.remote_peer


    def remote_login(self, ignore_error=None):
        """Call specific python library or PYPI library login with
        remote peer.
        This function is inherited by backend, so self is the backend.

        Args:
            self: backend instance from which retrieve connection params

        Returns:
            Obj: connection
        """
        self.get_env()
        return self.env[self.api_model].api_remote_login(
            ignore_error=ignore_error, backend=self,
        )

    def remote_search(self, ignore_error=None, remote_model=None, filter=None):
        """Execute the remote search of model.
        This function is inherited by backend, so self is the backend.

        Args:
            self: backend instance from which retrieve connection params
            remote_model (str): remote table to search

        Returns:
            list: remote object list
        """
        self.get_env()
        return self.env[self.api_model].api_remote_search(
            ignore_error=ignore_error,
            backend=self,
            remote_model=remote_model,
            filter=filter,
        )
