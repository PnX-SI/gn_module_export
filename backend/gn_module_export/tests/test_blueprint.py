import pytest

from flask import url_for
from geonature.tests.fixtures import *
from geonature.tests.utils import set_logged_user_cookie


from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestBlueprint:
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

    def test_private_export_with_allowed_user(self, users, exports):
        # with an allowed user and without token
        set_logged_user_cookie(self.client, users["user"])
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private"].id,
            )
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
