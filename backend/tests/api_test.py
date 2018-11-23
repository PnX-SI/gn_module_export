import sys
import os
# import json
import pytest
from flask import (
    url_for,
    # session,
    # Response,
    # request
)
# from cookies import Cookie
# from geonature.utils.errors import InsufficientRightsError

sys.path.append(os.path.expanduser('~/geonature/backend/tests'))
from .bootstrap_test import (
    app,  # pylint: disable=W0611
    # post_json,
    # json_of_response,
    get_token
)  # noqa: E402
assert app  # silence pyflake's unused import warning by using assert as a “usage” of the empty import.  # noqa: E501
# UserWarning: The psycopg2 wheel package will be renamed from release 2.8 ...
import warnings  # noqa: E402
warnings.filterwarnings("ignore", category=UserWarning, module='psycopg2')


@pytest.mark.usefixtures('client_class')
class TestApiModuleExports:
    """
        Test de l'api du module Exports
    """

    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }

    def test_getExports(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(url_for('exports.getExports'))
        print('data:', response.data)
        assert response.status_code == 200

    def test_etalab(self):
        response = self.client.get(url_for('exports.etalab_export'))
        assert response.status_code == 200

    def test_export_dlb_csv(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(
            url_for('exports.export', id_export=1, format='csv'))
        assert response.status_code == 200

    def test_export_dlb_json(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(
            url_for('exports.export', id_export=1, format='json'))
        assert response.status_code == 200

    def test_export_dlb_shp(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(
            url_for('exports.export', id_export=1, format='shp'))
        # DLB has geom field
        assert response.status_code == 200

    def test_export_sinp_shp(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(
            url_for('exports.export', id_export=2, format='shp'))
        # SINP export has no geom field
        assert response.status_code == 404
