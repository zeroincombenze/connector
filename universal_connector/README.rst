============================================================
|icon| Universal Connector/Connettore universale 10.0.0.3.14
============================================================

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/connector/10.0/universal_connector/static/description/icon.png


.. contents::



Overview | Panoramica
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


|it| Questo modulo rende disponibile alucne funzioni per sincronizzare con l'esterno.

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


|thumbnail|

.. |thumbnail| image:: https://raw.githubusercontent.com/zeroincombenze/connector/10.0/universal_connector/static/description/


Getting started | Primi passi
=============================

|Try Me|


Prerequisites | Prerequisiti
----------------------------

* python 2.7+ (best 2.7.5+)
* postgresql 9.2+ (best 9.5)

::

    cd $HOME
    # Follow statements activate deployment, installation and upgrade tools
    cd $HOME
    [[ ! -d ./tools ]] && git clone https://github.com/zeroincombenze/tools.git
    cd ./tools
    ./install_tools.sh -pUT
    source $HOME/devel/activate_tools



Installation | Installazione
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
| `Zeroincombenze Tools <https://zeroincombenze-tools.readthedocs.io/>`__ |
+---------------------------------+------------------------------------------+
| Suggested deployment is:        | Posizione suggerita per l'installazione: |
+---------------------------------+------------------------------------------+
| $HOME/10.0 |
+----------------------------------------------------------------------------+

::

    # Odoo repository installation; OCB repository must be installed
    deploy_odoo clone -r connector -b 10.0 -G zero -p $HOME/10.0
    # Upgrade virtual environment
    vem amend $HOME/10.0/venv_odoo



Upgrade | Aggiornamento
-----------------------

::

    deploy_odoo update -r connector -b 10.0 -G zero -p $HOME/10.0
    vem amend $HOME/10.0/venv_odoo
    # Adjust following statements as per your system
    sudo systemctl restart odoo



Support | Supporto
------------------

|Zeroincombenze| This module is supported by the `SHS-AV s.r.l. <https://www.zeroincombenze.it/>`__



Get involved | Ci mettiamo in gioco
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



ChangeLog History | Cronologia modifiche
----------------------------------------

10.0.0.3.14 (2026-03-19)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Import new product from VG7 / Import nuovi prodotti da VG7
* [FIX] Import res.partner.bank
* [IMP] Weight in sale.order.line
* [QUA] Test coverage 60% (5019: 1997+3022) [560 TestPoints]

10.0.0.3.13 (2025-07-31)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Import new product from VG7 / Import nuovi prodotti da VG7
* [QUA] Test coverage 64% (5066: 1822+3244) [1376 TestPoints] - quality rating 82 (target 100)

10.0.0.3.12 (2025-03-14)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Import partner w/o vat and fiscalcode / Import nominativo senza CF e PI
* [QUA] Test coverage 64% (5061: 1827+3234) [1376 TestPoints] - quality rating 82 (target 100)

10.0.0.3.11 (2025-03-10)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Minor aesthetic update
* [QUA] Test coverage 64% (5068: 1832+3236) [1376 TestPoints] - quality rating 82 (target 100)
 
10.0.0.3.10 (2025-03-10)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Minor aesthetic update
* [QUA] Test coverage 64% (5068: 1832+3236) [1376 TestPoints] - quality rating 82 (target 100)

10.0.0.3.9 (2024-08-10)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Import person from vg7
* [IMP] Some internal field renamed
* [QUA] Test coverage 64% (5068: 1832+3236) [1376 TestPoints] - quality rating 82 (target 100)

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



Credits | Ringraziamenti
========================

Copyright
---------

Odoo is a trademark of `Odoo S.A. <https://www.odoo.com/>`__ (formerly OpenERP)


Authors | Autori
----------------

* `SHS-AV s.r.l. <https://www.zeroincombenze.it>`__



Contributors | Partecipanti
---------------------------

* `Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>`__



Maintainer | Manutenzione
-------------------------

* `Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>`__



----------------

|en| **zeroincombenze®** is a trademark of `SHS-AV s.r.l. <https://www.shs-av.com/>`__
which distributes and promotes ready-to-use **Odoo** on own cloud infrastructure.
`Zeroincombenze® distribution of Odoo <https://www.zeroincombenze.it/>`__
is mainly designed to cover Italian law and markeplace.

|it| **zeroincombenze®** è un marchio registrato da `SHS-AV s.r.l. <https://www.shs-av.com/>`__
che distribuisce e promuove **Odoo** pronto all'uso sulla propria infrastuttura.
La distribuzione `Zeroincombenze® <https://www.zeroincombenze.it/>`__ è progettata per le esigenze del mercato italiano.


|
|

This module is part of connector project.

Last Update / Ultimo aggiornamento: 2026-03-21

.. |Maturity| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: 
.. |license gpl| image:: https://img.shields.io/badge/licence-LGPL--3-7379c3.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |license opl| image:: https://img.shields.io/badge/licence-OPL-7379c3.svg
    :target: https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html
    :alt: License: OPL
.. |Try Me| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-try-it-10.svg
    :target: https://erp10.zeroincombenze.it
    :alt: Try Me
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
