☰ Settings > Activate the developer mode

☰ Settings > Technical > Synchronization Backend

#. Set protocol to "By xmlrpc over https" or "By xmlrpc over http" or other
#. Set Host Name, if needed (for xmlrpc over http set endpoint)
#. Set communication port, if needed
#. Declare remote database name. if needed
#. Declare remote user and password (password is not visible)
#. Some protocols require Client Key rather than password
#. Declare identity
#. Declare remote version, if needed
#. Choose prefix for this backend
#. Declare remote user language
#. Set Endpoint, if needed (required for xmlrpc over http)
#. Click on button [Check Connection]

If Odoo can connect with remote counterparty, backend state is set to "Ready".

Some parameters depend on chosen protocol and identity. Below a short list of most used
protocols.

**xmlrpc over http/https**

Read info from required *universal_connector_base* plugin.

**http/https**

Read info from required *universal_connector_by_http* plugin.

**jsonrpc**

Read info from required *universal_connector_by_json* plugin.

**xmlrpc**

Read info from required *universal_connector_by_xmlrpc* plugin.

**csv**

Read info from required *universal_connector_by_jcsv* plugin.
