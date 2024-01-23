
===========================================================
|icon| universal_connector/Connettore universale 10.0.0.3.3
===========================================================

**Universal connector**

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


|

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



Getting started | Primi passi
=============================

|Try Me|


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

    cd $HOME
    # *** Tools installation & activation ***
    # Case 1: you have not installed zeroincombenze tools
    git clone https://github.com/zeroincombenze/tools.git
    cd $HOME/tools
    ./install_tools.sh -pT
    source $HOME/devel/activate_tools
    # Case 2: you have already installed zeroincombenze tools
    cd $HOME/tools
    ./install_tools.sh -UT
    source $HOME/devel/activate_tools
    # *** End of tools installation or upgrade ***
    # Odoo repository installation; OCB repository must be installed
    deploy_odoo clone -r connector -b 10.0 -G zero -p $HOME/10.0
    # Upgrade virtual environment
    vem amend $HOME/10.0/venv_odoo

From UI: go to:

* |menu| Setting > Activate Developer mode
* |menu| Apps > Update Apps List
* |menu| Setting > Apps |right_do| Select **universal_connector** > Install



Upgrade | Aggiornamento
-----------------------


::

    cd $HOME
    # *** Tools installation & activation ***
    # Case 1: you have not installed zeroincombenze tools
    git clone https://github.com/zeroincombenze/tools.git
    cd $HOME/tools
    ./install_tools.sh -pT
    source $HOME/devel/activate_tools
    # Case 2: you have already installed zeroincombenze tools
    cd $HOME/tools
    ./install_tools.sh -UT
    source $HOME/devel/activate_tools
    # *** End of tools installation or upgrade ***
    # Odoo repository upgrade
    deploy_odoo update -r connector -b 10.0 -G zero -p $HOME/10.0
    vem amend $HOME/10.0/venv_odoo
    # Adjust following statements as per your system
    sudo systemctl restart odoo

From UI: go to:

* |menu| Setting > Activate Developer mode
* |menu| Apps > Update Apps List
* |menu| Setting > Apps |right_do| Select **universal_connector** > Update



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

10.0.0.3.3 (2023-10-31)
~~~~~~~~~~~~~~~~~~~~~~~
* [IMP] Unit price withoit tax / Scorporo IVA

10.0.0.3.2 (2023-03-02)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Pull records sto last remote pulled record id
* [FIX] Excel backend with connected test

10.0.0.3.1 (2023-02-26)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Ignore Odoo counterpart fields do not exist in local
* [FIX] Wrong error messages



Credits | Didascalie
====================

Copyright
---------

Odoo is a trademark of `Odoo S.A. <https://www.odoo.com/>`__ (formerly OpenERP)


Authors | Autori
----------------

* SHS-AV s.r.l. <https://www.zeroincombenze.it>


Contributors | Contributi da
----------------------------

* Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>


Maintainer | Manutenzione
-------------------------

Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>


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

Last Update / Ultimo aggiornamento: 2023-10-31

.. |Maturity| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: 
.. |Build Status| image:: https://travis-ci.org/zeroincombenze/connector.svg?branch=10.0
    :target: https://travis-ci.com/zeroincombenze/connector
    :alt: github.com
.. |license gpl| image:: https://img.shields.io/badge/licence-LGPL--3-7379c3.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |license opl| image:: https://img.shields.io/badge/licence-OPL-7379c3.svg
    :target: https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html
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
   :target: https://t.me/Assitenza_clienti_powERP


