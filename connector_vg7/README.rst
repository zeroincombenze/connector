
===============================
|icon| connector_vg7 10.0.0.2.1
===============================


**Connector to/from VG7 software**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/connector/10.0/connector_vg7/static/description/icon.png

|Maturity| |Build Status| |Codecov Status| |license gpl| |Try Me|


.. contents::


Overview / Panoramica
=====================

|en| This module makes available some functions to synchronize external data
with Odoo data.

Characteristics
~~~~~~~~~~~~~~~

* Multi-channels interchange
* JSON, XMLRPC and CSV files protocols
* Push and/or Pull logic
* Many2one, One2Many and Many2Many managed with external references
* Automatic field value translation
* Odoo version from 6.1 to 12.0 field name and values automatic translation
* Anti-recurse checks
* Two phases create in order to create hierarchical record structure
* Dynamic translation database

This module can be used for:

* Upgrade Odoo DB from a version to another version (even beck upgrade)
* Import data from files without duplicating records
* Connect Odoo with other software (current version supports until 4 counterparts)
* Populate Odoo DB in the first installation migrated from another software


Synchro
~~~~~~~

The function synchro return the ID of record found or created. Negative values
are error codes.

The function synchro accepts a data dictionary with field values, like create
and write functions.

Every field name may be:

* `id` (integer): the Odoo ID of record; if supplied means write specific existent record (deprecated)
* `PFX_id` (integer): the external partner ID of record (PFX is the channel prefix)
* External name as format `PFX:FIELD` where PFX is the channel prefix and FIELD is the external name which is translated into Odoo name based on dictionary

Every field value may be:

* Value as is, i.e. partner name; the value is acquired as is
* External references: ID of external reference
* Text of reference: key of reference key, i.e. "admin" in user_id field

Synchronizer behavior:

* If `PFX_id` field is supplied, record with `PFX_id` is searched
* Otherwise Synchronizer search for a record matching values passed; the function execute a fallback search algorithm
* If record found, Synchronizer executes the Odoo function write
* If record not found, Synchronizer executes the Odoo function create and assign external 'id' to `PFX_id`


|

|it| Connettore con VG7

Questo modulo rende disponibile alucne funzioni per sincronizzare con l'esterno.

Caratteristiche
~~~~~~~~~~~~~~~

* Scambio multi-canale
* Protocolli JSON, XMLRPC e file CSV
* Logica Push o Pull
* Many2one, One2Many e Many2Many gestiti con referenze esterne
* Traduzione automatica dei campi
* Traduzione automatica dei campi e dei valori di Odoo dalla 6.1 alla 12.0
* Controllo anti-ricorsione
* Creazione a due fasi
* Traduttore dinamico

Questo modulo può essere usato per:

