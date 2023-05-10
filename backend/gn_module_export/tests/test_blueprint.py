import pytest

from flask import url_for
from geonature.tests.fixtures import *
from geonature.tests.utils import set_logged_user_cookie


from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestBlueprint:
    def test_dummy(self):
        assert True

    def test_api_get_one_private(self, exports):
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private"].id,
            )
        )
        assert response.status_code == 403
        # with token
        response = self.client.get(
            url_for(
                "exports.get_one_export_api",
                id_export=exports["private"].id,
                token="fake_token",
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

    # def test_get_one_export_api_private_with_users(self, users, exports):
    #     pass

    # def test_get_one_export_api_private_with_token(self, users, exports):
    #     pass
