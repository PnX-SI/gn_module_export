import os
from datetime import datetime
import logging
from flask import (
    Blueprint,
    # session,
    request,
    current_app,
    send_from_directory,
    jsonify)
from geonature.utils.env import DB, get_module_id
# from geonature.core.gn_meta.models import TDatasets, CorDatasetsActor
# from geonature.utils.errors import GeonatureApiError
# from geonature.core.users.models import TRoles, UserRigth
from geonature.utils.utilssqlalchemy import json_resp
# from pypnusershub.db.tools import (
#     InsufficientRightsError, get_or_fetch_user_cruved)
# from pypnusershub.routes import check_auth_cruved

from .models import (Export, Format, format_map_ext, format_map_mime)


logger = logging.getLogger(__name__)
EXPORTS_FOLDER = os.path.join(current_app.static_folder, 'exports')


try:
    ID_MODULE = get_module_id('exports')
except Exception as e:
    ID_MODULE = 'Error'
    logger.log(str(e))

blueprint = Blueprint('exports', __name__)


@blueprint.route('/add', methods=['GET', 'POST'])
# @check_auth_cruved('C', True)
def add(id_role=None):
    label = request.args.get('label', 'SINP')
    formats = [Format.CSV, Format.JSON]
    exports = []
    for format in formats:
        export = Export(label, format, id_role)
        DB.session.add(export)
        exports.append(export)
    DB.session.commit()
    return jsonify([export.as_dict() for export in exports])


@blueprint.route('/exports')
# @check_auth_cruved('R', True, id_app=ID_MODULE)
# FIXME: 'No token'
# def getExports(info_role):
#     user_cruved = get_or_fetch_user_cruved(
#         session=session,
#         id_role=info_role.id_role,
#         id_application=ID_MODULE,
#         id_application_parent=current_app.config['ID_APPLICATION_GEONATURE']
#     )
#     logger.debug('cruved_user', user_cruved)
@json_resp
def getExports():
    exports = Export.query\
                    .filter(Export.status >= 0)\
                    .group_by(Export.id_export, Export.id)\
                    .order_by(Export.id.desc())\
                    .limit(50)\
                    .all()
    return [export.as_dict() for export in exports]


@blueprint.route('/download/<path:export>')
# @check_auth_cruved('R', True)
def getExport(id_role=None, export=None):
    filename, label, id, extension = fname(export)
    mime = [format_map_mime[k]
            for k, v in format_map_ext.items() if v == extension][0]
    try:
        return send_from_directory(
            EXPORTS_FOLDER, filename, mimetype=mime, as_attachment=True)
    except Exception as e:
        logger.error(str(e))
        raise
        return jsonify(error=str(e))


def fname(export):
    rest, ext = export.rsplit('.', 1)
    _, lbl, id = rest.split('_')
    id = datetime.strftime(
        datetime.fromtimestamp(float(id)), '%Y-%m-%d %H:%M:%S.%f')
    return ('export_{lbl}_{id}.{ext}'.format(lbl=lbl, id=id, ext=ext),
            lbl, id, ext)
