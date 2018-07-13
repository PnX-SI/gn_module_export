import os
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import (
    Blueprint,
    session,
    request,
    current_app,
    send_from_directory,
    jsonify)
from geonature.utils.env import DB, get_module_id
# from geonature.core.gn_meta.models import TDatasets, CorDatasetsActor
# from geonature.utils.errors import GeonatureApiError
from geonature.core.users.models import TRoles, UserRigth
from geonature.utils.utilssqlalchemy import (
    GenericQuery, json_resp, to_json_resp, csv_resp)
from pypnusershub.db.tools import (
    InsufficientRightsError, get_or_fetch_user_cruved)
from pypnusershub import routes as fnauth

from .models import (
    Export,
    ExportLog,
    # Format,
    format_map_ext,
    format_map_mime)


logger = current_app.logger
logger.setLevel(logging.DEBUG)

EXPORTS_FOLDER = os.path.join(current_app.static_folder, 'exports')
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

try:
    ID_MODULE = get_module_id('exports')
except Exception as e:
    ID_MODULE = 'Error'
    logger.log(str(e))
    raise

blueprint = Blueprint('exports', __name__)


def get_one_export(id_export=None):
    data = GenericQuery(
        DB.session,
        'mavue',
        'gn_exports',
        None,
        {},
        10000, 0).return_query()
    return data, 200


@blueprint.route('/export/<int:id_export>/json', methods=['GET'])
# @json_resp(as_file=True, filename='export.json', indent=4)
def json_export(id_export=None):
    info_role = None
    info_role = info_role.id_role if info_role else 1
    return to_json_resp(
        get_one_export(id_export),
        as_file=True, filename='export.json', indent=4)


@blueprint.route('/export/<int:id_export>/csv', methods=['GET'])
@csv_resp
def csv_export(id_export=None):
    info_role = None
    info_role = info_role.id_role if info_role else 1
    return get_one_export(id_export)


@blueprint.route('/export', defaults={'id_export': None}, methods=['GET', 'POST'])   # noqa E501
@blueprint.route('/export/<id_export>', methods=['GET', 'POST', 'PUT'])
# @fnauth.check_auth_cruved('C', True, id_app=ID_MODULE)
# @fnauth.check_auth(3, True)
@json_resp
# def create_or_update_export(info_role=None, id_export=None):
def create_or_update_export(id_export=None):
    # logger.debug(info_role)
    info_role = None
    id_role = info_role.id_role if info_role else 1

    # payload = request.get_json()
    # payload.get('label', None)
    # payload.get('selection', None)  # noqa E501
    if not id_export:
        id_export = request.args.get('id_export', None)
        id_export = int(id_export)

    label = request.args.get('label', None)
    selection = request.args.get('selection', None)

    if label and selection:
        if not id_export:
            try:
                export = Export(id_role, label, selection)
                DB.session.add(export)
                DB.session.commit()
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
                export = DB.session.query(Export)\
                                   .filter(Export.id == id_export)\
                                   .one()
                export.label = label if label else export.label
                export.selection = selection if selection else export.selection
                DB.session.commit()
                return export.as_dict(), 200
            except NoResultFound as e:
                DB.session.rollback()
                logger.warn(str(e))
                return {'error': 'Unknown export.'}, 404
            except Exception as e:
                DB.session.rollback()
                logger.warn(str(e))
                return {'error': 'Echec mise à jour.'}, 500
    else:
        return {
            'error': 'Missing {} parameter.'. format(
                'label' if selection else 'selection')}, 400


@blueprint.route('/export/<id_export>', methods=['DELETE'])
@json_resp
def delete_export(id_export):
    try:
        export = Export.query.filter_by(id_export=id_export).one()
    except NoResultFound:
        return {'error': 'No result.'}, 404
    else:
        try:
            DB.session.delete(export)
            DB.session.commit()
            return {'result': 'success'}, 204
        except Exception as e:
            DB.session.rollback()
            logger.warn('%s', str(e))
            return {'error': 'Echec de suppression.'}


@blueprint.route('/')
# @fnauth.check_auth_cruved('R', True, id_app=ID_MODULE)
# def getExports(info_role):
#     user_cruved = get_or_fetch_user_cruved(
#         session=session,
#         id_role=info_role.id_role,
#         id_application=ID_MODULE,
#         id_application_parent=current_app.config['ID_APPLICATION_GEONATURE']
#     )
#     logger.debug('cruved_user', user_cruved)
@json_resp
def getExports(info_role=1):

    exports = Export.query\
                    .filter(Export.status >= 0)\
                    .group_by(Export.label, Export.id)\
                    .order_by(Export.start.desc())\
                    .limit(50)\
                    .all()
    return [export.as_dict() for export in exports] or {
        'error': 'No available export.'}, 204
