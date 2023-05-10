import csv
import io
import json

import pytest

from gn_module_export.utils.export import export_csv, export_geojson


@pytest.mark.usefixtures("temporary_transaction")
class TestUtilsExport:
    def test_export_csv(self, synthese_data, export_query):
        tmpfile = io.StringIO()
        columns = export_query.view.tableDef.columns.keys()
        export_query.limit = 10000
        export_csv(query=export_query, fp=tmpfile, columns=columns)

        tmpfile.seek(0)
        dialect = csv.Sniffer().sniff(tmpfile.read(1024))
        tmpfile.seek(0)
        reader = csv.DictReader(tmpfile, dialect=dialect)
        ids = {int(row["id_synthese"]) for row in reader}

        ids_synthese = {
            synthese["id_synthese"] for synthese in export_query.return_query()["items"]
        }

        assert ids_synthese == ids

    def test_export_geojson(self, synthese_data, export_query):
        tmpfile = io.StringIO()
        columns = export_query.view.tableDef.columns.keys()
        export_query.limit = 10000

        export_geojson(query=export_query, fp=tmpfile, columns=columns)

        tmpfile.seek(0)
        res_txt = tmpfile.read()
        res_json = json.loads(res_txt)

        assert res_json["type"] == "FeatureCollection"
        assert len(res_json["features"]) > 0

    def test_export_geojson_with_filters(self, synthese_data, export_query):
        tmpfile = io.StringIO()
        columns = export_query.view.tableDef.columns.keys()
        export_query.limit = 10000

        export_query.filters = {"filter_d_lo_id_synthese": 4}

        export_geojson(query=export_query, fp=tmpfile, columns=columns)

        tmpfile.seek(0)
        res_txt = tmpfile.read()
        res_json = json.loads(res_txt)

        assert res_json["type"] == "FeatureCollection"
        assert len(res_json["features"]) > 0
