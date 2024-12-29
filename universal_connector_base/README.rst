======================================================================
|icon| Universal Connector Base/Base connettore universale 12.0.0.3.11
======================================================================

**Basic features for Universal Connector**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/universal_connector_base/static/description/icon.png


.. contents::



Overview | Panoramica
=====================

|en| This module is base for Universal Connector suite and makes available some functions
to synchronize external data with Odoo data.

Site Characteristics
~~~~~~~~~~~~~~~~~~~~

* Multi-backend interchange
* Multi-protocols, like JSON, XMLRPC and CSV
* Push and/or Pull logic
* Many2one, One2Many and Many2Many acquired with remote references
* Recognition by external reference (only remote Odoo)
* Updatable configuration by GUI
* Anti-recurse checks
* Two phases create in order to create hierarchical record structure
* Dynamic database migration for Odoo since 6.1

This module can be used for:

* Migrate Odoo DB from a version to another version, like openupgrade, (even back upgrade)
* Import data from files in specific location using user configuration
* Create demo and test environment based on csv files
* Connect just in time Odoo with other software or other Odoo instnces
* Populate database when Oddo requires to migrate from another software


|it| Questo modulo è base della suite Universal Connector e rende disponibile alcune
funzioni per sincronizzare con l'esterno.

Caratteristiche della suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Scambio multi-dorsale
* Multi-protocollo come JSON, XMLRPC e CSV
* Logica Push o Pull
* Many2one, One2Many e Many2Many acquisiti con riferimenti remoti
* Riconosicmento con referenze esterne (solo istanze remote Odoo)
* Configurazione modificabile da GUI
* Controllo anti-ricorsione
* Creazione a due fasi per gestire le gerarchie
* Migratore dinamico database da Odoo 6.1

Questo modulo può essere usato per:

* Migrare database di Odoo tra versioni come openupgrade (anche all'indietro)
* Importare dati da file in locazioni specifiche usando configurazione utente
* Creare ambienti di demo e test partendo da file csv
* Connettere in tempo reale Odoo con altri software o altre istanze Odoo
* Popolare il database quando Odoo necessita di migrare da altro software


|thumbnail|

.. |thumbnail| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/universal_connector_base/static/description/


Configuration | Configurazione
------------------------------

☰ Settings > Technical > Synchronizarion Backend

Set backend parameters to connect with remote counterparty and then click on
button [Check Connection].
If Odoo can connect with remote counterparty, backend state is set to "Ready".

Parameters depend on remote identity and protocol to use.

**xmlrpc over http/https**

This protocol, called XML-RPC, is available with current module and it is implemented
by `python client xmlrpc <https://docs.python.org/3/library/xmlrpc.client.html>`__,
so no additional python package is required to be installed. This protocol is more
simple than REST and SOAP by design.

The typical endpoint to login remote Odoo instance should
be "https://admin@localhost:8069/xmlrpc/2/common" and authentication is based on
username/password; this endppoint uses json rather than xml.
If remote Odoo version is 6.0, 6.1 or 7.0, the typical endpoint should
be "https://admin@localhost:8069/xmlrpc/common".

**http/https**

This protocol is another way to use XML-RPC over http/https. It is supplied by
*universal_connector_by_http* plugin and it is implemented
by `python requests <https://requests.readthedocs.io/en/latest/>`__,
so the `PYPI requests <https://pypi.org/project/requests/>`__ package has to be
installed.

You have to use this protocol to connect remote identities different from Odoo.

**jsonrpc**

This protocol, called JSON-RPC, is like XML-RPC but use JSON representation rather than
XML and it is designed just for Odoo remote identities. It is supplied by
*universal_connector_by_json* plugin and it is implemented
by `odoorpc <https://pythonhosted.org/OdooRPC/>`__,
so the `PYPI odoorpc <https://pypi.org/project/OdooRPC/>`__ package has to be
installed.

**xmlrpc**

This protocol is another way to use XML-RPC over http/https and it is designed just
for Odoo remote identities. It is supplied by
*universal_connector_by_xmlrpc* plugin and it is implemented
by `oerplib <https://pythonhosted.org/OERPLib/>`__,
so the `PYPI oerplib3 <https://pypi.org/project/oerplib3/>`__ package has to be
installed.

You must use this protocol to connect old Odoo instance (before Odoo 10.0).



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

12.0.0.3.11 (2024-12-29)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Context values / Valori in contesto
* [FIX] Language management / Gestione valori in lingua
* [IMP] On connect synchronize company / Sincronizazione azienda alla connessione
* [IMP] New feature: sync by external reference / Sincronizzazione con riferimento esterno
* [IMP] Concatenate function on field / Funzioni concateante per campo
* [IMP] Warning for comodel w/o counterparty / Segnalazione per modelli senza controparte
* [IMP] Best log messages / Migliorie messaggi di log
* [IMP] New tests / Nuovi test
* [QUA] Test coverage 80% (2256: 453+1803) [244 TestPoints] - quality rating 66 (target 100)

12.0.0.3.10 (2024-12-20)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Split from universal_connector
* [IMP] Full refactoring
* [QUA] Test coverage 74% (2186: 578+1608) [215 TestPoints] - quality rating 60 (target 100)



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

Last Update / Ultimo aggiornamento: 2024-12-29

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
