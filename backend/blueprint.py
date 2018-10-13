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
from flask_cors import cross_origin
from geonature.utils.utilssqlalchemy import (
    json_resp, to_json_resp, to_csv_resp)
from geonature.utils.env import get_module_id
from geonature.utils.filemanager import removeDisallowedFilenameChars
from pypnusershub.db.tools import InsufficientRightsError
from pypnusershub import routes as fnauth  # get_or_fetch_user_cruved

from .repositories import ExportRepository, EmptyDataSetError


logger = current_app.logger
logger.setLevel(logging.DEBUG)

blueprint = Blueprint('exports', __name__)

SHAPEFILES_DIR = os.path.join(current_app.static_folder, 'shapefiles')

DEFAULT_SCHEMA = 'gn_exports'
ID_MODULE = get_module_id('exports')

ASSETS = os.path.join(blueprint.root_path, 'assets')
# extracted from dummy npm install
SWAGGER_UI_DIST_DIR = os.path.join(ASSETS, 'swagger-ui-dist')
SWAGGER_UI_SAMPLE_INDEXHTML = 'index.sample.html'
SWAGGER_UI_INDEXHTML = 'index.html'
SWAGGER_API_SAMPLE_YAML = 'api_sample.yaml'
SWAGGER_API_YAML = 'api.yml'

for template, serving in {
        os.path.join(
            ASSETS, SWAGGER_API_SAMPLE_YAML): os.path.join(
                ASSETS, SWAGGER_API_YAML),
        os.path.join(
            ASSETS, SWAGGER_UI_SAMPLE_INDEXHTML): os.path.join(
                SWAGGER_UI_DIST_DIR, SWAGGER_UI_INDEXHTML)
        }.items():
    with open(template, 'r') as input:
        from geonature.utils.utilstoml import load_toml
        content = input.read()
        host, base_path, *_ = current_app.config['API_ENDPOINT']\
                                         .replace('https://', '')\
                                         .replace('http://', '')\
                                         .split('/', 1) + ['']
        for k, v in ({
                'API_ENDPOINT': current_app.config['API_ENDPOINT'],
                'HOST': host,
                'BASE_PATH': '/' + base_path if base_path else '',
                'API_URL': load_toml(
                        os.path.join(
                            blueprint.root_path, '..', 'config',
                            'conf_gn_module.toml')
                    ).get('api_url').lstrip('/'),
                'API_YAML': SWAGGER_API_YAML
                }).items():
            content = content.replace('{{{{{}}}}}'.format(k), v)
        with open(serving, 'w') as output:
            output.write(content)


@blueprint.route('/swagger-ui/')
def swagger_ui():
    return send_from_directory(SWAGGER_UI_DIST_DIR, 'index.html')


@blueprint.route('/swagger-ui/<asset>')
def swagger_assets(asset):
    return send_from_directory(SWAGGER_UI_DIST_DIR, asset)


@blueprint.route('/' + SWAGGER_API_YAML)
def swagger_api_yml():
    return send_from_directory(ASSETS, SWAGGER_API_YAML)


def export_filename(export):
    return '{}_{}'.format(
        removeDisallowedFilenameChars(export.get('label')),
        datetime.now().strftime('%Y_%m_%d_%Hh%Mm%S'))


@blueprint.route('/<int:id_export>/<format>', methods=['GET'])
@cross_origin(
    supports_credentials=True,
    allow_headers=['content-type', 'content-disposition'],
    expose_headers=['Content-Type', 'Content-Disposition', 'Authorization'])
@fnauth.check_auth_cruved('E', True, id_app=ID_MODULE)
def export(id_export, format, info_role):
    if id_export < 1 or format not in {'csv', 'json', 'shp'}:
        return to_json_resp({'api_error': 'InvalidExport'}, status=404)

    try:
        repo = ExportRepository()
        export, columns, data = repo.get_by_id(
            info_role.id_role, id_export, with_data=True, format=format)
        if export:
            fname = export_filename(export)
            has_geometry = export.get('geometry_field', None)

            if format == 'json':
                return to_json_resp(
                    data.get('items', []),
                    as_file=True,
                    filename=fname,
                    indent=4)

            if format == 'csv':
                return to_csv_resp(
                    fname,
                    data.get('items'),
                    [c.name for c in columns],
                    separator=',')

            if (format == 'shp' and has_geometry):
                from geojson.geometry import Point, Polygon, MultiPolygon
                from geonature.utils.utilsgeometry import FionaShapeService as ShapeService  # noqa: E501
                from geonature.utils import filemanager

                filemanager.delete_recursively(
                    SHAPEFILES_DIR, excluded_files=['.gitkeep'])

                ShapeService.create_shapes_struct(
                    db_cols=columns, srid=export.get('geometry_srid'),
                    dir_path=SHAPEFILES_DIR, file_name=fname)

                items = data.get('items')
                for feature in items['features']:
                    geom, props = (feature.get(field)
                                   for field in ('geometry', 'properties'))
                    if isinstance(geom, Point):
                        ShapeService.point_shape.write(feature)
                        ShapeService.point_feature = True

                    elif (isinstance(geom, Polygon)
                          or isinstance(geom, MultiPolygon)):  # noqa: E123 W503
                        ShapeService.polygone_shape.write(props)
                        ShapeService.polygon_feature = True

                    else:
                        ShapeService.polyline_shape.write(props)
                        ShapeService.polyline_feature = True

                ShapeService.save_and_zip_shapefiles()

                return send_from_directory(
                    SHAPEFILES_DIR, fname + '.zip', as_attachment=True)
            else:
                return to_json_resp(
                    {'api_error': 'NonTransformableError'}, status=404)

    except NoResultFound as e:
        return to_json_resp({'api_error': 'NoResultFound',
                             'message': str(e)}, status=404)
    except InsufficientRightsError:
        return to_json_resp(
            {'api_error': 'InsufficientRightsError'}, status=403)
    except EmptyDataSetError as e:
        return to_json_resp(
            {'api_error': 'EmptyDataSetError',
             'message': str(e)}, status=404)
    except Exception as e:
        logger.critical('%s', e)
        # raise
        return to_json_resp({'api_error': 'LoggedError'}, status=400)


