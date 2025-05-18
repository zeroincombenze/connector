======================================================================
|icon| Universal Connector Base/Base connettore universale 10.0.1.3.14
======================================================================

**Basic features for Universal Connector**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/connector/10.0/universal_connector_base/static/description/icon.png


.. contents::



Overview | Panoramica
=====================

|en| This module is base for Universal Connector suite and makes available some functions
to synchronize external data with Odoo data.

The used protocol is "xmlrpc over http/https", called XML-RPC, that is  implemented
by `python client xmlrpc <https://docs.python.org/3/library/xmlrpc.client.html>`__,
so no package is required to be installed. This protocol is more simple than REST and
SOAP by design.

The typical endpoint to login remote Odoo instance should be "https://admin@localhost:8069"
and authentication is based on username/password.

Synchronizable models are:

* Company (res.company)
* Country (res.country and res.country.state)
* Currency (res.currency and res.currency.rate)
* Language (res.lang)
* Partner (res.partner and res.partner.category)
* User (res.users and res.groups)

This module can synchroniza Odoo from version 8.0 to 18.0.
For prior versions you should install the module *universal_connector_openerp*


|it| Questo modulo è base della suite Universal Connector e rende disponibile alcune
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


|thumbnail|

.. |thumbnail| image:: https://raw.githubusercontent.com/zeroincombenze/connector/10.0/universal_connector_base/static/description/


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

<<<<<<< HEAD
10.0.1.3.14 (2025-05-18)
========================
10.0.1.3.14 (2025-05-18)
>>>>>>> 10.0-tmp-20250515
~~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Separate apply e default functions
* [IMP] Protocol items to manage in backend
* [IMP] Importing languages install language
* [IMP] Dynamic apply functions and default functions for specific fields
* [IMP] Automatic propagation limitation for \*many fields
* [QUA] Test coverage 81% (2463: 464+1999) [281 TestPoints] - quality rating 59 (target 100)

10.0.1.3.13 (2025-04-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] company synchronization best algorithm
* [IMP] synchro parameters
* [IMP] cache management
* [IMP] virtual model are deprecated
* [IMP] Protocol model
* [IMP] Identity model
* [QUA] Test coverage 81% (2326: 447+1879) [134 TestPoints] - quality rating 58 (target 100)

10.0.1.3.12 (2025-01-03)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Message log improvements / Migliorie elencazione messeggi
* [IMP] Partner recognition by e-mail too / Riconoscimento nominativo anche da e-mail
* [IMP] Backend does not operate when 'draft' / Dorsale non operative se in 'bozza'
* [IMP] New policy "Only Recent" / Nuova politica "Aggiornamento più recenti"
* [IMP] Button "Pull record" / Bottone "Prelevare dati"
* [QUA] Test coverage 80% (2330: 455+1875) [244 TestPoints] - quality rating 66 (target 100)

10.0.1.3.11 (2024-12-29)
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

10.0.1.3.10 (2024-12-20)
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

Last Update / Ultimo aggiornamento: 2025-05-18

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
