============================================================
|icon| Universal Connector/Connettore universale 12.0.1.3.16
============================================================

**Universal Connector complete suite**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/universal_connector/static/description/icon.png


.. contents::



Overview | Panoramica
=====================

|en| This module is Universal Connector suite. Itself does nothing, it is a bunch of all Universal Connector modules.
For furthemore info read documentation of specific modules.

Suite Characteristics
~~~~~~~~~~~~~~~~~~~~~

* Multi-backend interchange
* Multi-protocols, like JSON, XMLRPC and CSV
* Push and/or Pull logic
* Many2one, One2Many and Many2Many acquired with remote references
* Recognition by external reference (only remote Odoo)
* Updatable configuration by GUI
* Anti-recurse checks
* Create in two phases in order to keep hierarchical record structure
* Dynamic database migration for Odoo since 6.1
* Configurable protection rules

This suit can be used for:

* **Migrate Odoo Database** from a version to another version (like openupgrade but even back upgrade)
* **Import data** from files in specific location using user configuration (alternative to standard import)
* **Create demo and test environment** based on csv files
* **Connect just in time** Odoo with other software or other Odoo instances
* **Populate database from another dataset** when Odoo replace another software
* **Interchange Support Centre** to manage interactive EDI with couterparties


|it| Questo modulo è la suite Universal Connector. Di per sé non fa nulla, è un insieme
di tutti i moduli Universal Connector. Per ulteriori informazioni,
leggere la documentazione dei moduli specifici.

Caratteristiche della suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Scambio multi-dorsale
* Multi-protocollo, come JSON, XMLRPC e CSV
* Logica push e/o pull
* Many2one, One2Many e Many2Many acquisiti con riferimenti remoti
* Riconoscimento tramite riferimento esterno (solo Odoo remoto)
* Configurazione aggiornabile tramite GUI
* Controlli anti-ricorsione
* Creazione a due fasi per mantenere la struttura gerarchica dei record
* Migrazione dinamica del database per Odoo dalla versione 6.1
* Regole di protezione configurabili

Questa suite può essere utilizzata per:

* **Migrare il database Odoo** da una versione a un'altra versione (come openupgrade ma anche all'indietro)
* **Importare dati** da file in una posizione specifica utilizzando la configurazione utente (alternativa all'importazione standard)
* **Creare un ambiente demo e di test** basato su file csv
* **Connettersi in tempo reale** Odoo con altri software o altre istanze Odoo
* **Popolare il database da un altro set di dati** quando Odoo sostituisce un altro software
* **Centro di supporto per lo scambio** per gestire EDI interattivo con le controparti


|thumbnail|

.. |thumbnail| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/universal_connector/static/description/description.gif


Configuration | Configurazione
------------------------------

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



Usage | Utilizzo
----------------

If you want comunicate with Odoo form remote you can use 2 functions:

* ``ir.model.synchro.trigger_one_record(ext_model, prefix, ext_id)``
* ``odoo_model.synchro(vals)``

All the functions return the ID of record found or created. Negative values are error codes.

synchro
~~~~~~~

The function synchro accepts a data dictionary with field values, like RPC create
and RPC write functions.

Every field name may be:

* ``id`` (integer): the Odoo ID of record, supplied if write specific existent record
* ``PFX_id`` (integer): the external partner ID of record (PFX is the backend prefix)
* External name as format ``"PFX:FIELD"`` where PFX is the backend prefix and ``FIELD``
is the external name which is converted into Odoo name and value, based on backend
configuration.

Synchronizer behavior:

* If ``PFX_id`` field is supplied, record with ``PFX_id`` is searched
* Otherwise Synchronizer search for a record matching values passed; the function execute a fallback search algorithm
* If record found, Synchronizer executes the Odoo function write
* If record not found, Synchronizer executes the Odoo function create and assign external 'id' to ``PFX_id``


trigger_one_recod
~~~~~~~~~~~~~~~~~

This function may be used if counterparty make available an interface to read record.
This is automatic (with JSON-RPC and XML-RPC) for Odoo remote instances.
Other software must publish the interchange interface
like `Swagger <https://swagger.io/>`__
Swagger is avaialable on Odoo too, example `Swagger for Odoo <https://github.com/ychirino/openapi>`__
and `Odoo REST framework <https://github.com/OCA/rest-framework>`__
For furthermore info read `Generate swagger yaml from route methods <https://www.odoo.com/it_IT/forum/assistenza-1/generate-swagger-yaml-from-route-methods-192911>`__



Getting started | Primi passi
=============================

|Try Me|


Prerequisites | Prerequisiti
----------------------------

* python 3.7
* postgresql 9.6+ (best 10.0+)

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
| $HOME/12.0 |
+----------------------------------------------------------------------------+

::

    # Odoo repository installation; OCB repository must be installed
    deploy_odoo clone -r connector -b 12.0 -G zero -p $HOME/12.0
    # Upgrade virtual environment
    vem amend $HOME/12.0/venv_odoo



Upgrade | Aggiornamento
-----------------------

::

    deploy_odoo update -r connector -b 12.0 -G zero -p $HOME/12.0
    vem amend $HOME/12.0/venv_odoo
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

12.0.1.3.17 (2025-06-06)
~~~~~~~~~~~~~~~~~~~~~~~~

* [QUA]

12.0.0.3.16 (2025-06-02)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] New improvements of modules / Migliorie dei singoli moduli

