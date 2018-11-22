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
    # app,
    # post_json,
    # json_of_response,
    get_token
)  # noqa: E402
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
        response = self.client.get(
            url_for('exports.getExports')
        )

        assert response.status_code == 200
