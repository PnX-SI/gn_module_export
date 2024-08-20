"""
   Spécification du schéma toml des paramètres de configurations
"""

from geonature.utils.env import ROOT_DIR
from marshmallow import Schema, fields

export_format_map = {
    "csv": {"mime": "text/csv", "geofeature": False, "label": "CSV"},
    "json": {"mime": "application/json", "geofeature": False, "label": "Json"},
    "geojson": {"mime": "application/json", "geofeature": True, "label": "GeoJson"},
    "gpkg": {"mime": "application/zip", "geofeature": True, "label": "GeoPackage"},
}  # noqa: E133


class GnModuleSchemaConf(Schema):
    MODULE_URL = fields.String(load_default="/exports")
    export_format_map = fields.Dict(load_default=export_format_map)
    export_dsw_dir = fields.String(load_default="exports/dsw")
    export_dsw_filename = fields.String(load_default="export_dsw.ttl")
    nb_days_keep_file = fields.Int(load_default=15)
    csv_separator = fields.String(load_default=";")
    expose_dsw_api = fields.Boolean(load_default=False)
    max_page_size_api = fields.Int(load_default=1000)
    default_page_size_api = fields.Int(load_default=1000)
