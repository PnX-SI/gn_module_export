import pytest

from geonature.utils.env import DB
from pypnusershub.db.models import User
from geonature.tests.fixtures import users

from gn_module_export.models import Export, Licences


@pytest.fixture
def exports(users):
    licence = Licences.query.first()
    public_export = Export(
        label="test public",
        schema_name="gn_commons",
        view_name="t_modules",
        desc="test public export",
        geometry_field=None,
        geometry_srid=None,
        public=True,
        licence=licence,
    )
    DB.session.add(public_export)

    private_export = Export(
        label="test private",
        schema_name="gn_commons",
        view_name="t_modules",
        desc="test private export",
        geometry_field=None,
        geometry_srid=None,
        public=False,
        licence=licence,
    )

    private_export.allowed_roles.append(users["admin_user"])
    DB.session.add(private_export)

    return {
        "public_export": public_export, 
        "private_export": private_export
    }
