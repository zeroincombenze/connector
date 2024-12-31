This module enable the importing from csv files. The csv files must be located in
directory declared in backend configuration

The first line of csv file must contains the field labels. User can configure the
mapping of the field labels with internal Odoo fields; user can declare conversion
function for every field.

If user declare counterpart Odoo version, after connection, the mapping between
current Odoo version e declared Odoo version will be loaded.

If csv file contains the column "id", the value is used to avoid data replication.
Without this column, the line number is used as "id".
