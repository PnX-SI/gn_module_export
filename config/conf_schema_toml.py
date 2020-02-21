'''
   Spécification du schéma toml des paramètres de configurations
'''

from marshmallow import fields, Schema
form geonature.utils.env import ROOT_DIR

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

export_dir = str(ROOT_DIR) + 'backend/static/exports/'
export_schedules_dir = export_dir + '/schedules/'
export_dsw_dir = export_dir + '/dsw/'
export_dsw_filename = 'export_dsw.ttl'

class GnModuleSchemaConf(Schema):
    export_format_map = fields.Dict(missing=export_format_map)
    default_schema = fields.String(missing=default_schema)
    export_dir = fields.String(missing=export_dir)
    export_schedules_dir = fields.String(missing=export_schedules_dir)
    export_dsw_dir = fields.String(missing=export_dsw_dir)
    export_dsw_filename = fields.String(missing=export_dsw_filename)
    nb_days_keep_file = fields.Int(missing=15)
