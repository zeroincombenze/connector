===================================================================
|icon| EDI Import Match/Validazione importazione di base 12.0.1.0.0
===================================================================

**Try to avoid duplicate before importing**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/edi_import_match/static/description/icon.png


.. contents::



Overview | Panoramica
=====================

|en| This module, inspired to OCA module `Base Import Match <https://github.com/OCA/server-backend/tree/12.0/base_import_match>`__,
allows you to set additional rules to match if a given import record is an update or a
new record.

Target Audience
---------------

This module can be used to import data from Excel with improved rules.

Why use this
------------

When importing data (like CSV import) with the standard Odoo *base_import* module,
Odoo follows this rule:

* If you import the XMLID of a record, make an **update**
* If you do not, **create** a new record

These rules are too simple and data imported will be duplicated every time file
is imported.

This module avoid to duplicate records.

How
---

User can create his own rules to recognize records.


|it| Questo modulo, ispirato al moduleo OCA `Base Import Match <https://github.com/OCA/server-backend/tree/12.0/base_import_match>`__,
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


|thumbnail|

.. |thumbnail| image:: https://raw.githubusercontent.com/zeroincombenze/connector/12.0/edi_import_match/static/description/description.png


Features | Caratteristiche
--------------------------

Description | Descrizione,Z0incombenze(R),Note(s)
Match rules by end user | Regole definite da utente finale,✅,Available on OCA module
Conditional rule | Regola condizionale,✅,Available on OCA module
Default for conditional rule | Valore predefinito per regola condizionale,✅,
State depends on Country | Provincia dipendente da nazione,✅,
Match boolean values | Confronta valori booleani,❌,



Configuration | Configurazione
------------------------------

Activate developer mode:

#. ☰ Settings > Technical > Database Structure > Import Match
#. [Create]
#. Choose a *Model*
#. Choose the *Fields* that can be used in the search
#. If the rule must be used only for certain imported values, check
   *Conditional* and enter the **exact string** that is going to be imported
   in *Imported value*.

   #. Keep in mind that the match here is evaluated as a case sensitive
      **text string** always. If you enter e.g. ``True``, it will match that
      string, but will not match ``1`` or ``true``.
#. [Save]

In that list view, you can sort rules by drag and drop.



Usage | Utilizzo
----------------

To use this module, you need to:

#. Follow steps in **Configuration** section above.
#. Go to any list view.
#. Press [Import] and follow the import procedure as usual.



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



Known issues | Roadmap
----------------------

This module replaces some feature of the base Odoo function that cannot be overridden.
For this reason, this module depends on specific 12.0.1.3 version of *base* that is the
latest version.

Please, before buy this module, check for base version and if it is older, update base
module to most recent version.



Proposals for enhancement
-------------------------

|en| If you have a proposal to change this module, you may want to send an email to <cc@shs-av.com> for initial feedback.
An Enhancement Proposal may be submitted if your idea gains ground.

|it| Se hai proposte per migliorare questo modulo, puoi inviare una mail a <cc@shs-av.com> per un iniziale contatto.



ChangeLog History | Cronologia modifiche
----------------------------------------

12.0.1.0.0 (2024-01-22)
~~~~~~~~~~~~~~~~~~~~~~~

* Initial implementation / Implementazione iniziale
* [QUA] Test coverage 46% (203: 109+94) [0 TestPoints] - quality rating 28 (target 100)



Credits | Ringraziamenti
========================

Copyright
---------

Odoo is a trademark of `Odoo S.A. <https://www.odoo.com/>`__ (formerly OpenERP)


Authors | Autori
----------------

* `Tecnativa <https://www.tecnativa.com>`__
* `Odoo Community Association (OCA) <https://odoo-community.org>`__
* `SHS-AV s.r.l. <https://www.zeroincombenze.it>`__



Contributors | Partecipanti
---------------------------

* `Tecnativa <https://www.tecnativa.com>`__
* `Antonio M. Vigliotti <antoniomaria.vigliott@gmail.com>`__



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

Last Update / Ultimo aggiornamento: 2024-02-27

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
