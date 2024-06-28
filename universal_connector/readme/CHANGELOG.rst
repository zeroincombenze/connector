10.0.0.3.8 (2024-07-01)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Search for shipping and invoice addresses / Migliorie ricerca indirizzi di spedizione e fatturazione
* [FIX] Tax, account, uom in order lines / IVA, conto e um nelle righe ordini
* [FIX] Flag is_company in res.partner / Indicatore azienda in nominativi
* [IMP] uom from vg7 purchase orders
* [QUA] Test coverage 64% (5084: 1855+3229) [1253 TestPoints] - quality rating 78 (target 100)

10.0.0.3.7 (2024-06-27)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] apply date/time functions
* [FIX] Purchase orders
* [IMP] Test on vg7 suppliers
* [QUA] Test coverage 43% (5092: 2879+2213) [1189 TestPoints] - quality rating 64 (target 100)

10.0.0.3.6 (2024-06-24)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Double function after import
* [FIX] No reset search keys
* [FIX] Many2one fields from old Odoo with multiple matches
* [IMP] Imported cvs/Excel: fields with None or \N are ignored
* [IMP] Double product description and name / Descrizione prodotto doppia
* [QUA] Test coverage 42% (5031: 2908+2123) [1051 TestPoints] - quality rating 59 (target 100)

10.0.0.3.5 (2024-06-20)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] This is the 1.st application with 1000+ test points!
* [FIX] No price with VAT from VF7 order / Prezzo ordine VG7 senza scorporo IVA
* [QUA] Test coverage 33% (4993: 3342+1651) [1037 TestPoints] - quality rating 54 (target 100)

10.0.0.3.4 (2024-06-19)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Model res.lang
* [FIX] Model account.payment.term
* [FIX] Automatic reset -9 status
* [FIX] Search tax by amount only if amount > 0
* [IMP] Minor improvements: only minimal data is the default
* [IMP] Model with sequences get data even if > 16 records
* [IMP] Casting improvements
* [IMP] New versioned dependency control
* [REF] New concurrent tests
* [IMP] Test trace "why"
* [QUA] Test coverage 32% (4993: 3373+1620) [1005 TestPoints] - quality rating 52 (target 100)

10.0.0.3.3 (2023-10-31)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Unit price without tax / Scorporo IVA
* [QUA] Test coverage 45% (4960: 2735+2225) [6 TestPoints] - quality rating 1336 (target 100)

10.0.0.3.2 (2023-03-02)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Pull records sto last remote pulled record id
* [FIX] Excel backend with connected test

10.0.0.3.1 (2023-02-26)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Ignore Odoo counterpart fields do not exist in local
* [FIX] Wrong error messages

10.0.0.2.9 (2022-07-27)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Enhanced search

10.0.0.2.8 (2022-07-18)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Partner: check for parent_id / Controlli su import clienti

10.0.0.2.7 (2022-03-18)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Purchase orders / Ordini a fornitore

10.0.0.2.6 (2021-03-08)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Wrong error -9
* [IMP] UI log message on synchro entry

10.0.0.2.5 (2021-02-24)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] note + weight in ddt header from vg7

10.0.0.2.4 (2021-02-14)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] account.account import
* [FIX] json import
* [FIX] import float & monetary value from csv
* [FIX] import vg7 ddt by trigger

10.0.0.2.3 (2020-12-27)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] type_name error

10.0.0.2.2 (2020-12-17)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Index error

10.0.0.2.1 (2020-11-30)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Better ancillary keys management / Miglioramento gestione delle chiavi ausiliarie

10.0.0.2.0 (2020-11-30)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Partner without vat / Soggetto senza partita IVA
* [IMP] Default tax type is 'sale' / Tipo codice IVA predefinito è 'vendita'
* [IMP] Cache time-out changes / Modifica time-out di cache
* [IMP] Supplemental keys / Chiavi di ricerca supplementari
* [IMP] Langugae import / Importazione basato su lingua utente
* [IMP] Odoo import store DB structure / Importazione da Odoo crea struttura
* [IMP] Ancillary keys management / Gestione delle chiavi ausiliarie
* [IMP] Automatic keys recognize / Riconoscimento automatico delle chiavi

10.0.0.1.46 (2020-10-20)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Import PO / Importazione ordini di acquisto


10.0.0.1.45 (2020-10-14)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Complete workflow if SO in draft / Completa workflow se ordine in bozza


