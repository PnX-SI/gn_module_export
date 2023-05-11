import pytest
from geonature.utils.env import db
from geonature.tests.fixtures import users

from gn_module_export.models import Export, Licences


@pytest.fixture(scope="class")
def exports(users):
    licence = Licences.query.first()
    export_public = Export(
        label="Public",
        schema_name="gn_exports",
        view_name="t_exports",
        geometry_field=None,
        geometry_srid=None,
        public=True,
        licence=licence,
    )
    export_private = Export(
        label="Private",
        schema_name="gn_exports",
        view_name="t_exports",
        geometry_field=None,
        geometry_srid=None,
        public=False,
        licence=licence,
    )
    with db.session.begin_nested():
        db.session.add(export_public)
        db.session.add(export_private)
    with db.session.begin_nested():
        export_private.allowed_roles.append(users["admin_user"])
    return {"public": export_public, "private": export_private}
