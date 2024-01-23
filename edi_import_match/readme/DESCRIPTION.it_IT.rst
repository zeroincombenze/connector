Cosa è
------

Questo modulo, ispirato al moduleo OCA `Base Import Match <https://github.com/OCA/server-backend/tree/12.0/base_import_match>`__,
permette di aggiungere regole aggiuntive per combaciare se un record
è da modificare o da creare.

Destinatari
-----------

Questo modulo è utilizzabile da chi deve importare dati con regole evolute.

Perché
------

Quando si importa dati (esempio un CSV) con il modulo standard di Odoo *base_import*,
sono applicate solo 2 regole:

* Se presente XMLID esegue un **aggiornamento**.
* Altrimenti esegue la **creazione** di un nuovo record

Queste regole sono troppo semplici e i dati sono duplicati se il file è importato più
volte.

Questo modulo evita le duplicazioni.

Come
----

L'utente può creare proprie regole di riconoscimento record.
