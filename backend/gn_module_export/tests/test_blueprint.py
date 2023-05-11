import pytest
from jsonschema import validate as validate_json
from flask import url_for

from geonature.tests.fixtures import *
from geonature.tests.utils import set_logged_user_cookie
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_export.tests.fixtures import exports

from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestExportsBlueprints:
    def test_private_export_without_token_or_login(self, users, exports):
        # private without token and without loggin
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private"].id,
            )
        )
        assert response.status_code == 403

    def test_private_export_with_fake_token(self, users, exports):
        # with fake token
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private"].id,
                token="fake_token",
            )
        )
        assert response.status_code == 403

    def test_public_export(self, exports, users):
        set_logged_user_cookie(self.client, users["user"])
        response = self.client.get(
            url_for("exports.get_one_export_api", id_export=exports["public"].id)
        )
        assert response.status_code == 200

    def test_private_export(self, exports, users):
        set_logged_user_cookie(self.client, users["user"])
        response = self.client.get(
            url_for("exports.get_one_export_api", id_export=exports["private"].id)
        )
        assert response.status_code == 403

    def test_private_export_with_good_token(self, users, exports):
        # with good token
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private"].id,
                token=exports["private"].cor_roles_exports[0].token,
            )
        )
        assert response.status_code == 200

    def test_private_admin_export(self, exports, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for("exports.get_one_export_api", id_export=exports["private"].id)
        )
        assert response.status_code == 200

    def test_private_export_with_good_token(self, users, exports):
        # with an not allowed user and without token
        set_logged_user_cookie(self.client, users["noright_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private"].id,
            )
        )
        assert response.status_code == 403

    def test_get_one_export_api_public(self, exports):
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["public"].id,
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
            url_for("exports.get_one_export_api", id_export=exports["private"].id)
        )
        assert response.status_code == 200
        validate_json(instance=response.json, schema=schema)

    def test_unknown_export(self, exports, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for("exports.get_one_export_api", id_export=1000000)
        )
        assert response.status_code == 404
