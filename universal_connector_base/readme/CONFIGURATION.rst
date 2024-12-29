☰ Settings > Technical > Synchronizarion Backend

Set backend parameters to connect with remote counterparty and then click on
button [Check Connection].
If Odoo can connect with remote counterparty, backend state is set to "Ready".

Parameters depend on remote identity and protocol to use.

**xmlrpc over http/https**

This protocol, called XML-RPC, is available with current module and it is implemented
by `python client xmlrpc <https://docs.python.org/3/library/xmlrpc.client.html>`__,
so no additional python package is required to be installed. This protocol is more
simple than REST and SOAP by design.

The typical endpoint to login remote Odoo instance should
be "https://admin@localhost:8069/xmlrpc/2/common" and authentication is based on
username/password; this endppoint uses json rather than xml.
If remote Odoo version is 6.0, 6.1 or 7.0, the typical endpoint should
be "https://admin@localhost:8069/xmlrpc/common".

**http/https**

This protocol is another way to use XML-RPC over http/https. It is supplied by
*universal_connector_by_http* plugin and it is implemented
by `python requests <https://requests.readthedocs.io/en/latest/>`__,
so the `PYPI requests <https://pypi.org/project/requests/>`__ package has to be
installed.

You have to use this protocol to connect remote identities different from Odoo.

**jsonrpc**

This protocol, called JSON-RPC, is like XML-RPC but use JSON representation rather than
XML and it is designed just for Odoo remote identities. It is supplied by
*universal_connector_by_json* plugin and it is implemented
by `odoorpc <https://pythonhosted.org/OdooRPC/>`__,
so the `PYPI odoorpc <https://pypi.org/project/OdooRPC/>`__ package has to be
installed.

**xmlrpc**

This protocol is another way to use XML-RPC over http/https and it is designed just
for Odoo remote identities. It is supplied by
*universal_connector_by_xmlrpc* plugin and it is implemented
by `oerplib <https://pythonhosted.org/OERPLib/>`__,
so the `PYPI oerplib3 <https://pypi.org/project/oerplib3/>`__ package has to be
installed.

You must use this protocol to connect old Odoo instance (before Odoo 10.0).
