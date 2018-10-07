'''
   Spécification du schéma toml des paramètres de configurations
'''

from marshmallow import fields
from geonature.utils.config_schema import GnModuleProdConf


export_format_map = {
    'csv': {
        'mime': 'text/csv',
        'extension': 'csv'
        },
    'json': {
        'mime': 'application/json',
        'extension': 'json'
        },
    'rdf': {
        'mime': 'application/rdf+xml',
        'extension': 'rdf'
        }
}  # noqa: E133


class GnModuleSchemaConf(GnModuleProdConf):
    export_format_map = fields.Dict(missing=export_format_map)
