import os
from datetime import datetime
from flask import (
    Blueprint, request, current_app, send_from_directory, jsonify)
from geonature.utils.env import DB
# from geonature.utils.errors import GeonatureApiError
# from geonature.core.users.models import TRoles, UserRigth
# from pypnusershub.db.tools import InsufficientRightsError
# from pypnusershub import routes as fnauth

from .models import (Export, Format, format_map_ext, format_map_mime)
# Standard, standard_map_label)
EXPORTS_FOLDER = os.path.join(current_app.static_folder, 'exports')
# FIXME: backend/frontend/jobs shared conf


blueprint = Blueprint('exports', __name__)


@blueprint.route('/add', methods=['GET'])
# @fnauth.check_auth && id_role
def add():
    label = request.args.get('label', 'SINP')
    formats = [Format.CSV, Format.JSON]
    export = None
    exports = []
    # now = datetime.utcnow()
    for format in formats:
        export = Export(label, format)
        DB.session.add(export)
        exports.append(export)
    DB.session.commit()
    return jsonify([export.as_dict() for export in exports])


@blueprint.route('/exports')
# @fnauth.check_auth
def getExports():
    exports = Export.query\
                    .filter(Export.status >= 0)\
                    .group_by(Export.id_export, Export.id)\
                    .order_by(Export.id.desc())\
                    .limit(50)\
                    .all()
    return jsonify([export.as_dict() for export in exports])


@blueprint.route('/download/<path:export>')
# @fnauth.check_auth
def getExport(export):
    filename, label, id, extension = fname(export)
    mime = [format_map_mime[k]
            for k, v in format_map_ext.items() if v == extension][0]
    print(filename)
    try:
        return send_from_directory(
            EXPORTS_FOLDER, filename, mimetype=mime, as_attachment=True)
    except Exception as e:
        raise
        return jsonify(error=str(e))


def fname(export):
    rest, ext = export.rsplit('.', 1)
    _, lbl, id = rest.split('_')
    # DOING: datetime interface
    id = datetime.strftime(
        datetime.fromtimestamp(float(id)), '%Y-%m-%d %H:%M:%S.%f')
    return ('export_{lbl}_{id}.{ext}'.format(lbl=lbl, id=id, ext=ext),
            lbl, id, ext)
