from marshmallow_sqlalchemy.fields import Nested

from geonature.utils.env import ma

from utils_flask_sqla.schema import SmartRelationshipsMixin


from gn_module_export.models import Export, Licences, CorExportsRoles


class ExportSchema(SmartRelationshipsMixin, ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Export
        include_fk = True

    licence = Nested("LicencesSchema")
    cor_roles_exports = Nested("CorExportsRolesSchema", many=True, only=("id_role", "token"))


class LicencesSchema(SmartRelationshipsMixin, ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Licences
        include_fk = True

    exports = Nested("ExportSchema", many=True)


class CorExportsRolesSchema(SmartRelationshipsMixin, ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CorExportsRoles
        include_fk = True

    exports = Nested("ExportSchema", many=True)
