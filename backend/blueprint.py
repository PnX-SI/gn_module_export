# flake8: noqa E501
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import (
    Blueprint,
    session,
    request,
    current_app)
from geonature.utils.utilssqlalchemy import (
    json_resp, to_json_resp, to_csv_resp)
from pypnusershub.db.tools import (
    InsufficientRightsError,
    get_or_fetch_user_cruved)
from pypnusershub import routes as fnauth

from .repositories import ExportRepository


logger = current_app.logger
logger.setLevel(logging.DEBUG)

DEFAULT_SCHEMA = 'gn_exports'

blueprint = Blueprint('exports', __name__)


class UserMock(object):
    def __init__(self, id_role=1, tag_object_code='2'):
        self.id_role = id_role
        self.tag_object_code = tag_object_code
        self.id_organisme = '-1'


def export_filename_pattern(export):
    return '_'.join(
        [export.get('label'), datetime.now().strftime('%Y_%m_%d_%Hh%Mm%S')])


@blueprint.route('/export/<int:id_export>/<format>', methods=['GET'])
# @fnauth.check_auth_cruved(
#     'E', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
#     redirect_on_invalid_token=current_app.config.get('URL_APPLICATION'))
def export_format(id_export, format, info_role=None):
    info_role = info_role if info_role else UserMock()
    logger.debug('info_role: %s', info_role)

    assert id_export >= 1
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
        return to_json_resp({'error': 'InsufficientRightsError'}, status=404)


@blueprint.route(
    '/export', defaults={'id_export': None}, methods=['POST', 'PUT'])
@blueprint.route('/export/<int:id_export>', methods=['POST', 'PUT'])
# @fnauth.check_auth_cruved(
#     'E', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
#     redirect_on_invalid_token=current_app.config.get('URL_APPLICATION'))
@json_resp
def create_or_update_export(info_role=None, id_export=None):
    # logger.debug(info_role)
    info_role = info_role if info_role else UserMock()

    payload = request.get_json()
    label = payload.get('label', None)
    view_name = payload.get('view_name', None)
    schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
    desc = payload.get('desc', None)
    id_export = payload.get('id_export', None) or id_export

    id_creator = info_role.id_role

    repo = ExportRepository()
    if label and schema_name and view_name:
        if not id_export:
            try:
                export = repo.create(
                    id_creator=id_creator,
                    label=label,
                    schema_name=schema_name,
                    view_name=view_name,
                    desc=desc)
                return export.as_dict(), 201
            except IntegrityError as e:
                if '(label)=({})'.format(label) in str(e):
                    return {'error': 'Label {} is already registered.'.format(label)}, 400  # noqa E501
                else:
                    raise
        else:
            try:
                export = repo.update(
                    id_creator=id_creator,
                    id_export=id_export,
                    label=label,
                    schema_name=schema_name,
                    view_name=view_name,
                    desc=desc)
                return export.as_dict(), 201
            except NoResultFound as e:
                logger.warn('%s', str(e))
                return {'error': 'Unknown export.'}, 404
            except Exception as e:
                logger.warn('%s', str(e))
                return {'error': 'Echec mise à jour.'}, 400
    else:
        return {
            'error': 'Missing {} parameter.'. format(
                'label' if (schema_name and view_name) else 'schema or view name')}, 400  # noqa E501


@blueprint.route('/export/<id_export>', methods=['DELETE'])
# @fnauth.check_auth_cruved(
#     'D', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
#     redirect_on_invalid_token=current_app.config.get('URL_APPLICATION'))
@json_resp
def delete_export(id_export, info_role=None):
    id_role = info_role.id_role if info_role else UserMock()
    repo = ExportRepository()
    try:
        repo.delete(id_role, id_export)
        return {'result': 'success'}, 204
    except NoResultFound:
        return {'error': 'No result.'}, 404
    except Exception as e:
        logger.warn('%s', str(e))
        return {'error': 'Echec de suppression.'}


@blueprint.route('/')
# @fnauth.check_auth_cruved('R', True)
@json_resp
def getExports(info_role=None):
    # user_cruved = get_or_fetch_user_cruved(
    #     session=session,
    #     id_role=info_role.id_role,
    #     id_application_parent=current_app.config['ID_APPLICATION_GEONATURE']
    # )
    # logger.debug('cruved_user', user_cruved)
    repo = ExportRepository()
    exports = repo.get_list()
    return [export.as_dict() for export in exports]
