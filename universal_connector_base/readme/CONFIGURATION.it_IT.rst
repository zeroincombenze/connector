☰ Configurazione > Funzioni tecniche > Dorsale di sincronizzazione

Impostare i parametri di sincronizzazione della dorsale e poi fare click sul
bottone [Check Connection].
Se Odoo riesce a connettersi con la controparte remota, lo stato della dorsale è
modificato in "Pronto".

I parametri dipendono dal tipo di protocollo utilizzato e dall'indenità remota.

**xmlrpc over http/https**

Questo protocollo, chiamato XML-RPC, è incluso nel presente modulo
attraverso `python client xmlrpc <https://docs.python.org/3/library/xmlrpc.client.html>`__,
quindi nessun package python aggiuntivo è necessario.

Il tipico endpoint per connettere un'istanza remota di Odoo può
essere "https://admin@localhost:8069/xmlrpc/2/common" con autenticazione basata su
username/password; questo endppoint usa json invece di xml.
Se la versione remota di Odoo è 6.0, 6.1 o 7.0, il tipico endpoint può
essere "https://admin@localhost:8069/xmlrpc/common".

**http/https**

Questo protocollo è una variante di XML-RPC over http/https. Vine fornito dal modulo
*universal_connector_by_http*
attraverso `python requests <https://requests.readthedocs.io/en/latest/>`__,
quindi il package python `PYPI requests <https://pypi.org/project/requests/>`__ deve
essere installato.

Usare questo protocollo per identità diverse da Odoo.

**jsonrpc**

Questo protocollo, chiamato JSON-RPC, è simile a XML-RPC ma usa la rappresentazione
JSON invece di XML ed è progettato specificatamente per istanze remote di Odoo.
Viene fornito dal modulo *universal_connector_by_json*
attraverso `odoorpc <https://pythonhosted.org/OdooRPC/>`__,
quindi il package python `PYPI odoorpc <https://pypi.org/project/OdooRPC/>`__ deve
essere installato.

**xmlrpc**

Questo protocollo è una variante di XML-RPC over http/https ed è progettato
specificatamente per istanze remote di Odoo. Viene fornito dal
modulo *universal_connector_by_xmlrpc*
attraverso `oerplib <https://pythonhosted.org/OERPLib/>`__,
quindi il package python `PYPI oerplib3 <https://pypi.org/project/oerplib3/>`__ deve
essere installato.

Usare questo protocollo per connettere vecchie versioni di Odoo (precedenti alla 10.0).

