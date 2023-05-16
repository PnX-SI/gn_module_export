import pytest
from jsonschema import validate as validate_json
from pathlib import Path

import datetime
import tempfile
import os

from geonature.tests.fixtures import *
from geonature.tests.utils import set_logged_user_cookie
from pypnusershub.tests.utils import set_logged_user_cookie

from gn_module_export.tasks import clean_export_file

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
