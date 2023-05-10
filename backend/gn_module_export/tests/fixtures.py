import pytest

from geonature.utils.env import db

from gn_module_export.models import Export


@pytest.fixture(scope="function")
def exports():
    export_public = Export(
        label="Public", schema_name="gn_exports", view_name="test", public=True
    )
    export_private = Export(
        label="Private", schema_name="gn_exports", view_name="test", public=False
    )
    db.session.add(export_public)
    db.session.add(export_private)
    return {"public": export_public, "private": export_private}