12.0.0.3.14 (2025-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] New improvements of modules / Migliorie dei singoli moduli
* [IMP] synchro parameters
* [IMP] cache management
* [IMP] virtual model are deprecated
* [IMP] Protocol model
* [IMP] Identity model
* [QUA] Test coverage 80% (2330: 455+1875) [244 TestPoints] - quality rating 66 (target 100)

12.0.0.3.13 (2025-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] New improvements of modules / Migliorie dei singoli moduli
* [QUA] Test coverage 80% (2330: 455+1875) [244 TestPoints] - quality rating 66 (target 100)

12.0.0.3.12 (2025-01-03)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] New improvements of modules / Migliorie dei singoli moduli
* [QUA] Test coverage 80% (2330: 455+1875) [244 TestPoints] - quality rating 66 (target 100)

12.0.0.3.11 (2024-12-29)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Full refactoring: most functions moved in specific modules
* [IMP] New tests / Nuovi test
* [QUA] Test coverage 80% (2256: 453+1803) [244 TestPoints] - quality rating 66 (target 100)

12.0.0.3.10 (2024-11-16)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Minor aesthetic update
* [QUA] Test coverage 28% (3919: 2836+1083) [20 TestPoints] - quality rating 18 (target 100)

12.0.0.3.9 (2024-08-10)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Import person from vg7
* [IMP] Some internal field renamed
* [QUA] Test coverage 64% (5068: 1832+3236) [1376 TestPoints] - quality rating 82 (target 100)

12.0.0.3.8 (2024-07-01)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Search for shipping and invoice addresses / Migliorie ricerca indirizzi di spedizione e fatturazione
* [FIX] Tax, account, uom in order lines / IVA, conto e um nelle righe ordini
* [FIX] Flag is_company in res.partner / Indicatore azienda in nominativi
* [IMP] uom from vg7 purchase orders
* [QUA] Test coverage 64% (5084: 1855+3229) [1253 TestPoints] - quality rating 78 (target 100)

12.0.0.3.7 (2024-06-27)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] apply date/time functions
* [FIX] Purchase orders
* [IMP] Test on vg7 suppliers
* [QUA] Test coverage 43% (5092: 2879+2213) [1189 TestPoints] - quality rating 64 (target 100)

12.0.0.3.6 (2024-06-24)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Double function after import
* [FIX] No reset search keys
* [FIX] Many2one fields from old Odoo with multiple matches
* [IMP] Imported cvs/Excel: fields with None or \N are ignored
* [IMP] Double product description and name / Descrizione prodotto doppia
* [QUA] Test coverage 42% (5031: 2908+2123) [1051 TestPoints] - quality rating 59 (target 100)

12.0.0.3.5 (2024-06-20)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] This is the 1.st application with 1000+ test points!
* [FIX] No price with VAT from VF7 order / Prezzo ordine VG7 senza scorporo IVA
* [QUA] Test coverage 33% (4993: 3342+1651) [1037 TestPoints] - quality rating 54 (target 100)



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

Last Update / Ultimo aggiornamento: 2025-06-10

.. |Maturity| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: 
.. |license gpl| image:: https://img.shields.io/badge/licence-LGPL--3-7379c3.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |license opl| image:: https://img.shields.io/badge/licence-OPL-7379c3.svg
    :target: https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html
    :alt: License: OPL
.. |Try Me| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-try-it-12.svg
    :target: https://erp12.zeroincombenze.it
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
