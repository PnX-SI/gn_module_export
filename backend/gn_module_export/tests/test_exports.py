from flask import url_for, current_app

from pytest_benchmark.plugin import benchmark

# assert app  # silence pyflake's unused import warning

import pytest
from werkzeug.exceptions import Unauthorized, Forbidden

from geonature.tests.utils import set_logged_user_cookie


# @pytest.mark.incremental
@pytest.mark.usefixtures("client_class")
@pytest.mark.usefixtures("temporary_transaction")
class TestExports:
    # mimetype = "application/json"
    # headers = {"Content-Type": mimetype, "Accept": mimetype}

    def test_get_exports(self, users):
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == Unauthorized.code

        set_logged_user_cookie(self.client, users["noright_user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == Forbidden.code

        set_logged_user_cookie(self.client, users["stranger_user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200

        set_logged_user_cookie(self.client, users["associate_user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200

        set_logged_user_cookie(self.client, users["self_user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200

        set_logged_user_cookie(self.client, users["user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200

        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(url_for("exports.get_exports"))
        assert response.status_code == 200

        assert response
        assert response.data
        assert response.json[0]["label"] == "Synthese SINP"

    # def test_export_synthese_sinp_csv(self, users):
    #     #token = get_token(self.client)
    #     #self.client.set_cookie("/", "token", token)
    #     set_logged_user_cookie(self.client, users["admin_user"])
    #     tick = datetime.now().replace(microsecond=0)
    #     response = self.client.post(
    #         url_for("exports.getOneExportThread", id_export=1, export_format="csv"), json={'email': "test"}
    #     )
    #     tock = datetime.now().replace(microsecond=0)
    #     assert response.status_code == 200

    #     content_disposition = set(response.headers["Content-Disposition"].split("; "))
    #     assert "attachment" in content_disposition

    #     content_disposition = list(content_disposition)
    #     filenames = [
    #         item for item in content_disposition if item.startswith("filename=")
    #     ]
    #     assert len(filenames) == 1

    #     filename = filenames[0].replace("filename=", "")
    #     assert filename.startswith("export_OccTax_-_DLB_")
    #     assert filename.endswith(".csv")
    #     ts = datetime.strptime(
    #         filename, "export_OccTax_-_DLB_%Y_%m_%d_%Hh%Mm%S.csv"
    #     ).replace(microsecond=0)
    #     assert tick <= ts <= tock
    #     # assert somecontent in response.data

    def test_get_one_export_api(self, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        url_request = url_for("exports.get_one_export_api", id_export=1)
        limit = None
        if limit:
            url_request += f"?limit={limit}"

        response = self.client.get(url_request)

        assert response.status_code == 200
        assert response
        assert response.data

    def test_benchmark_get_one_export_api(self, users, benchmark):
        def _test_get_one_export_api():
            return self.test_get_one_export_api(users)

        benchmark(_test_get_one_export_api)
