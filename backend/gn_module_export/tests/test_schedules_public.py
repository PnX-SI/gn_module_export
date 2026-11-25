"""
Only public exports can be scheduled (scheduled files are downloadable
without authentication). Checks the admin restrictions and the runtime guards.
"""

import pytest
from click.testing import CliRunner
from flask import url_for
from sqlalchemy import select

from geonature.utils.env import db
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_export import tasks
from gn_module_export.commands import generate
from gn_module_export.models import ExportSchedules

from .fixtures import *


@pytest.fixture
def private_export_schedule(exports):
    """Schedule on a non-public export (e.g. created before the restriction)."""
    schedule = ExportSchedules(
        id_export=exports["private_user_associated"].id, frequency=1, format="csv"
    )
    with db.session.begin_nested():
        db.session.add(schedule)
    return schedule


@pytest.mark.usefixtures("client_class", "temporary_transaction", "g_permissions")
class TestSchedulesOnlyPublic:
    def test_admin_reject_schedule_on_private_export(self, users, exports):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.post(
            url_for("exportschedules.create_view"),
            data={
                "export": exports["private_user_associated"].id,
                "frequency": 1,
                "format": "csv",
            },
            content_type="application/x-www-form-urlencoded",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Record was successfully created" not in response.data.decode()
        assert (
            db.session.scalar(
                select(ExportSchedules).where(
                    ExportSchedules.id_export == exports["private_user_associated"].id
                )
            )
            is None
        )

    def test_admin_reject_scheduled_export_becoming_private(self, users, exports_schedule):
        export = exports_schedule.export
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.post(
            url_for("export.edit_view", id=export.id),
            data={
                "label": export.label,
                "schema_name": export.schema_name,
                "view_name": export.view_name,
                "view_pk_column": export.view_pk_column,
                "licence": export.id_licence,
                # "public" unchecked
            },
            content_type="application/x-www-form-urlencoded",
            follow_redirects=True,
        )
        assert response.status_code == 200
        body = response.data.decode()
        assert "doit rester public" in body
        # Flask-Admin rolls the session back on failure: nothing saved
        assert "Record was successfully saved" not in body

    def test_force_schedule_private_export_forbidden(self, users, private_export_schedule):
        set_logged_user_cookie(self.client, users["admin_user"])
        response = self.client.get(
            url_for(
                "exports.forceScheduleExport",
                id_export=private_export_schedule.id_export,
                export_format="csv",
            )
        )
        assert response.status_code == 403, response.data

    def test_scheduler_skip_private_export(
        self, monkeypatch, exports_schedule, private_export_schedule, export_directories
    ):
        scheduled_ids = []
        monkeypatch.setattr(
            tasks.generate_export,
            "delay",
            lambda **kwargs: scheduled_ids.append(kwargs["schedule_id"]),
        )
        tasks.generate_scheduled_exports()
        assert exports_schedule.id_export_schedule in scheduled_ids
        assert private_export_schedule.id_export_schedule not in scheduled_ids

    def test_cli_reject_private_scheduled_export(self, private_export_schedule):
        result = CliRunner().invoke(
            generate, [str(private_export_schedule.id_export), "--format", "csv"]
        )
        assert result.exit_code == 1
        assert "is not public" in result.output
