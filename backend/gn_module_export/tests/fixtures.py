import pytest
from geonature.tests.fixtures import users
from geonature.utils.env import db
from pypnusershub.db.models import User
from utils_flask_sqla_geo.generic import GenericQueryGeo

from flask import current_app
from pathlib import Path

import tempfile

from gn_module_export.models import CorExportsRoles, Export, Licences, ExportSchedules

EXPORT_SYNTHESE_NAME = "Synthese SINP"


@pytest.fixture(scope="function")
def group_and_user(users):
    with db.session.begin_nested():
        group = User(groupe=True, identifiant="1")
        db.session.add(group)
        user1 = users["user"]
        user1.groups.append(group)
        db.session.add(user1)
    return {"group": group, "user": user1}


@pytest.fixture(scope="function")
def exports(group_and_user, users):
    licence = Licences.query.first()
    export_public = Export(
        label="Public",
        schema_name="gn_exports",
        view_name="t_exports",
        geometry_field=None,
        geometry_srid=None,
        public=True,
        licence=licence,
        view_pk_column="id",
    )
    export_private_group_associated = Export(
        label="Private1",
        schema_name="gn_exports",
        view_name="t_exports",
        geometry_field=None,
        geometry_srid=None,
        public=False,
        id_licence=licence.id_licence,
        view_pk_column="id",
        cor_roles_exports=[CorExportsRoles(id_role=group_and_user["group"].id_role)],
    )
    export_private_role_associated = Export(
        label="Private2",
        schema_name="gn_exports",
        view_name="t_exports",
        public=False,
        id_licence=licence.id_licence,
        view_pk_column="id",
        cor_roles_exports=[CorExportsRoles(id_role=users["self_user"].id_role)],
    )
    with db.session.begin_nested():
        db.session.add(export_public)
        db.session.add(export_private_group_associated)
        db.session.add(export_private_role_associated)
    return {
        "public": export_public,
        "private_group_associated": export_private_group_associated,
        "private_user_associated": export_private_role_associated,
    }


@pytest.fixture(scope="function")
def exports_schedule(exports):
    export_schedule = ExportSchedules(id_export=exports["public"].id, frequency=1, format="csv")
    with db.session.begin_nested():
        db.session.add(export_schedule)
    return export_schedule


@pytest.fixture
def export_synthese_sinp():
    return Export.query.filter(Export.label == EXPORT_SYNTHESE_NAME).one()


@pytest.fixture
def export_synthese_sinp_query(export_synthese_sinp):
    return GenericQueryGeo(
        db,
        export_synthese_sinp.view_name,
        export_synthese_sinp.schema_name,
        geometry_field=export_synthese_sinp.geometry_field,
        limit=10,
    )


@pytest.fixture(scope="function")
def temporary_media_directory(monkeypatch):
    with tempfile.TemporaryDirectory() as media_td:
        monkeypatch.setitem(current_app.config, "MEDIA_FOLDER", media_td)
        yield media_td


@pytest.fixture
def export_directories(temporary_media_directory):
    media_td = temporary_media_directory
    export_path = Path(media_td + "/exports")
    schedules_path = Path(media_td + "/exports/schedules")
    usr_generated_path = Path(media_td + "/exports/usr_generated")
    export_path.mkdir()
    schedules_path.mkdir()
    usr_generated_path.mkdir()
    yield {
        "export_path": export_path,
        "schedules_path": schedules_path,
        "usr_generated_path": usr_generated_path,
    }


@pytest.fixture()
def notifications_enabled(monkeypatch):
    monkeypatch.setitem(current_app.config, "NOTIFICATIONS_ENABLED", True)
