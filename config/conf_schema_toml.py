'''
   Spécification du schéma toml des paramètres de configurations
'''

from marshmallow import fields, Schema
from geonature.utils.env import ROOT_DIR

export_format_map = {
    'csv': {
        'mime': 'text/csv',
        'geofeature': False,
        'label': 'CSV'
        },
    'json': {
        'mime': 'application/json',
        'geofeature': False,
        'label': 'Json'
        },
    'geojson': {
        'mime': 'application/json',
        'geofeature': True,
        'label': 'GeoJson'
        },
    'shp': {
        'mime': 'application/zip',
        'geofeature': True,
        'label': 'ShapeFile'
        },
    'gpkg': {
        'mime': 'application/zip',
        'geofeature': True,
        'label': 'GeoPackage'
        }
}  # noqa: E133

base_export_dir = str(ROOT_DIR) + '/backend/static/exports/'
export_schedules_dir = base_export_dir + 'schedules/'
export_dsw_dir = base_export_dir + 'dsw/'
export_usrgenerated_dir = str(ROOT_DIR) + '/backend/static/exports/usr_generated'
export_dsw_filename = 'export_dsw.ttl'


class GnModuleSchemaConf(Schema):
    export_format_map = fields.Dict(missing=export_format_map)
    export_schedules_dir = fields.String(missing=export_schedules_dir)
    export_dsw_dir = fields.String(missing=export_dsw_dir)
    export_dsw_filename = fields.String(missing=export_dsw_filename)
    nb_days_keep_file = fields.Int(missing=15)
    export_usrgenerated_dir = fields.String(missing=export_usrgenerated_dir)
    export_web_url = fields.String()
