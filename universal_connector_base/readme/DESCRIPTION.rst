This module is base for Universal Connector suite and makes available some functions
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
