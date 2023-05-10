import pytest

from geonature.utils.env import db
from geonature.tests.fixtures import users

from gn_module_export.models import Export, Licences, CorExportsRoles


@pytest.fixture(scope="class")
def exports(users):
    licence = Licences.query.first()
    export_public = Export(
        label="Public",
        schema_name="gn_exports",
        view_name="t_exports",
        public=True,
        id_licence=licence.id_licence,
    )
    export_private = Export(
        label="Private",
        schema_name="gn_exports",
        view_name="t_exports",
        public=False,
        id_licence=licence.id_licence,
        cor_roles_exports=[CorExportsRoles(id_role=users["user"].id_role)],
    )
    with db.session.begin_nested():
        db.session.add(export_public)
        db.session.add(export_private)
    return {"public": export_public, "private": export_private}
