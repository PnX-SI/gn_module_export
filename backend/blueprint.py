import os
from flask import (
    Blueprint, request, current_app, send_from_directory, jsonify)
from geonature.utils.env import DB
# from geonature.utils.errors import GeonatureApiError
# from geonature.core.users.models import TRoles, UserRigth
# from pypnusershub.db.tools import InsufficientRightsError
# from pypnusershub import routes as fnauth

from .models import (Export,
                     Format, format_map_ext, format_map_mime,
                     Standard, standard_map_label)
EXPORTS_FOLDER = os.path.join(current_app.static_folder, 'exports')
# FIXME: backend/frontend/jobs shared conf


blueprint = Blueprint('exports', __name__)


@blueprint.route('/add', methods=['GET'])
# @fnauth.check_auth
def add():
    label = request.args.get('label', 'SINP')
    formats = [Format.CSV, Format.JSON]
    export = None
    exports = []
    for format in formats:
        export = Export(label, format)
        DB.session.add(export)
        exports.append(export)
    DB.session.commit()
    return jsonify([{
            'id': export.id,
            'label': export.label,
            'selection': export.selection,
            'format': format_map_ext[export.format].upper()
        } for export in exports])


@blueprint.route('/download/<path:export>')
# @fnauth.check_auth
def getExport(export):
    filename, label, id, extension = fname(export)
    mime = [format_map_mime[k]
            for k, v in format_map_ext.items() if v == extension][0]
    try:
        return send_from_directory(
            EXPORTS_FOLDER, filename, mimetype=mime, as_attachment=True)
    except Exception as e:
        return str(e)


@blueprint.route('/exports')
# @fnauth.check_auth
def getExports():
    # FIXME: export selection, order, limit
    exports = Export.query\
                    .filter(Export.status >= 0)\
                    .group_by(Export.id_export, Export.id)\
                    .order_by(Export.id.desc())\
                    .limit(50)\
                    .all()
    return jsonify([export.as_dict() for export in exports])


def fname(export):
    rest, ext = export.rsplit('.', 1)
    _, lbl, id = rest.split('_')
    return ('export_{lbl}_{id}.{ext}'.format(lbl=lbl, id=id, ext=ext),
            lbl, id, ext)