* Aggiornare database di Odoo tra versioni (anche all'indietro)
* Importare dati da file senza duplicazioni
* Connettere Odoo con altri software (sino a 4 contemporaneamente)
* Popolare il DB di Odoo nella prima installazione quando migrazione da altro software


|

OCA comparation / Confronto con OCA
-----------------------------------


+-----------------------------------------------------------------+-------------------+----------------+--------------------------------+
| Description / Descrizione                                       | Zeroincombenze    | OCA            | Notes / Note                   |
+-----------------------------------------------------------------+-------------------+----------------+--------------------------------+
| Coverage / Copertura test                                       |  |Codecov Status| | |OCA Codecov|  |                                |
+-----------------------------------------------------------------+-------------------+----------------+--------------------------------+


|
|

Getting started / Come iniziare
===============================

|Try Me|


|

Installation / Installazione
----------------------------


+---------------------------------+------------------------------------------+
| |en|                            | |it|                                     |
+---------------------------------+------------------------------------------+
| These instructions are just an  | Istruzioni di esempio valide solo per    |
| example; use on Linux CentOS 7+ | distribuzioni Linux CentOS 7+,           |
| Ubuntu 14+ and Debian 8+        | Ubuntu 14+ e Debian 8+                   |
|                                 |                                          |
| Installation is built with:     | L'installazione è costruita con:         |
+---------------------------------+------------------------------------------+
| `Zeroincombenze Tools <https://zeroincombenze-tools.readthedocs.io/>`__    |
+---------------------------------+------------------------------------------+
| Suggested deployment is:        | Posizione suggerita per l'installazione: |
+---------------------------------+------------------------------------------+
| $HOME/10.0                                                                 |
+----------------------------------------------------------------------------+

::

    cd $HOME
    # *** Tools installation & activation ***
    # Case 1: you have not installed zeroincombenze tools
    git clone https://github.com/zeroincombenze/tools.git
    cd $HOME/tools
    ./install_tools.sh -p
    source $HOME/devel/activate_tools
    # Case 2: you have already installed zeroincombenze tools
    cd $HOME/tools
    ./install_tools.sh -U
    source $HOME/devel/activate_tools
    # *** End of tools installation or upgrade ***
    # Odoo repository installation; OCB repository must be installed
    odoo_install_repository connector -b 10.0 -O zero -o $HOME/10.0
    vem create $HOME/10.0/venv_odoo -O 10.0 -a "*" -DI -o $HOME/10.0

From UI: go to:

* |menu| Setting > Activate Developer mode 
* |menu| Apps > Update Apps List
* |menu| Setting > Apps |right_do| Select **connector_vg7** > Install


|

Upgrade / Aggiornamento
-----------------------


::

    cd $HOME
    # *** Tools installation & activation ***
    # Case 1: you have not installed zeroincombenze tools
    git clone https://github.com/zeroincombenze/tools.git
    cd $HOME/tools
    ./install_tools.sh -p
    source $HOME/devel/activate_tools
    # Case 2: you have already installed zeroincombenze tools
    cd $HOME/tools
    ./install_tools.sh -U
    source $HOME/devel/activate_tools
    # *** End of tools installation or upgrade ***
    # Odoo repository upgrade
    odoo_install_repository connector -b 10.0 -o $HOME/10.0 -U
    vem amend $HOME/10.0/venv_odoo -o $HOME/10.0
    # Adjust following statements as per your system
    sudo systemctl restart odoo

From UI: go to:

* |menu| Setting > Activate Developer mode
* |menu| Apps > Update Apps List
* |menu| Setting > Apps |right_do| Select **connector_vg7** > Update

|

Support / Supporto
------------------


|Zeroincombenze| This module is maintained by the `SHS-AV s.r.l. <https://www.zeroincombenze.it/>`__


|
|

Get involved / Ci mettiamo in gioco
===================================

Bug reports are welcome! You can use the issue tracker to report bugs,
and/or submit pull requests on `GitHub Issues
<https://github.com/zeroincombenze/connector/issues>`_.

In case of trouble, please check there if your issue has already been reported.

Proposals for enhancement
-------------------------


|en| If you have a proposal to change this module, you may want to send an email to <cc@shs-av.com> for initial feedback.
An Enhancement Proposal may be submitted if your idea gains ground.

|it| Se hai proposte per migliorare questo modulo, puoi inviare una mail a <cc@shs-av.com> per un iniziale contatto.

ChangeLog History / Cronologia modifiche
----------------------------------------

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


|
|

Credits / Didascalie
====================

Copyright
---------

Odoo is a trademark of `Odoo S.A. <https://www.odoo.com/>`__ (formerly OpenERP)



|

Authors / Autori
----------------

* `SHS-AV s.r.l. <https://www.zeroincombenze.it/>`__


Contributors / Collaboratori
----------------------------

* Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>


Maintainer / Manutenzione
-------------------------




|

----------------


|en| **zeroincombenze®** is a trademark of `SHS-AV s.r.l. <https://www.shs-av.com/>`__
which distributes and promotes ready-to-use **Odoo** on own cloud infrastructure.
`Zeroincombenze® distribution of Odoo <https://wiki.zeroincombenze.org/en/Odoo>`__
is mainly designed to cover Italian law and markeplace.

|it| **zeroincombenze®** è un marchio registrato da `SHS-AV s.r.l. <https://www.shs-av.com/>`__
che distribuisce e promuove **Odoo** pronto all'uso sulla propria infrastuttura.
La distribuzione `Zeroincombenze® <https://wiki.zeroincombenze.org/en/Odoo>`__ è progettata per le esigenze del mercato italiano.


|chat_with_us|


|

This module is part of connector project.

Last Update / Ultimo aggiornamento: 2020-12-10

.. |Maturity| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |Build Status| image:: https://travis-ci.org/zeroincombenze/connector.svg?branch=10.0
    :target: https://travis-ci.org/zeroincombenze/connector
    :alt: github.com
.. |license gpl| image:: https://img.shields.io/badge/licence-LGPL--3-7379c3.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |license opl| image:: https://img.shields.io/badge/licence-OPL-7379c3.svg
    :target: https://www.odoo.com/documentation/user/9.0/legal/licenses/licenses.html
    :alt: License: OPL
.. |Coverage Status| image:: https://coveralls.io/repos/github/zeroincombenze/connector/badge.svg?branch=10.0
    :target: https://coveralls.io/github/zeroincombenze/connector?branch=10.0
    :alt: Coverage
.. |Codecov Status| image:: https://codecov.io/gh/zeroincombenze/connector/branch/10.0/graph/badge.svg
    :target: https://codecov.io/gh/zeroincombenze/connector/branch/10.0
    :alt: Codecov
.. |Tech Doc| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-docs-10.svg
    :target: https://wiki.zeroincombenze.org/en/Odoo/10.0/dev
    :alt: Technical Documentation
.. |Help| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-help-10.svg
    :target: https://wiki.zeroincombenze.org/it/Odoo/10.0/man
    :alt: Technical Documentation
.. |Try Me| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-try-it-10.svg
    :target: https://erp10.zeroincombenze.it
    :alt: Try Me
.. |OCA Codecov| image:: https://codecov.io/gh/OCA/connector/branch/10.0/graph/badge.svg
    :target: https://codecov.io/gh/OCA/connector/branch/10.0
    :alt: Codecov
.. |Odoo Italia Associazione| image:: https://www.odoo-italia.org/images/Immagini/Odoo%20Italia%20-%20126x56.png
   :target: https://odoo-italia.org
   :alt: Odoo Italia Associazione
.. |Zeroincombenze| image:: https://avatars0.githubusercontent.com/u/6972555?s=460&v=4
   :target: https://www.zeroincombenze.it/
   :alt: Zeroincombenze
.. |en| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/flags/en_US.png
   :target: https://www.facebook.com/Zeroincombenze-Software-gestionale-online-249494305219415/
.. |it| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/flags/it_IT.png
   :target: https://www.facebook.com/Zeroincombenze-Software-gestionale-online-249494305219415/
.. |check| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/check.png
.. |no_check| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/no_check.png
.. |menu| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/menu.png
.. |right_do| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/right_do.png
.. |exclamation| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/exclamation.png
.. |warning| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/warning.png
.. |same| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/same.png
.. |late| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/late.png
.. |halt| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/halt.png
.. |info| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/info.png
.. |xml_schema| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/iso/icons/xml-schema.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/iso/scope/xml-schema.md
.. |DesktopTelematico| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/ade/icons/DesktopTelematico.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/ade/scope/Desktoptelematico.md
.. |FatturaPA| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/ade/icons/fatturapa.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/ade/scope/fatturapa.md
.. |chat_with_us| image:: https://www.shs-av.com/wp-content/chat_with_us.gif
   :target: https://t.me/axitec_helpdesk

