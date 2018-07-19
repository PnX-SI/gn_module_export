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

# FIXME: mv consts to conf
DEFAULT_SCHEMA = 'gn_exports'
EXPORTS_FOLDER = os.path.join(current_app.static_folder, 'exports')
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

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


@blueprint.route('/export/<int:id_export>/json', methods=['GET'])
# @fnauth.check_auth_cruved(
#     'E', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'))
def json_export(info_role=None, id_export=None):
    info_role = None
    info_role = info_role.id_role if info_role else 1

    repo = ExportRepository()
    try:
        export, data = repo.get_one(id_export, info_role)
        fname = export_filename_pattern(export.get('label'))
        return to_json_resp(data, as_file=True, filename=fname, indent=4)
    except NoResultFound as e:
        logger.warn('%s', str(e))
        return to_json_resp({'error': str(e)}, status=404)


@blueprint.route('/export/<int:id_export>/csv', methods=['GET'])
# @fnauth.check_auth_cruved(
#     'E', True,
#     redirect_on_expiration=current_app.config.get('URL_APPLICATION'))
def csv_export(info_role=None, id_export=None):
    info_role = None
    info_role = info_role.id_role if info_role else 1

    geom_column_header = 'geom_4326'  # FIXME: geom column config.defaults
    srid = 4326  # FIXME: srid config.defaults

    export = Export.query.get(id_export)
    if export:
        fname = export_filename_pattern(export)
        view = GenericTable(
            export.view_name, export.schema_name, geom_column_header, srid)
        columns = [col.name for col in view.db_cols]
        data = get_one_export(export.view_name, export.schema_name)
        try:
            ExportLog.log(id_export=export.id, format='csv', id_user=info_role)
        except Exception as e:
            DB.session.rollback()
            logger.warn('%s', str(e))
            return {'error': 'Echec de journalisation.'}
        return to_csv_resp(fname, data.get('items', None), columns, ',')
    else:
        return {'error': 'Unknown export.'}, 404


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

    # TODO: (drop and re) create view
    # if not id_export and not view_name => creation
    #    create_and_populate_view(schema_def)
    # if id_export and view_name and schema_def? != export.schema_def
    #    drop_view(view_name)
    #    create_and_populate_view()

    repo = ExportRepository()
    if label and schema_name and view_name:
        if not id_export:
            try:
                export = repo.create(
                    id_creator, label, schema_name, view_name, desc)
                return export.as_dict(), 200
            except IntegrityError as e:
                DB.session.rollback()
                logger.warn('%s', str(e))
                if '(label)=({})'.format(label) in str(e):
                    return {'error': 'Label {} is already registered.'.format(label)}, 400  # noqa E501
                else:
                    raise
        else:
            try:
                export = Export.query.get(id_export)
                export.label = label if label else export.label
                export.schema_name = (
                    schema_name if schema_name else export.schema_name)
                export.view_name = view_name if view_name else export.view_name
                export.desc = desc if desc else export.desc
                DB.session.commit()
                return export.as_dict(), 200
            except NoResultFound as e:
                DB.session.rollback()
                logger.warn('%s', str(e))
                return {'error': 'Unknown export.'}, 404
            except Exception as e:
                DB.session.rollback()
                logger.warn('%s', str(e))
                return {'error': 'Echec mise à jour.'}, 500

            try:
                ExportLog.log(
                    id_export=export.id, format='crea', id_user=info_role)
            except Exception as e:
                DB.session.rollback()
                logger.warn('%s', str(e))
                return {'error': 'Echec de journalisation.'}
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
    # TODO: drop view
    try:
        export = Export.query.get(id_export)
    except NoResultFound:
        return {'error': 'No result.'}, 404
    else:
        try:
            export.deleted = datetime.utcnow()
            DB.session.add(export)
            DB.session.commit()
            try:
                ExportLog.log(
                    id_export=export.id, format='dele', id_user=info_role)
            except Exception as e:
                DB.session.rollback()
                logger.critical('%s', str(e))
                return {'error': 'Echec de journalisation.'}
            return {'result': 'success'}, 204
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

    exports = Export.query.filter(Export.deleted.is_(None)).all()
    return [export.as_dict() for export in exports]
