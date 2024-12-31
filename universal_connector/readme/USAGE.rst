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
