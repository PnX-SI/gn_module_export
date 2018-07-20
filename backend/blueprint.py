# flake8: noqa E501
import os
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import (
    Blueprint,
    # session,
    request,
    current_app)

from geonature.utils.env import DB
# from geonature.core.gn_meta.models import TDatasets, CorDatasetsActor
# from geonature.utils.errors import GeonatureApiError
# from geonature.core.users.models import TRoles, UserRigth
from geonature.utils.utilssqlalchemy import (
    GenericQuery, GenericTable, json_resp, to_json_resp, to_csv_resp)
# from pypnusershub.db.tools import (
#     InsufficientRightsError, get_or_fetch_user_cruved)
# from pypnusershub import routes as fnauth

from .models import Export, ExportLog
from .repositories import ExportRepository


logger = current_app.logger
logger.setLevel(logging.DEBUG)

DEFAULT_SCHEMA = 'gn_exports'

blueprint = Blueprint('exports', __name__)


# FIXME: mv export file name pattern to conf
def export_filename_pattern(label):
    return '_'.join(
        [label, datetime.now().strftime('%Y_%m_%d_%Hh%Mm%S')])


def get_one_export(
        view, schema,
        geom_column_header=None, filters={},
        limit=10000, paging=0):

    logger.debug('Querying "%s"."%s"', schema, view)

    # public.geometry_columns
    data = GenericQuery(
        DB.session, view, schema, geom_column_header,
        filters, limit, paging).return_query()

    logger.debug('Query results: %s', data)
    return data


@blueprint.route('/export/<int:id_export>/<format>', methods=['GET'])
# @fnauth.check_auth_cruved(
#     'E', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'))
def export_format(id_export, format):
    info_role = None  # mv to func args
    id_role = info_role.id_role if info_role else 1

    assert format in ['csv', 'json']

    repo = ExportRepository()
    try:
        export, data, columns = repo.get_by_id(
            id_role, id_export, with_data=True, format=format)
        if export:
            fname = export_filename_pattern(export.get('label'))

            if format == 'json':
                return to_json_resp(
                    data, as_file=True, filename=fname, indent=4)
            if format == 'csv':
                return to_csv_resp(fname, data, columns, ',')

    except NoResultFound as e:
        logger.warn('%s', str(e))
        return to_json_resp({'error': str(e)}, status=404)


@blueprint.route(
    '/export', defaults={'id_export': None}, methods=['POST', 'PUT'])
@blueprint.route('/export/<int:id_export>', methods=['POST', 'PUT'])
# @fnauth.check_auth_cruved(
#     'E', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'))
@json_resp
def create_or_update_export(info_role=None, id_export=None):
    # logger.debug(inf _role)
    id_creator = info_role.id_role if info_role else 1

    payload = request.get_json()
    label = payload.get('label', None)
    view_name = payload.get('view_name', None)
    schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
    desc = payload.get('desc', None)
    id_export = payload.get('id_export', None) or id_export

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
                return export.as_dict(), 200
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
                return export.as_dict(), 200
            except NoResultFound as e:
                logger.warn('%s', str(e))
                return {'error': 'Unknown export.'}, 404
            except Exception as e:
                DB.session.rollback()
                logger.warn('%s', str(e))
                return {'error': 'Echec mise à jour.'}, 500
    else:
        return {
            'error': 'Missing {} parameter.'. format(
                'label' if (schema_name and view_name) else 'schema or view name')}, 400  # noqa E501


@blueprint.route('/export/<id_export>', methods=['DELETE'])
# @fnauth.check_auth_cruved(
#     'D', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'))
@json_resp
def delete_export(info_role=None, id_export=None):
    id_role = info_role.id_role if info_role else 1
    repo = ExportRepository()
    try:
        repo.delete(id_role, id_export)
        return {'result': 'success'}, 204
    except NoResultFound:
        return {'error': 'No result.'}, 404
    except Exception as e:
        DB.session.rollback()
        logger.warn('%s', str(e))
        return {'error': 'Echec de suppression.'}


@blueprint.route('/')
# @fnauth.check_auth_cruved(
#     'R', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'))
# def getExports(info_role):
#     user_cruved = get_or_fetch_user_cruved(
#         session=session,
#         id_role=info_role.id_role,
#        # id_application=ID_MODULE,
#         id_application_parent=current_app.config['ID_APPLICATION_GEONATURE']
#     )
#     logger.debug('cruved_user', user_cruved)
@json_resp
def getExports(info_role=1):
    repo = ExportRepository()
    exports = repo.get_all()
    return [export.as_dict() for export in exports]
