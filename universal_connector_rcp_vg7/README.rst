=============================================================
|icon| Universal Connector VG7/Connettore per VG7 12.0.1.3.16
=============================================================

**Add Remote Counterparty VG7 to Universal Connector**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/universal_connector_rcp_vg7/static/description/icon.png


.. contents::



Overview | Panoramica
=====================

|en| Connector to "VG7 print" software.

This module, based on Universal Connector, allow the download of data from remote
"VG7 print" software. Connector can import:

* Customers
* Customer addresses
* Products


|it| Connettore verso software "VG7 print".

Questo modulo, basato su Connettore Universlae, permette di scaricare i dati da
"VG7 print". Il connettore può importare:

* Clienti
* Indirizzi clienti
* Prodotti


|thumbnail|

.. |thumbnail| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/universal_connector_rcp_vg7/static/description/


Configuration | Configurazione
------------------------------

☰ Settings > Activate the developer mode

☰ Settings > Technical > Synchronization Backend

#. Set protocol to "VG7 Print"
#. Add Client Key
#. Declare identity "VG7"
#. Choose "vg7_id" prefix for this backend
#. Declare remote user language
#. Set Endpoint
#. Click on button [Check Connection]

If Odoo can connect with remote counterparty, backend state is set to "Ready".



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

12.0.1.3.17 (2025-06-09)
~~~~~~~~~~~~~~~~~~~~~~~~

* [QUA] Test coverage 63% (262: 98+164) [34 TestPoints] - quality rating 47 (target 100)

12.0.1.3.16 (2025-06-06)
~~~~~~~~~~~~~~~~~~~~~~~~

* [QUA] Test coverage 63% (262: 98+164) [16 TestPoints] - quality rating 42 (target 100)

12.0.1.3.15 (2025-05-19)
~~~~~~~~~~~~~~~~~~~~~~~~

* [QUA] Test coverage 63% (262: 98+164) [11 TestPoints] - quality rating 41 (target 100)

12.0.1.3.14 (2025-05-18)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Instance without company splitmode
* [FIX] set_globak
* [QUA] Test coverage 63% (262: 98+164) [11 TestPoints] - quality rating 41 (target 100)

12.0.1.3.13 (2025-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Instance without company splitmode
* [FIX] set_globak
* [QUA] Test coverage 67% (223: 73+150) [11 TestPoints] - quality rating 49 (target 100)

12.0.1.3.12 (2024-12-30)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Dependign on version check / Controllo versione dipendenze
* [QUA] Test coverage 66% (223: 76+147) [9 TestPoints] - quality rating 47 (target 100)

12.0.1.3.11 (2024-12-29)
~~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Upgrade to universal_connector_base
* [QUA] Test coverage 66% (223: 76+147) [9 TestPoints] - quality rating 47 (target 100)

12.0.1.3.10 (2024-12-19)
~~~~~~~~~~~~~~~~~~~~~~~~

* Initial implementation / Implementazione iniziale
* [QUA] Test coverage 66% (223: 76+147) [9 TestPoints] - quality rating 47 (target 100)



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

Last Update / Ultimo aggiornamento: 2025-06-09

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
