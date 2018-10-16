'''
   Spécification du schéma toml des paramètres de configurations
'''

from marshmallow import fields
from geonature.utils.config_schema import GnModuleProdConf


export_format_map = {
    'csv': {
        'mime': 'text/csv'
        },
    'json': {
        'mime': 'application/json'
        },
    'shp': {
        'mime': 'application/zip'
        },
    'rdf': {
        'mime': 'application/rdf+xml'
        }
}  # noqa: E133


class GnModuleSchemaConf(GnModuleProdConf):
    api_url = fields.String(required=True)
    id_application = fields.Integer(required=True)
    export_format_map = fields.Dict(missing=export_format_map)