10.0.0.1.44 (2020-09-27)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] New external ID model / Nuovo modello per external ID


10.0.0.1.43 (2020-08-08)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Report child error / Segnala errore nei record figli
* [IMP] Purchase order / Ordini a fornitore
* [FIX] Sometimes error -6 from vg7 client / Errore casuale -6 con client vg7
* [FIX] Import new users / Importazione nuovi utenti


10.0.0.1.42 (2020-08-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Unit price in min invoice line / Prezzo unitario in riga fattura minima


10.0.0.1.41 (2020-08-29)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Avoid recurse / Controllo anti-ricorsione


10.0.0.1.40 (2020-08-23)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Show Workflow model / Mostra modello workflow corrente


10.0.0.1.39 (2020-08-11)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Install just installed modules / Installazione solo di moduli installati


10.0.0.1.38 (2020-08-06)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Full import DB / Funzione importazione DB completo
* [FIX] Crash with some tomany fields / Strano crash con campi tomany
* [FIX] Wrong paid state invoice / Stato fattura pagato
* [IMP] Minimal values + No deep + remote_ids / Opzioni valori minimi + No livelli + ID remoti


10.0.0.1.37 (2020-08-01)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Crash with unmanaged tables / Crash con tabelle non gestite


10.0.0.1.36 (2020-07-24)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Ignore partner.user_ids / Ignora partner.user_ids


10.0.0.1.35 (2020-06-18)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Sync with odoo partner / Sincronizzazione con partner odoo
* [IMP] Data value in error log / Dati passati in log errori


10.0.0.1.34 (2020-05-25)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Sync with model w/o odoo id / Sincronizzazione con modelle senza ID odoo
* [IMP] Transaction log / Registro transazioni
* [IMP] Partner record timestamp & error message / Data, ora e messaggio di errore in record soggetti


10.0.0.1.33 (2020-05-11)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Burst writing / Scritture ripetute in sequenza


10.0.0.1.31 (2020-04-14)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Banks / Conti bancari


10.0.0.1.30 (2020-04-10)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Account invoice / Fatture
* [FIX] Payment term / Termini di pagamento


10.0.0.1.29 (2020-04-07)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Sale order / Ordini di vendita


10.0.0.1.28 (2020-04-06)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Product category / Categoria prodotto


10.0.0.1.27 (2020-03-20)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Import country_id / Importazione nazione


10.0.0.1.26 (2020-03-11)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Many patches / Varie migliorie


10.0.0.1.17 (2020-01-19)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Avoid recursive infinite loop / Controllo per evitare cicli ricorsivi infiniti


10.0.0.1.16 (2020-01-18)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] New search algorithm / Nuovo agloritmo di ricerca


10.0.0.1.15 (2020-01-07)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Import banks / Importazione c/c bancari


10.0.0.1.14 (2020-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Import supplier / Importazione fornitori
* [IMP] Send/Receive method / Metodo di invio/ricezione dati


10.0.0.1.13 (2020-01-02)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Improvements / Migliorie varie e protezione contro bug VG7


10.0.0.1.12 (2019-12-30)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Protect against wrong id in invoice lines / Protezione contro ID non validi in dettaglio fatture
* [IMP] Protect against wrong id in sale order lines / Protezione contro ID non validi in dettaglio ordini
* [IMP] Import from file csv / Importazione da file csv
* [IMP] Import address record / Importazioni indirizzi di spedizione e fatturazione
* [IMP] Synchronizzation button on parters and products / Bottone di sincronizzazione in soggetti e prodotti
* [IMP] Import uom / Importazione um


10.0.0.1.11 (2019-12-03)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Partner minor fixes / Problemi minori clienti
* [IMP] Delivery document import / Importazione DdT


10.0.0.1.10 (2019-11-11)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Parse id of vg7_response function / Validazione id funzione vg7_response
* [FIX] Field with olny space are ingnored / I campi di soli spazi sono ignorati
* [FIX] Log error whene invalid state change / Segnala errore in caso di cambio stato non valido
* [IMP] Customer manages addressess / L'importazione dei clienti gestisce gli indirizzi


10.0.0.1.9 (2019-10-14)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Not() function applied only to ext. ref. / La funzione not() è applicata solo se nome esterno


10.0.0.1.8 (2019-10-09)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Account Payment Term / Tabella termini di pagamento
* [IMP] New protection level / Nuovo livello di protezione
