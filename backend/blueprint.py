from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import (
    Blueprint,
    request,
    current_app)
from geonature.utils.env import get_module_id
from geonature.utils.utilssqlalchemy import (
    json_resp, to_json_resp, to_csv_resp)
from pypnusershub.db.tools import InsufficientRightsError
from pypnusershub import routes as fnauth

from .repositories import ExportRepository


logger = current_app.logger
logger.setLevel(logging.DEBUG)

ID_MODULE = get_module_id('exports')
DEFAULT_SCHEMA = 'gn_exports'

blueprint = Blueprint('exports', __name__)


def export_filename_pattern(export):
    return '_'.join(
        [export.get('label'), datetime.now().strftime('%Y_%m_%d_%Hh%Mm%S')])


@blueprint.route('/export/<int:id_export>/<format>', methods=['GET'])
@fnauth.check_auth_cruved('E', True, id_app=ID_MODULE)
def export(id_export, format, info_role):
    logger.debug('info_role: %s', info_role)

    if id_export < 1:
        return to_json_resp({'error': 'Invalid export id'}, status=404)

    assert format in ['csv', 'json']

    repo = ExportRepository()
    try:
        export, columns, data = repo.get_by_id(
            info_role, id_export, with_data=True, format=format)
        if export:
            fname = export_filename_pattern(export)

            if format == 'json':
                return to_json_resp(
                    data.get('items', None),
                    as_file=True, filename=fname, indent=4)

            if format == 'csv':
                return to_csv_resp(
                    fname, data.get('items', None), columns, ',')

    except NoResultFound as e:
        logger.warn('%s', str(e))
        return to_json_resp({'error': str(e)}, status=404)
    except InsufficientRightsError:
        logger.warn('InsufficientRightsError')
        return to_json_resp({'error': 'InsufficientRightsError'}, status=403)
    except Exception as e:
        logger.critical('%s', str(e))
        return to_json_resp({'error': 'LoggedError'}, status=400)


@blueprint.route('/export', methods=['POST', 'PUT'])  # noqa E501
@fnauth.check_auth_cruved('C', True, id_app=ID_MODULE)
@json_resp
def create(info_role):
    payload = request.get_json()
    label = payload.get('label', None)
    view_name = payload.get('view_name', None)
    schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
    desc = payload.get('desc', None)

    id_creator = info_role.id_role

    if not(label and schema_name and view_name):
        return {
            'error': 'Missing {} parameter.'. format(
                'label' if (schema_name and view_name) else 'schema or view name')}, 400  # noqa E501

    repo = ExportRepository()
    try:
        export = repo.create(
            id_creator=id_creator,
            label=label,
            schema_name=schema_name,
            view_name=view_name,
            desc=desc)
    except IntegrityError as e:
        if '(label)=({})'.format(label) in str(e):
            return {'error': 'Label {} is already registered.'.format(label)}, 400  # noqa E501
        else:
            raise
    else:
        return export.as_dict(), 201


@blueprint.route('/export/<int:id_export>', methods=['POST', 'PUT'])
@fnauth.check_auth_cruved('U', True, id_app=ID_MODULE)
def update(id_export, info_role):
    payload = request.get_json()
    label = payload.get('label', None)
    view_name = payload.get('view_name', None)
    schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
    desc = payload.get('desc', None)

    id_creator = info_role.id_role

    if not all(label, schema_name, view_name, desc):
        return {
            'error': 'Missing parameter.'. format(
                'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa E501

    repo = ExportRepository()
    try:
        export = repo.update(
            id_creator=id_creator,
            id_export=id_export,
            label=label,
            schema_name=schema_name,
            view_name=view_name,
            desc=desc)
    except NoResultFound as e:
        logger.warn('%s', str(e))
        return {'error': str(e)}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'error': 'LoggedError'}, 400
    else:
        return export.as_dict(), 201


@blueprint.route('/export/<id_export>', methods=['DELETE'])
@fnauth.check_auth_cruved('D', True, id_app=ID_MODULE)
@json_resp
def delete_export(id_export, info_role):
    repo = ExportRepository()
    try:
        repo.delete(info_role.id_role, id_export)
    except NoResultFound as e:
        logger.warn('%s', str(e))
        return {'error': str(e)}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'error': 'LoggedError'}, 400
    else:
        return {'result': 'success'}, 204


@blueprint.route('/')
@fnauth.check_auth_cruved('R', True, id_app=ID_MODULE)
@json_resp
def getExports(info_role):
    repo = ExportRepository()
    try:
        exports = repo.get_list()
    except NoResultFound as e:
        logger.warn('%s', str(e))
        return {'error': str(e)}, 204
    else:
        return [export.as_dict() for export in exports]
