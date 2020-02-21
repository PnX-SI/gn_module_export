'''
   Spécification du schéma toml des paramètres de configurations
'''

from marshmallow import fields, Schema
from geonature.utils.env import ROOT_DIR

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

base_export_dir = str(ROOT_DIR) + '/backend/static/exports/'
export_schedules_dir = base_export_dir + 'schedules/'
export_dsw_dir = base_export_dir + 'dsw/'
export_dsw_filename = 'export_dsw.ttl'


class GnModuleSchemaConf(Schema):
    export_format_map = fields.Dict(missing=export_format_map)
    export_schedules_dir = fields.String(missing=export_schedules_dir)
    export_dsw_dir = fields.String(missing=export_dsw_dir)
    export_dsw_filename = fields.String(missing=export_dsw_filename)
    nb_days_keep_file = fields.Int(missing=15)
