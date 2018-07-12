import os
from datetime import datetime
import logging
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


# scratch
@blueprint.route('/queue')
@json_resp
def getQueue():
    exports = Export.query.filter(Export.status == -2, Export.start.is_(None))\
                          .group_by(Export.label, Export.id)\
                          .order_by(Export.id.desc())\
                          .limit(50)\
                          .all()
    return [export.as_dict() for export in exports]


# scratch
@blueprint.route('/perform/<int:export_id>')
@json_resp
def perform(export_id):
    Export.query.filter(Export.id == export_id)\
                .update({'start': DB.func.now()}, synchronize_session=False)
    DB.session.commit()

    # if not exists view(export.label slug):
    #     mkview(export.label slug)
    #     populate view
    # query(view)
    # transform(format, view)
    # save(file) or stream(response)
    export = Export.query.filter(Export.id == export_id).one()
    rows = DB.session.execute(export.selection).fetchall()
    results = [row for row in rows]
    logger.debug(results)
    return results


@blueprint.route('/add', methods=['GET', 'POST'])
# @fnauth.check_auth_cruved('C', True, id_app=ID_MODULE)
@fnauth.check_auth(3)
@json_resp
def add(info_role=None):
    # id_role = info_role.id_role or 1
    id_role = 1
    label = request.args.get('label', None)
    selection = request.args.get('selection', None)
    if label and selection:
        export = Export(id_role, label, selection)
        DB.session.add(export)
        DB.session.commit()
        return export.as_dict()
    else:
        return {'error': 'Missing label or selection parameter.'}


@blueprint.route('/all')
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
    return [export.as_dict() for export in exports] or {'error': 'No available export.'}  # noqa E501


# @blueprint.route('/download/<format>/<int:export_id>')
@blueprint.route('/download/<path:export>')
# @fnauth.check_auth_cruved('R', True)
# @fnauth.check_auth(3)
def getExport(id_role=None, export=None):

    filename, label, id, extension = fname(export)
    mime = [format_map_mime[k]
            for k, v in format_map_ext.items() if v == extension][0]
    if os.path.isfile(filename):
        return send_from_directory(
            EXPORTS_FOLDER, filename, mimetype=mime, as_attachment=True)
    else:
        return jsonify(error='Non existant export.')


def fname(export):
    rest, ext = export.rsplit('.', 1)
    _, lbl, id = rest.split('_')
    id = datetime.strftime(
        datetime.fromtimestamp(float(id)), '%Y-%m-%d %H:%M:%S.%f')
    return ('export_{lbl}_{id}.{ext}'.format(lbl=lbl, id=id, ext=ext),
            lbl, id, ext)
