import pytest
from jsonschema import validate as validate_json
from flask import url_for
from werkzeug.datastructures import Headers

from geonature.tests.fixtures import *
from geonature.tests.utils import set_logged_user_cookie
from pypnusershub.tests.utils import set_logged_user_cookie

from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestExportsBlueprints:
    def test_private_export_without_token_or_login(self, users, exports):
        # private without token and without loggin
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 403

    def test_private_export_with_fake_token(self, users, exports):
        # with fake token
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
                token="fake_token",
            )
        )
        assert response.status_code == 403

    def test_private_export_with_good_token(self, users, exports):
        # With good token
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
                token=exports["private_user_associated"].cor_roles_exports[0].token,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_token_in_header_Authorization_Bearer(
        self, users, exports
    ):
        # With good token and good Authorization Bearer HTTP header
        token = exports["private_user_associated"].cor_roles_exports[0].token
        headers = Headers()
        headers.extend(
            {
                "Authorization": f"Bearer {token}",
            }
        )

        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            ),
            headers=headers,
        )
        assert response.status_code == 200

    def test_private_export_with_token_in_header_Authorization(self, users, exports):
        # Compatibility with Swagger not adding "Bearer" prefix to authorization header value
        token = exports["private_user_associated"].cor_roles_exports[0].token
        headers = Headers()
        headers.extend(
            {
                "Authorization": token,
            }
        )

        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            ),
            headers=headers,
        )
        assert response.status_code == 200

    def test_private_export_with_allowed_id_role(self, users, exports):
        # with an allowed user and without token
        set_logged_user_cookie(self.client, users["self_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 200

    def test_private_admin_export(self, exports, users):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_allowed_group(self, group_and_user, exports):
        # log with a user which is in a group associated with "private_group_associated" export
        set_logged_user_cookie(self.client, group_and_user["user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_group_associated"].id,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_scope_3(self, users, exports):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
            )
        )
        assert response.status_code == 200

    def test_private_export_with_unautorized_user(self, users, exports):
        # with an not allowed user and without token
        set_logged_user_cookie(self.client, users["noright_user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
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
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private_user_associated"].id,
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
