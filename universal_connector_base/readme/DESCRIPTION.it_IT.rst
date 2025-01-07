Questo modulo è base della suite Universal Connector e rende disponibile alcune
funzioni per sincronizzare con l'esterno.

Il protocollo utilizzato è "xmlrpc su http/https", chiamato XML-RPC, che è implementato
da `python client xmlrpc <https://docs.python.org/3/library/xmlrpc.client.html>`__,
quindi non è necessario installare alcun pacchetto. Questo protocollo è più semplice di
REST e SOAP per progettazione.

Il tipico endpoint per accedere all'istanza remota di Odoo dovrebbe essere "https://admin@localhost:8069"
e l'autenticazione è basata su nome utente/password.

I modelli sincronizzabili sono:

* Azienda (res.company)
* Nazione (res.country and res.country.state)
* Divisa (res.currency and res.currency.rate)
* Lingua (res.lang)
* Nominativo (res.partner and res.partner.category)
* Utente (res.users and res.groups)

Questo modulo può sincronizzare Odoo dalla versione 8.0 alle 18.0.
Per versioni precedenti è disponibile il modulo *universal_connector_openerp*