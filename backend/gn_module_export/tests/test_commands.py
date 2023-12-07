import pytest

from click.testing import CliRunner

from geonature.tests.fixtures import *

from gn_module_export.commands import generate
from .fixtures import *


@pytest.mark.usefixtures("client_class", "temporary_transaction", "g_permissions")
class TestExportsCommands:
    # deletes the files hand created files
    def test_generate_user(self, export_directories, exports, users):
        runner = CliRunner()
        result = runner.invoke(
            generate,
            [
                str(exports["public"].id),
                "--format",
                "csv",
                "--user-id",
                users["admin_user"].id_role,
            ],
        )
        # print(result.stdout)
        assert result.exit_code == 0

        # Test skip-newer-than
        result = runner.invoke(
            generate,
            [
                str(exports["public"].id),
                "--format",
                "csv",
                "--user-id",
                users["admin_user"].id_role,
                "--skip-newer-than",
                "5",
            ],
        )
        assert result.exit_code == 1
        assert "sufficiently recent, skip generation" in result.output

        # Test not found fake id export
        result = runner.invoke(
            generate,
            [str(50236944)],
        )
        assert result.exit_code == 1
        assert "not found" in result.output

        # Test not allowed
        result = runner.invoke(
            generate,
            [
                str(exports["private_user_associated"].id),
                "--user-id",
                users["associate_user"].id_role,
            ],
        )
        assert result.exit_code == 1
        assert "not allow for user id" in result.output

    def test_schedule_user(self, export_directories, exports_schedule):
        runner = CliRunner()
        result = runner.invoke(
            generate,
            [str(exports_schedule.export.id), "--format", "csv"],
        )
        print("-----", result.stdout)
        assert result.exit_code == 0
