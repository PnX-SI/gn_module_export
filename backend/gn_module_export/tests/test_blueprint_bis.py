import pytest

from flask import url_for, current_app
from jsonschema import validate as validate_json

from geonature.core.notifications.models import Notification

from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_export.tests.fixtures import exports
from geonature.tests.fixtures import celery_eager


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestBlueprintExportThread:
    def test_public_export_thread(self, exports, users, celery_eager):
        set_logged_user_cookie(self.client, users["user"])
        response = self.client.post(
            url_for(
                "exports.getOneExportThread",
                id_export=exports["public"].id,
                export_format=list(
                    current_app.config["EXPORTS"]["export_format_map"]
                )[0],
            ),
            json={},
        )
        notif = Notification.query.filter_by(id_role=users["user"].id_role).one()
        assert notif
        assert response.status_code == 200

    def test_private_export_thread(self, exports, users, celery_eager):
        set_logged_user_cookie(self.client, users["user"])
        response = self.client.post(
            url_for(
                "exports.getOneExportThread",
                id_export=exports["private"].id,
                export_format=list(
                    current_app.config["EXPORTS"]["export_format_map"].keys()
                )[0],
            ),
            json={},
        )
        assert response.status_code == 403

    def test_private_export_thread_admin(self, exports, users, celery_eager):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.post(
            url_for(
                "exports.getOneExportThread",
                id_export=exports["private"].id,
                export_format=list(
                    current_app.config["EXPORTS"]["export_format_map"]
                )[0],
            ),
            json={},
        )
        # notif = Notification.query.filter_by(id_role=users["user"].id_role).one()
        # assert notif
        assert response.status_code == 200