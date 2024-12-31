Per comunicare con Odoo da remoto è possibile usare 2 funzioni:

* ``ir.model.synchro.trigger_one_record(ext_model, prefix, ext_id)``
* ``odoo_model.synchro(vals)``

Tutte le funzioni restituiscono l'ID del record trovato o creato.
I valori negativi sono codici di errore.

synchro
~~~~~~~

La funzione synchro accetta un dizionario dati con valori di campo, come le funzioni
RPC create e RPC write.

Ogni nome di campo può essere:

* ``id`` (intero): l'ID Odoo del record, fornito se si scrive uno specifico record esistente
* ``PFX_id`` (intero): l'ID partner esterno del record (PFX è il prefisso della dorsale)
* Nome esterno nel formato ``"PFX:FIELD"`` dove PFX è il prefisso dorsale e ``FIELD``
è il nome esterno che viene convertito nel nome e nel valore Odoo, in base alla configurazione della dorsale.

Comportamento del sincronizzatore:

* Se viene fornito il campo ``PFX_id``, viene ricercato il record con ``PFX_id``
* Altrimenti, il sincronizzatore cerca un record corrispondente ai valori passati; la funzione esegue un algoritmo di ricerca di fallback
* Se il record è stato trovato, Synchronizer esegue la funzione Odoo write
* Se il record non è stato trovato, Synchronizer esegue la funzione Odoo create e assegna un 'id' esterno a ``PFX_id``

trigger_one_recod
~~~~~~~~~~~~~~~~~~

Questa funzione può essere utilizzata se la controparte rende disponibile un'interfaccia per leggere i record.
Questo è automatico (con JSON-RPC e XML-RPC) per le istanze remote di Odoo. Altri software devono pubblicare
l'interfaccia di interscambio come `Swagger <https://swagger.io/>`__
Swagger è disponibile anche su Odoo, ad esempio `Swagger per Odoo <https://github.com/ychirino/openapi>`__
e `Odoo REST framework <https://github.com/OCA/rest-framework>`__
Per ulteriori informazioni leggere `Genera swagger yaml da metodi di route <https://www.odoo.com/it_IT/forum/assistenza-1/genera-swagger-yaml-da-metodi-di-route-192911>`__
