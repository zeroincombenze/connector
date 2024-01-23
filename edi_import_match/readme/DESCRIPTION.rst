What is
-------

This module, inspired to OCA module `Base Import Match <https://github.com/OCA/server-backend/tree/12.0/base_import_match>`__,
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
