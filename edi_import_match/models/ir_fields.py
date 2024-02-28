import psycopg2

from odoo import api, models, _
from odoo.tools import pycompat

REFERENCING_FIELDS = {None, 'id', '.id'}


class IrFieldsConverter(models.AbstractModel):
    _inherit = 'ir.fields.converter'

    def _register_hook(self):

        @api.model
        def for_model_z0(self, model, fromtype=str):
            """ Returns a converter object for the model. A converter is a
            callable taking a record-ish (a dictionary representing an odoo
            record with values of typetag ``fromtype``) and returning a converted
            records matching what :meth:`odoo.osv.orm.Model.write` expects.

            This monkey patch manages 2 level search for res.country.state
            :param model: :class:`odoo.osv.orm.Model` for the conversion base
            :returns: a converter callable
            :rtype: (record: dict, logger: (field, error) -> None) -> dict
            """
            # make sure model is new api
            model = self.env[model._name]

            converters = {
                name: self.to_field(model, field, fromtype)
                for name, field in model._fields.items()
            }

            def fn(record, log):
                converted = {}
                # Search for country of res.country.state
                suppl = {}
                if "country_id" in record.keys() and "state_id" in record.keys():
                    field = "country_id"
                    if len(record[field]) and None in record[field][0]:
                        id, ws = converters[field](record[field])
                        if id:
                            suppl["state_id"] = [("country_id", "=", id)]

                for field, value in record.items():
                    if field in REFERENCING_FIELDS:
                        continue
                    if not value:
                        converted[field] = False
                        continue
                    try:
                        if field in suppl:
                            converted[field], ws = converters[field](value,
                                                                     args=suppl[field])
                        else:
                            converted[field], ws = converters[field](value)
                        for w in ws:
                            if isinstance(w, pycompat.string_types):
                                # wrap warning string in an ImportWarning for
                                # uniform handling
                                w = ImportWarning(w)
                            log(field, w)
                    except (UnicodeEncodeError, UnicodeDecodeError) as e:
                        log(field, ValueError(str(e)))
                    except ValueError as e:
                        log(field, e)
                return converted

            return fn

        @api.model
        def _str_to_many2one_z0(self, model, field, values, args=None):
            # Redefined function with supplemental arguments (monkey patch)
            # Should only be one record, unpack
            [record] = values

            subfield, w1 = self._referencing_subfield(record)

            id, _, w2 = self.db_id_for(model, field, subfield, record[subfield],
                                       args=args)
            return id, w1 + w2

        @api.model
        def db_id_for_z0(self, model, field, subfield, value, args=None):
            """ Finds a database id for the reference ``value`` in the referencing
            subfield ``subfield`` of the provided field of the provided model.

            :param model: model to which the field belongs
            :param field: relational field for which references are provided
            :param subfield: a relational subfield allowing building of refs to
                             existing records: ``None`` for a name_get/name_search,
                             ``id`` for an external id and ``.id`` for a database
                             id
            :param value: value of the reference to match to an actual record
            :param args: supplemental arguments for name_search (monkey patch)
            :param context: OpenERP request context
            :return: a pair of the matched database identifier (if any), the
                     translated user-readable name for the field and the list of
                     warnings
            :rtype: (ID|None, unicode, list)
            """
            # the function 'flush' comes from BaseModel.load(), and forces the
            # creation/update of former records (batch creation)
            flush = self._context.get('import_flush', lambda arg=None: None)

            id = None
            warnings = []
            error_msg = ''
            action = {'type': 'ir.actions.act_window', 'target': 'new',
                      'view_mode': 'tree,form', 'view_type': 'form',
                      'views': [(False, 'tree'), (False, 'form')],
                      'help': _(u"See all possible values")}
            if subfield is None:
                action['res_model'] = field.comodel_name
            elif subfield in ('id', '.id'):
                action['res_model'] = 'ir.model.data'
                action['domain'] = [('model', '=', field.comodel_name)]

            RelatedModel = self.env[field.comodel_name]
            if subfield == '.id':
                field_type = _(u"database id")
                if isinstance(value, str) and not self._str_to_boolean(model,
                                                                       field,
                                                                       value)[0]:
                    return False, field_type, warnings
                try:
                    tentative_id = int(value)
                except ValueError:
                    tentative_id = value
                try:
                    if RelatedModel.search([('id', '=', tentative_id)]):
                        id = tentative_id
                except psycopg2.DataError:
                    # type error
                    raise self._format_import_error(
                        ValueError,
                        _(u"Invalid database id '%s' for the field '%%(field)s'"),
                        value,
                        {'moreinfo': action})
            elif subfield == 'id':
                field_type = _(u"external id")
                if not self._str_to_boolean(model, field, value)[0]:
                    return False, field_type, warnings
                if '.' in value:
                    xmlid = value
                else:
                    xmlid = "%s.%s" % (self._context.get('_import_current_module',
                                                         ''), value)
                flush(xmlid)
                id = self.env['ir.model.data'].xmlid_to_res_id(
                    xmlid, raise_if_not_found=False) or None
            elif subfield is None:
                field_type = _(u"name")
                if value == '':
                    return False, field_type, warnings
                flush()
                ids = RelatedModel.name_search(name=value, operator='=', args=args)
                if ids:
                    if len(ids) > 1:
                        warnings.append(ImportWarning(
                            _("Found multiple matches for field '%%(field)s'"
                              " (%d matches)") % (len(ids))))
                    id, _name = ids[0]
                else:
                    name_create_enabled_fields = self.env.context.get(
                        'name_create_enabled_fields') or {}
                    if name_create_enabled_fields.get(field.name):
                        try:
                            id, _name = RelatedModel.name_create(name=value)
                        except Exception as e:
                            error_msg = repr(e)
            else:
                raise self._format_import_error(
                    Exception,
                    _(u"Unknown sub-field '%s'"),
                    subfield
                )

            if id is None:
                if error_msg:
                    message = _(
                        "No matching record found for %(field_type)s '%(value)s'"
                        " in field '%%(field)s' and the following error was encountered"
                        " when we attempted to create one: %(error_message)s")
                else:
                    message = _("No matching record found for %(field_type)s"
                                " '%(value)s' in field '%%(field)s'")
                raise self._format_import_error(
                    ValueError,
                    message,
                    {'field_type': field_type,
                     'value': value,
                     'error_message': error_msg},
                    {'moreinfo': action})
            return id, field_type, warnings

        self._patch_method("for_model",
                           for_model_z0)
        self._patch_method("db_id_for",
                           db_id_for_z0)
        self._patch_method("_str_to_many2one",
                           _str_to_many2one_z0)
        return super()._register_hook()
