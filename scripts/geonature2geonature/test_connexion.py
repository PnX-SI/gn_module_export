#coding=utf-8

# Imports
import sys
import json
import requests
import config
#import psycopg2

# Connexion à l'instance
# MAIN_URL = 'http://carnets.flavia-ape.fr/geonature/api'
MAIN_URL = config.MAIN_URL
EXPORT_API_URL = config.EXPORT_API_URL
ID_EXPORT = config.ID_EXPORT
LOGIN = config.LOGIN
PASSWORD = config.PASSWORD
ID_APPLICATION = config.ID_APPLICATION

# MAIN_URL = 'http://0.0.0.0:8000'
# EXPORT_API_URL = '/exports/api/'
# ID_EXPORT = 1
# LOGIN = 'lpoaura_fcl'
# PASSWORD = 'Philogas80#GeoNature!'
# ID_APPLICATION = 3

session = requests.Session()

# Authentification
data = {
    "id_application": ID_APPLICATION,
    "login": LOGIN,
    "password": PASSWORD
}


AUTH_URL = MAIN_URL + "/auth/login"
# AUTH_DATA = json.dumps(data)
AUTH_DATA = data


print('auth_url', AUTH_URL)
print('auth_data', AUTH_DATA)

HEADERS = {'Content-Type': 'application/json'}

auth = session.post(
    AUTH_URL,
    json=AUTH_DATA,
    headers = HEADERS
)

print('authStatusCode', auth.status_code, auth.json, auth.content)

if not auth.status_code == 200:
    print("Unable to connect : ", auth.json()['msg'])
    sys.exit()

# If authentification is ok
# Getting Data from API
response = session.get(
    MAIN_URL + EXPORT_API_URL + str(ID_EXPORT),
    headers={'accept': 'application/json'}
)

dico = {}
data = response.json()
# print(data)
for k, v in data.items():
    if k == 'items':
        for key, val in v.items():
            print(v)