import pytest

from flask import url_for
from jsonschema import validate as validate_json

from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_export.tests.fixtures import exports


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestExportsBlueprints:
    def test_public_export(self, exports, users):
        set_logged_user_cookie(self.client, users["user"])
        response = self.client.get(
            url_for("exports.get_one_export_api", id_export=exports["public_export"].id)
        )
        assert response.status_code == 200

    def test_private_export(self, exports, users):
        set_logged_user_cookie(self.client, users["user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api", id_export=exports["private_export"].id
            )
        )
        assert response.status_code == 403

    def test_private_admin_export(self, exports, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api", id_export=exports["private_export"].id
            )
        )
        assert response.status_code == 200

    def test_export_schema(self, exports, users):
        schema = {
            "type": "object",
            "properties": {
                "license": {
                    "type": "object",
                    "properties": {
                        "href": {"type": "string"},
                        "name": {"type": "string"},
                    },
                },
                "items": {"type": "array"},
                "limit": {"type": "number"},
                "page": {"type": "number"},
                "total": {"type": "number"},
                "total_filtered": {"type": "number"},
            },
        }
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api", id_export=exports["private_export"].id
            )
        )
        assert response.status_code == 200
        validate_json(instance=response.json, schema=schema)

    def test_unknown_export(self, exports, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for("exports.get_one_export_api", id_export=1000000)
        )
        assert response.status_code == 404
