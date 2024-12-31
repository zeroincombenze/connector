This module is base for Universal Connector suite and makes available some functions
to synchronize external data with Odoo data.

The used protocol is "xmlrpc over http/https", called XML-RPC, that is  implemented
by `python client xmlrpc <https://docs.python.org/3/library/xmlrpc.client.html>`__,
so no package is required to be installed. This protocol is more simple than REST and
SOAP by design.

The typical endpoint to login remote Odoo instance should be "https://admin@localhost:8069"
and authentication is based on username/password.

Synchronizable models are:

* Company (res.company)
* Country (res.country and res.country.state)
* Currency (res.currency and res.currency.rate)
* Language (res.lang)
* Partner (res.partner and res.partner.category)
* User (res.users and res.groups)
