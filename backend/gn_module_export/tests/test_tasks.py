import pytest
from jsonschema import validate as validate_json
from pathlib import Path

import datetime
import tempfile
import os

from geonature.tests.fixtures import *
from geonature.tests.utils import set_logged_user_cookie
from pypnusershub.tests.utils import set_logged_user_cookie

from geonature.core.notifications.models import Notification
from gn_module_export.tasks import (
    clean_export_file,
    generate_export,
    generate_scheduled_exports,
)
from gn_module_export.utils_export import ExportGenerationNotNeeded, ExportRequest
from gn_module_export.tests.fixtures import exports

from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction")
class TestExportsTasks:
    # deletes the files hand created files
    def test_export_clean(self, export_directories):
        (export_directories["schedules_path"] / "very_old.txt").open("x")
        os.utime(
            export_directories["schedules_path"] / "very_old.txt",
            (1330712280, 1330712292),
        )
        recent = datetime.datetime.now() - datetime.timedelta(
            days=current_app.config["EXPORTS"]["nb_days_keep_file"] / 2
        )
        (export_directories["schedules_path"] / "recent.txt").open("x")
        os.utime(
            export_directories["schedules_path"] / "recent.txt",
            (recent.timestamp(), recent.timestamp()),
        )
        old = datetime.datetime.now() - datetime.timedelta(
            days=current_app.config["EXPORTS"]["nb_days_keep_file"] * 2
        )
        (export_directories["usr_generated_path"] / "old.txt").open("x")
        os.utime(
            export_directories["usr_generated_path"] / "old.txt",
            (old.timestamp(), old.timestamp()),
        )
        (export_directories["usr_generated_path"] / "very_recent.txt").open("x")

        clean_export_file()
        assert not (export_directories["schedules_path"] / "very_old.txt").is_file()
        assert (export_directories["schedules_path"] / "recent.txt").is_file()
        assert not (export_directories["usr_generated_path"] / "old.txt").is_file()
        assert (export_directories["usr_generated_path"] / "very_recent.txt").is_file()

    def test_generate_scheduled_exports(self, exports_schedule, export_directories):
        export_request = ExportRequest(
            id_export=exports_schedule.id_export,
            format=exports_schedule.format,
            skip_newer_than=exports_schedule.skip_newer_than,
        )
        generate_export(
            export_id=export_request.export.id,
            file_name=export_request.get_full_path_file_name(),
            export_url=None,
            format=export_request.format,
            id_role=None,
            filters=None,
        )
        assert Path(export_request.get_full_path_file_name()).is_file()

        #  test generation not needded
        with pytest.raises(ExportGenerationNotNeeded):
            export_request = ExportRequest(
                id_export=exports_schedule.id_export,
                format=exports_schedule.format,
                skip_newer_than=exports_schedule.skip_newer_than,
            )

    def test_generate_users_exports(
        self, export_directories, notifications_enabled, users, exports
    ):
        export_request = ExportRequest(
            id_export=exports["private_user_associated"].id, format="csv", user=users["self_user"]
        )
        generate_export(
            export_id=export_request.export.id,
            file_name=export_request.get_full_path_file_name(),
            export_url=None,
            format=export_request.format,
            id_role=users["self_user"].id_role,
            filters=None,
        )
        assert Path(export_request.get_full_path_file_name()).is_file()

        # Test notifications
        notifications = Notification.query.filter(
            Notification.id_role == users["self_user"].id_role
        ).all()
        assert {notification.id_role for notification in notifications} == {
            users["self_user"].id_role
        }
        assert all(
            exports["private_user_associated"].label in notif.content for notif in notifications
        )
