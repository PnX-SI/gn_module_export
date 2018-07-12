import os
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError
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
from geonature.utils.utilssqlalchemy import json_resp
from pypnusershub.db.tools import (
    InsufficientRightsError, get_or_fetch_user_cruved)
from pypnusershub import routes as fnauth

from .models import (
    Export,
    ExportLog,
    # Format,
    format_map_ext,
    format_map_mime)


logger = logging.getLogger(__name__)
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


# garder GET durant le dev/test BE ss auth
@blueprint.route('/create', methods=['GET', 'POST', 'PUT'])
# @fnauth.check_auth_cruved('C', True, id_app=ID_MODULE)
# @fnauth.check_auth(3, True)
@json_resp
def create(info_role=None):
    # FIXME: auth
    # logger.debug('info_role', info_role)
    id_role = info_role.id_role if info_role else 1

    payload = request.get_json()
    label = payload.get('label', None)
    selection = payload.get('selection', None)

    if label and selection:
        try:
            export = Export(id_role, label, selection)
            DB.session.add(export)
            DB.session.commit()
            return export.as_dict()
        except (IntegrityError) as e:
            DB.session.rollback()
            logger.warn('%s', str(e))
            return {'status': 400,
                    'error': 'Label {} is already registered.'.format(label)}

    else:
        return {'status': 400,
                'error': 'Missing {} parameter.'. format('label' if selection else 'selection')}  # noqa E501


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
    return [export.as_dict() for export in exports] or {'error': 'No available export.'}, 204  # noqa E501
