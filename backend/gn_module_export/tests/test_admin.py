import pytest
from flask import url_for
from sqlalchemy import select

from geonature.utils.env import db
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_export.models import Export

from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestExportSchedulesAdmin:
    def test_create_view_only_public_exports(self, app, exports):
        from gn_module_export.admin import ExportSchedulesView

        view = ExportSchedulesView(db.session)
        with app.test_request_context():
            form = view.create_form()
            choices = {str(choice[0]): choice[1] for choice in form.export.iter_choices()}

        labels = set(choices.values())
        assert exports["public"].label in labels
        assert exports["private_group_associated"].label not in labels
        assert exports["private_user_associated"].label not in labels

    def test_create_view_page(self, users, exports):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(url_for("exportschedules.create_view"))
        assert response.status_code == 200
        assert exports["public"].label.encode() in response.data
        assert exports["private_group_associated"].label.encode() not in response.data
        assert exports["private_user_associated"].label.encode() not in response.data
