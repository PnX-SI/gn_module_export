import os
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import (
    Blueprint,
    request,
    current_app,
    send_from_directory)
from geonature.utils.env import get_module_id
from geonature.utils.utilssqlalchemy import (
    json_resp, to_json_resp, to_csv_resp)
from pypnusershub.db.tools import InsufficientRightsError
from pypnusershub import routes as fnauth

from .repositories import ExportRepository


logger = current_app.logger
logger.setLevel(logging.DEBUG)

blueprint = Blueprint('exports', __name__)

ASSETS = os.path.join(blueprint.root_path, 'assets')
# extracted from dummy npm install
SWAGGER_UI_DIST_DIR = os.path.join(ASSETS, 'swagger-ui-dist')
SWAGGER_API_YAML = 'api.yaml'

SHAPEFILES_DIR = os.path.join(current_app.static_folder, 'shapefiles')

DEFAULT_SCHEMA = 'gn_exports'
ID_MODULE = get_module_id('exports')


@blueprint.route('/swagger-ui/')
def swagger_ui():
    return send_from_directory(SWAGGER_UI_DIST_DIR, 'index.html')


@blueprint.route('/swagger-ui/<asset>')
def swagger_assets(asset):
    return send_from_directory(SWAGGER_UI_DIST_DIR, asset)


@blueprint.route('/api.yml')
def swagger_api_yml():
    return send_from_directory(ASSETS, SWAGGER_API_YAML)


def export_filename(export):
    return '_'.join(
        [export.get('label'), datetime.now().strftime('%Y_%m_%d_%Hh%Mm%S')])


# TODO: UUIDs
@blueprint.route('/<int:id_export>/<format>', methods=['GET'])
@fnauth.check_auth(2, True)
def export(id_export, format, id_role):

    if id_export < 1:
        return to_json_resp({'error': 'Invalid export id'}, status=404)

    assert format in {'csv', 'json'}

    repo = ExportRepository()
    try:
        export, columns, data = repo.get_by_id(
            id_role, id_export, with_data=True, format=format)
        if export:
            fname = export_filename(export)

            if format == 'json':
                return to_json_resp(
                    data.get('items', None),
                    as_file=True, filename=fname, indent=4)

            if format == 'csv':
                return to_csv_resp(
                    fname, data.get('items', None), columns, ',')

            # if (format == 'shp'):
            #     from geoalchemy2 import Geometry
            #     from geonature.utils.utilsgeometry import ShapeService
            #
            #     shape_service = ShapeService(columns, srid=2150)
            #     shape_service.create_shapes(
            #         data=data.get('items', None),
            #         dir_path=SHAPEFILES_DIR,
            #         file_name=fname,
            #         geom_col=[c for c in data.columns
            #                   if isinstance(c.type, Geometry)][0])
            #
            #     return send_from_directory(dir_path, fname + '.zip', as_attachment=True)  # noqa: E501

    except NoResultFound as e:
        logger.warn('%s', str(e))
        return to_json_resp({'error': 'NoResultFound',
                             'message': str(e)}, status=404)
    except InsufficientRightsError:
        logger.warn('InsufficientRightsError')
        return to_json_resp({'error': 'InsufficientRightsError'}, status=403)
    except Exception as e:
        logger.critical('%s', str(e))
        return to_json_resp({'error': 'LoggedError'}, status=400)


@blueprint.route('/<int:id_export>', methods=['POST', 'PUT'])
@fnauth.check_auth(1, True)
@json_resp
def update(id_export, id_role):
    payload = request.get_json()
    label = payload.get('label', None)
    view_name = payload.get('view_name', None)
    schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
    desc = payload.get('desc', None)

    id_creator = id_role

    if not all(label, schema_name, view_name, desc):
        return {
            'error': 'MissingParameter',
            'message': 'Missing parameter: {}'. format(
                'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa: E501

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
        return {'error': 'NoResultFound',
                'message': str(e)}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'error': 'LoggedError'}, 400
    else:
        return export.as_dict(), 201


@blueprint.route('/<int:id_export>', methods=['DELETE'])
@fnauth.check_auth(3, True)
@json_resp
def delete_export(id_export, id_role):
    repo = ExportRepository()
    try:
        repo.delete(id_role, id_export)
    except NoResultFound as e:
        logger.warn('%s', str(e))
        return {'error': 'NoResultFound',
                'message': str(e)}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'error': 'LoggedError'}, 400
    else:
        return {'result': 'success'}, 204


@blueprint.route('/', methods=['POST', 'PUT'])
@fnauth.check_auth(1, True)
@json_resp
def create(id_role):
    payload = request.get_json()
    label = payload.get('label', None)
    view_name = payload.get('view_name', None)
    schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
    desc = payload.get('desc', None)

    id_creator = id_role

    if not(label and schema_name and view_name):
        return {
            'error': 'MissingParameter',
            'message': 'Missing parameter: {}'. format(
                'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa: E501

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
            return {'error': 'RegisteredLabel',
                    'message': 'Label {} is already registered.'.format(label)}, 400  # noqa: E501
        else:
            logger.critical('%s', str(e))
            raise
    else:
        return export.as_dict(), 201


@blueprint.route('/', methods=['GET'])
@fnauth.check_auth(2, True)
@json_resp
def getExports(id_role):
    repo = ExportRepository()
    try:
        exports = repo.get_list()
    except NoResultFound as e:
        logger.warn('%s', str(e))
        return {'error': 'NoResultFound',
                'message': str(e)}, 204
    else:
        return [export.as_dict() for export in exports]


@blueprint.route('/Collections/')
@json_resp
def getCollections():
    repo = ExportRepository()
    return repo.getCollections()


@blueprint.route('/testview')
def test_view():
    import sqlalchemy
    # from sqlalchemy import orm
    from geonature.utils.env import DB
    from geonature.core.gn_synthese.models import Synthese

    from .utils.exportview import View

    current_app.config['SQLALCHEMY_ECHO'] = True

    metadata = DB.MetaData(schema='gn_exports', bind=DB.engine)

    sample_view = View(
        'sample_view', metadata,
        sqlalchemy.sql.expression.select([
            Synthese.id_synthese,
            Synthese.id_dataset,
            Synthese.the_geom_4326]).select_from(Synthese))

    # orm.mapper(ViewName, v, primary_key=[v.c.id])

    assert sample_view is not None
    assert sample_view.primary_key == [Synthese.id_synthese]
    metadata.create_all(tables=sample_view, checkfirst=False)

    class MyStuff(DB.Model):
        __table__ = sample_view
        __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}

    print('my stuff:', DB.session.query(MyStuff).all())
    metadata.drop_all(tables=sample_view)
