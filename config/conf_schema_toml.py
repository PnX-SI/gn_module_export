'''
   Spécification du schéma toml des paramètres de configurations
'''
import os
from marshmallow import fields, Schema


default_schema = 'gn_exports'
export_format_map = {
    'csv': {
        'mime': 'text/csv',
        'geofeature': False
        },
    'json': {
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
lod_export = '/home/geonatureadmin/geonature/backend/static/exports/export_lod.ttl'


class GnModuleSchemaConf(Schema):
    export_format_map = fields.Dict(missing=export_format_map)
    default_schema = fields.String(missing=default_schema)
    lod_export = fields.String(missing=lod_export)
    nb_days_keep_file = fields.Int(missing=15)
