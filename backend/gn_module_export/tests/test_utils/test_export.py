import csv
import json
import tempfile

import fiona
import pytest

from gn_module_export.utils.export import _export_as_file, export_as_file
from gn_module_export.tests.fixtures import (
    export_synthese_sinp,
    export_synthese_sinp_query,
)


@pytest.mark.usefixtures("temporary_transaction")
class TestUtilsExport:
    def test_export_as_file(self, synthese_data, export_synthese_sinp, export_synthese_sinp_query):
        with tempfile.NamedTemporaryFile(suffix=".csv") as f:
            export_as_file(export_synthese_sinp, "csv", f.name, export_synthese_sinp_query)

    def test_export_csv(self, synthese_data, export_synthese_sinp_query):
        with tempfile.NamedTemporaryFile(suffix=".csv") as f:
            _export_as_file("csv", f.name, export_synthese_sinp_query)
            with open(f.name, "r") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                reader = csv.DictReader(csvfile, dialect=dialect)
                ids = {int(row["id_synthese"]) for row in reader}
        ids_synthese = {
            synthese["id_synthese"]
            for synthese in export_synthese_sinp_query.return_query()["items"]
        }
        assert ids_synthese == ids

    def test_export_geojson(self, synthese_data, export_synthese_sinp_query):
        with tempfile.NamedTemporaryFile(suffix=".geojson") as f:
            _export_as_file("geojson", f.name, export_synthese_sinp_query)
            with open(f.name, "r") as json_file:
                res_geojson = json.load(json_file)

        assert res_geojson["type"] == "FeatureCollection"
        assert len(res_geojson["features"]) > 0

    def test_export_json(self, synthese_data, export_synthese_sinp_query):
        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            _export_as_file("json", f.name, export_synthese_sinp_query)
            with open(f.name, "r") as json_file:
                res_json = json.load(json_file)

        assert len(res_json) > 0

    def test_export_geopackage(self, synthese_data, export_synthese_sinp_query):
        file_name = "/tmp/test_fiona.gpkg"
        _export_as_file("gpkg", file_name, export_synthese_sinp_query)

        with fiona.open(file_name, "r", "GPKG", overwrite=True) as gpkg:
            result = {data["properties"]["id_synthese"] for data in gpkg}

        # FIXME: obs1, obs2, obs3 are the only synthese data that can be exported
        # via the view
        ids_synthese = {
            value.id_synthese
            for key, value in synthese_data.items()
            if key in ["obs1", "obs2", "obs3"]
        }
        assert ids_synthese.issubset(result)
