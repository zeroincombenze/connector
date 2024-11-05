☰ Settings > Technical > Synchronizarion Backend

Set backend parameters to connect with remote counterparty and then click on
button [Check Connection].
If Odoo can connect with remote counterparty, backend state is set to checked.

Parameters depend on remote identity and protocol to use.

**xmlrpc over http/https**

This protocol, called XML-RPC, is available with current module and it is implemented
by `python client xmlrpc <https://docs.python.org/3/library/xmlrpc.client.html>`__,
so no package is required to be installed. This protocol is more simple than REST and
SOAP by design.

The typical endpoint to login remote Odoo instance should be "https://admin@localhost:8069"
and authentication is based on username/password.

You have to use this protocol to connect remote identities different from Odoo.

**http/https**

This protocol is another way to use XML-RPC over http/https. It is supplied by
"universal_connector_by_http" plugin and it is implemented
by `python requests <https://requests.readthedocs.io/en/latest/>`__,
so the `PYPI requests <https://pypi.org/project/requests/>`__ package has to be
installed.

The typical endpoint to login remote Odoo instance should be "https://admin@localhost:8069"
and authentication can be based on username/password or authorization client token.

You have to use this protocol to connect remote identities different from Odoo.

**jsonrpc**

This protocol, called JSON-RPC, is like XML-RPC but use JSON representation instead of
XML and it is designed just for Odoo remote identities. It is supplied by
"universal_connector_by_json" plugin and it is implemented
by `odoorpc <https://pythonhosted.org/OdooRPC/>`__,
so the `PYPI odoorpc <https://pypi.org/project/OdooRPC/>`__ package has to be
installed.

**xmlrpc**

his protocol is another way to use XML-RPC over http/https and it is designed just
for Odoo remote identities. It is supplied by
"universal_connector_by_xmlrpc" plugin and it is implemented
by `oerplib <https://pythonhosted.org/OERPLib/>`__,
so the `PYPI oerplib <https://pypi.org/project/oerplib3/>`__ package has to be
installed.

You must use this protocol to connect old Odoo instance (before Odoo 10.0).
