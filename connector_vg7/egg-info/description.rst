This module makes available the synchro function to synchronize external data
with Odoo data.
The function synchro return the ID of record found or created. Negative values
are error codes.

The function synchro accepts a data dictionary with field values, like create
and write functions.

Every field name may be:

* "id" (integer): the Odoo ID of record; if supplied means write specific existent record
* "vg7_id" (integer): the external partner ID of record
* Odoo name: same behavior of Odoo write and create; external partner must know the Odoo structure
* External name as format "vg7:field": external name is translated into Odoo name base on dictionary
* Prefixed Odoo name ad format "vg7_field":  external partner must know the Odoo structure but pass its local value

Every field value may be:

* Value as is, i.e. partner name; value is acquired as is.
* Odoo reference: ID of odoo M2O table; external partner must know the Odoo data
* External references: ID of external reference; field name is prefixed by "vg7:" or "vg7_"
* Text of reference: key of reference key, i.e. "admin" in user_id field

Behavior:

* If "id" in field names, the function executes a write to specific ID; id record does not exit exception is generated
* If "vg7_id" in field name, record with vg7_id is searched; if found, the function executes a write
* Search for record matching value passed; the function execute a fallback search algorithm
