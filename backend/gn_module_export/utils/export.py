from typing import Optional

from flask import current_app
from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from ref_geo.utils import get_local_srid
from utils_flask_sqla_geo.export import (export_csv, export_geojson,
                                         export_geopackage, export_json)
from utils_flask_sqla_geo.generic import GenericQueryGeo

from gn_module_export.models import Export


def export_as_file(export: Export, file_format: str, filename: str, generic_query_geo: GenericQueryGeo):
    # TODO Add export.pk_name when available
    _export_as_file(
        file_format, filename, generic_query_geo, export.geometry_field, srid=export.geometry_srid
    )


def _export_as_file(
    file_format: str,
    filename: str,
    generic_query_geo: GenericQueryGeo,
    geometry_field_name: Optional[str] = None,
    pk_name: Optional[str] = None,
    srid: Optional[int] = None,
):
    format_list = [k for k in current_app.config["EXPORTS"]["export_format_map"].keys()]

    if file_format not in format_list:
        raise GeoNatureError("Unsupported format")
    if file_format == "gpkg" and srid is None:
        srid = get_local_srid(db.session)

    schema_class = generic_query_geo.get_marshmallow_schema(pk_name=pk_name)
    columns = generic_query_geo.view.tableDef.columns.keys()
    columns = []

    if file_format == "gpkg":
        export_geopackage(
            query=generic_query_geo.raw_query(),
            schema_class=schema_class,
            filename=filename,
            geometry_field_name=geometry_field_name,
            srid=srid,
        )
        return

    func_dict = {"geojson": export_geojson, "json": export_json, "csv": export_csv}

    with open(filename, "w") as f:
        func_dict[file_format](
            query=generic_query_geo.raw_query(),
            schema_class=schema_class,
            fp=f,
            geometry_field_name=geometry_field_name,
            columns=columns,
        )
