"""
    Module de gestion des exports
"""

from geonature.utils.env import DB

from utils_flask_sqla_geo.generic import GenericTableGeo


from .models import Export, ExportSchedules


SWAGGER_TYPE_COR = {
    "INTEGER": {"type": "int", "format": "int32"},
    "BIGINT": {"type": "int", "format": "int64"},
    "TEXT": {"type": "string"},
    "UUID": {"type": "string", "format": "uuid"},
    "VARCHAR": {"type": "string"},
    "TIMESTAMP": {"type": "string", "format": "date-time"},
    "TIME": {"type": "string", "format": "date-time"},
    "DATE": {"type": "string", "format": "date"},
}


def generate_swagger_spec(id_export):
    """
    Fonction qui permet de générer dynamiquement
    les spécifications Swagger d'un export
    """
    swagger_parameters = []

    export = Export.query.filter(Export.id == id_export).one()

    export_table = GenericTableGeo(
        tableName=export.view_name,
        schemaName=export.schema_name,
        engine=DB.engine,
        geometry_field=export.geometry_field,
        srid=export.geometry_srid,
    )

    for column in export_table.tableDef.columns:
        type = {"type": "string"}
        if column.type.__class__.__name__ in SWAGGER_TYPE_COR:
            type = SWAGGER_TYPE_COR[column.type.__class__.__name__]
        swagger_parameters.append(
            {
                "in": "query",
                "name": column.name,
                "description": column.comment,
                **type,
            }
        )
    general_params = [
        {
            "in": "query",
            "name": "limit",
            "type": "int",
            "description": "Nombre maximum de résultats à retourner",
        },
        {
            "in": "query",
            "name": "offset",
            "type": "int",
            "description": "Numéro de page",
        },
        {
            "in": "query",
            "name": "orderby",
            "type": "varchar",
            "description": "Nom d'un champ de la vue qui sera utilisé comme variable de tri. Une mention au sens du tri peut être ajoutée en utilisant la syntaxe suivante : nom_col[:ASC|DESC]",
        },
    ]

    if not export.public:
        general_params.insert(
            0,
            {
                "in": "query",
                "name": "token",
                "type": "varchar",
                "description": "Clé de l'API (token). Vous pouvez utiliser aussi l'entête Authorization via le bouton Authorize pour passer ce paramètre.",
            },
        )

    return general_params + swagger_parameters