@blueprint.route('/', methods=['GET'])
@fnauth.check_auth_cruved('R', True, id_app=ID_MODULE)
@json_resp
def getExports(info_role):
    logger.debug('info_role: %s', info_role)
    repo = ExportRepository()
    # from time import sleep
    # sleep(2)
    try:
        exports = repo.list(id_role=info_role.id_role)
        logger.debug(exports)
    except NoResultFound:
        return {'api_error': 'NoResultFound',
                'message': 'Configure one or more export'}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'api_error': 'LoggedError'}, 400
    else:
        return [export.as_dict() for export in exports]

# @blueprint.route('/<int:id_export>', methods=['POST'])
# @fnauth.check_auth_cruved('U', True, id_app=ID_MODULE)
# @json_resp
# def update(id_export, info_role):
#     payload = request.get_json()
#     label = payload.get('label', None)
#     view_name = payload.get('view_name', None)
#     schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
#     desc = payload.get('desc', None)
#
#     if not all(label, schema_name, view_name, desc):
#         return {
#             'api_error': 'MissingParameter',
#             'message': 'Missing parameter: {}'. format(
#                 'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa: E501
#
#     repo = ExportRepository()
#     try:
#         export = repo.update(
#             id_export=id_export,
#             label=label,
#             schema_name=schema_name,
#             view_name=view_name,
#             desc=desc)
#     except NoResultFound as e:
#         logger.warn('%s', e)
#         return {'api_error': 'NoResultFound',
#                 'message': str(e)}, 404
#     except Exception as e:
#         logger.critical('%s', e)
#         return {'api_error': 'LoggedError'}, 400
#     else:
#         return export.as_dict(), 201
#
#
# @blueprint.route('/<int:id_export>', methods=['DELETE'])
# @fnauth.check_auth_cruved('D', True, id_app=ID_MODULE)
# @json_resp
# def delete_export(id_export, info_role):
#     repo = ExportRepository()
#     try:
#         repo.delete(info_role.id_role, id_export)
#     except NoResultFound as e:
#         logger.warn('%s', str(e))
#         return {'api_error': 'NoResultFound',
#                 'message': str(e)}, 404
#     except Exception as e:
#         logger.critical('%s', str(e))
#         return {'api_error': 'LoggedError'}, 400
#     else:
#         # return '', 204 -> 404 client side, interceptors ?
#         return {'result': 'success'}, 204
#
#
# @blueprint.route('/', methods=['POST'])
# @fnauth.check_auth_cruved('C', True, id_app=ID_MODULE)
# @json_resp
# def create(info_role):
#     payload = request.get_json()
#     label = payload.get('label', None)
#     view_name = payload.get('view_name', None)
#     schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
#     desc = payload.get('desc', None)
#     geometry_field = payload.get('geometry_field'),
#     geometry_srid = payload.get('geometry_srid')
#
#     if not(label and schema_name and view_name):
#         return {
#             'error': 'MissingParameter',
#             'message': 'Missing parameter: {}'. format(
#                 'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa: E501
#
#     repo = ExportRepository()
#     try:
#         export = repo.create({
#             'label': label,
#             'schema_name': schema_name,
#             'view_name': view_name,
#             'desc': desc,
#             'geometry_field': geometry_field,
#             'geometry_srid': geometry_srid})
#     except IntegrityError as e:
#         if '(label)=({})'.format(label) in str(e):
#             return {'api_error': 'RegisteredLabel',
#                     'message': 'Label {} is already registered.'.format(label)}, 400  # noqa: E501
#         else:
#             logger.critical('%s', str(e))
#             raise
#     else:
#         return export.as_dict(), 201
