'''
   Spécification du schéma toml des paramètres de configurations
'''

from marshmallow import fields, Schema


default_schema = 'gn_exports'
export_format_map = {
    'csv': {
        'mime': 'text/csv',
        'geofeature': False
        },
    'json': {
        'mime': 'application/json',
        'geofeature': False
        },
    'geojson': {
        'mime': 'application/json',
        'geofeature': True
        },
    'shp': {
        'mime': 'application/zip',
        'geofeature': True
        },
    'rdf': {
        'mime': 'application/rdf+xml',
        'geofeature': True
        }
}  # noqa: E133
export_semantic_dsw = '/home/geonatureadmin/geonature/backend/static/exports/export_semantic_dsw.ttl'

class GnModuleSchemaConf(Schema):
    export_format_map = fields.Dict(missing=export_format_map)
    default_schema = fields.String(missing=default_schema)
    export_semantic_dsw = fields.String(missing=export_semantic_dsw)
    nb_days_keep_file = fields.Int(missing=15)
