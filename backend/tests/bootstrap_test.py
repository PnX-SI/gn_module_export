import json
from flask import url_for
from cookies import Cookie
import pytest

import server
from geonature.utils.env import load_config, get_config_file_path

# TODO: fixture pour mettre des données test dans la base a chaque test
# https://github.com/pytest-dev/pytest-flask/issues/70

CONF_PATH = get_config_file_path()
APP_CONF = load_config(CONF_PATH)
APP_ID = APP_CONF.get('ID_APPLICATION_GEONATURE')


@pytest.fixture
def app():
    app = server.get_app(APP_CONF)
    app.config['TESTING'] = True
    return app


def post_json(client, url, json_dict):
    """Send dictionary json_dict as a json to the specified url """
    return client.post(
        url, data=json.dumps(json_dict), content_type='application/json')


def json_of_response(response):
    """Decode json from response"""
    return json.loads(response.data.decode('utf8'))


mimetype = 'application/json'
headers = {
    'Content-Type': mimetype,
    'Accept': mimetype
}


def get_token(client, login="admin", password="admin"):
    data = {
        'login': login,
        'password': password,
        'id_application': APP_ID,
        'with_cruved': True
    }
    response = client.post(
        url_for('auth.login'),
        data=json.dumps(data),
        headers=headers
    )
    try:
        token = Cookie.from_string(response.headers['Set-Cookie'])
        return token.value
    except Exception:
        raise Exception('Invalid login {}, {}'.format(login, password))
