This module makes available some functions to synchronize external data
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
