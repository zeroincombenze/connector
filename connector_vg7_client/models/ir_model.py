# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging
from openerp import models, fields, api
import openerp.release as release


_logger = logging.getLogger(__name__)

try:
    import oerplib
except ImportError as err:
    _logger.error(err)


class IrModel(models.Model):
    _inherit = 'ir.model'
    cnx = False
    session = False
    prefix = False

    @api.v8
    def default_params(self):
        endpoint = 'localhost'
        db = 'demo'
        login = 'admin'
        passwd = 'admin'
        protocol = 'xmlrpc'
        port = 8069
        return protocol, endpoint, port, db, login, passwd

    @api.v8
    def parse_endpoint(self, endpoint, login=None, port=None):
        protocol, url, def_port, db, user, passwd = self.default_params()
        login = login or user
        port = port or def_port
        if endpoint:
            if len(endpoint.split('@')) == 2:
                login = endpoint.split('@')[0]
                endpoint = endpoint.split('@')[1]
            if len(endpoint.split(':')) == 2:
                port = int(endpoint.split(':')[1])
                endpoint = endpoint.split(':')[0]
        return protocol, endpoint, port, login

    @api.v8
    def xml_connect(self, endpoint, protocol=None, port=None):
        if not self.cnx:
            prot, endpoint, def_port, login = self.parse_endpoint(endpoint)
            protocol = protocol or prot
            port = port or def_port
            try:
                self.cnx = oerplib.OERP(server=endpoint,
                                        protocol=protocol,
                                        port=port)
            except BaseException:  # pragma: no cover
                self.cnx = False
            if not self.cnx:
                _logger.error('Not response from %s:%s:%d' % (
                    protocol, endpoint, port))
        return self.cnx

    @api.v8
    def xml_login(self, cnx, endpoint,
                  db=None, login=None, passwd=None):
        if not self.session:
            login = login or self.env.user.login
            prot, endpoint, port, user = self.parse_endpoint(endpoint)
            db = db or 'demo'
            passwd = passwd or 'admin'
            login = login or user
            try:
                self.session = cnx.login(database=db,
                                         user=login,
                                         passwd=passwd)
            except BaseException:  # pragma: no cover
                self.session = False
            if not self.session:
                _logger.error('Connection refused by %s@%s/%s' % (
                    login, endpoint, db))
        return self.cnx, self.session

    @api.v8
    def connect_params(self):
        protocol, endpoint, port, db, login, passwd = self.default_params()
        channel_model = self.env['synchro.channel']
        for channel in channel_model.search([], order='sequence', limit=1):
            endpoint = channel.counterpart_url
            db = channel.client_key
            passwd = channel.password
            protocol, endpoint, port, login = self.parse_endpoint(
                endpoint, login=login, port=port)
            break
        return protocol, endpoint, port, db, login, passwd

    @api.v8
    def rpc_session(self):
        if self.cnx and self.session and self.prefix:
            return self.cnx, self.session, self.prefix
        prot, endpoint, port, db, login, passwd = self.connect_params()
        cnx, session = self.xml_login(
            self.xml_connect(endpoint, protocol=prot, port=port),
            endpoint,
            db=db,
            login=login,
            passwd=passwd)
        return cnx, session

    @api.v8
    def get_prefix(self):
        return 'oe%d' % int(release.major_version.split('.')[0])
