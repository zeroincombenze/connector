☰ Configurazione > Attivare la modalità sviluppatore

☰ Configurazione > Funzioni tecniche > Dorsale di sincronizzazione

#. Impostare il protocollo "By xmlrpc over https" o "By xmlrpc over http" or altro
#. Impostare nome host, se necessario (per xmlrpc over http impostare endpoint)
#. Impostare porta di comunicazione, se necessario
#. Dichiarare nome database remoto, se necessario
#. Dichiarare nome utente remoto e password (la password non è visibile)
#. Per alcuni protocolli è richiesta una Client Key al posto della password
#. Dichiarare identità
#. Dichiarare la versione remota, se necessario
#. Scegliere il prefisso per questa dorsale
#. Dichiarare la lingua usata da utente remoto
#. Impostare Endpoint, se necessario (richiesto per xmlrpc over http)
#. Fare click su bottone [Verificare Connessione]

Se Odoo riesce a connettersi con controparte, lo stato della dorsale diventa "Pronto".

I parametri dipendono dal tipo di protocollo utilizzato e dall'indenità remota. Qui a
sequito una breve lista dei più comuni.

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

Leggere info dal modulo *universal_connector_by_http*

**jsonrpc**

Leggere info dal modulo *universal_connector_by_json*

**xmlrpc**

Leggere info dal modulo *universal_connector_by_xmlrpc*

**csv**

Leggere info dal modulo *universal_connector_by_jcsv*