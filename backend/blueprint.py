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
# from flask_cors import CORS, cross_origin
from geonature.utils.utilssqlalchemy import (
    json_resp, to_json_resp, to_csv_resp)
from geonature.utils.filemanager import removeDisallowedFilenameChars
from pypnusershub.db.tools import InsufficientRightsError
from pypnusershub import routes as fnauth

from .repositories import ExportRepository


logger = current_app.logger
logger.setLevel(logging.DEBUG)

blueprint = Blueprint('exports', __name__)
# CORS(blueprint,
#      supports_credentials=True)
#      allow_headers=['content-type', 'content-disposition'],
#      expose_headers=['Content-Type', 'Content-Disposition'])

ASSETS = os.path.join(blueprint.root_path, 'assets')
# extracted from dummy npm install
SWAGGER_UI_DIST_DIR = os.path.join(ASSETS, 'swagger-ui-dist')
SWAGGER_API_YAML = 'api.yaml'

SHAPEFILES_DIR = os.path.join(current_app.static_folder, 'shapefiles')

DEFAULT_SCHEMA = 'gn_exports'


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
    return '_'.join([
        removeDisallowedFilenameChars(export.get('label')),
        datetime.now().strftime('%Y_%m_%d_%Hh%Mm%S')])


# TODO: UUIDs
# @cross_origin(expose_headers=["Content-Type", "Content-Disposition"])
@blueprint.route('/<int:id_export>/<format>', methods=['GET'])
# @fnauth.check_auth(2, True)
def export(id_export, format, id_role=1):
    if id_export < 1:
        return to_json_resp({'api_error': 'InvalidExport'}, status=404)

    try:
        assert format in {'csv', 'json', 'shp'}
        repo = ExportRepository()
        export, columns, data = repo.get_by_id(
            id_role, id_export, with_data=True, format=format)
        if export:
            fname = export_filename(export)
            geometry = export.get('geometry_field')

            # resp.headers['Access-Control-Allow-Headers'] += 'content-disposition'  # noqa: E501
            # resp.headers['Access-Control-Expose-Headers'] += 'Content-Disposition'  # noqa: E501
            if format == 'json':
                return to_json_resp(
                    data.get('items', None),
                    as_file=True, filename=fname, indent=4)

            if format == 'csv':
                return to_csv_resp(
                    fname,
                    data.get('items'),
                    [c.name for c in columns],
                    separator=',')

            if (format == 'shp' and geometry):
                from geojson.geometry import Point, Polygon, MultiPolygon
                from geonature.utils.utilsgeometry import FionaShapeService as ShapeService  # noqa: E501

                ShapeService.create_shapes_struct(
                    db_cols=columns, srid=export.get('geometry_srid'),
                    dir_path=SHAPEFILES_DIR, file_name=fname)

                items = data.get('items')
                for feature in items['features']:
                    logger.debug('feature: %s', feature)
                    geom, props = (feature.get(field)
                                   for field in ('geometry', 'properties'))
                    if isinstance(geom, Point):
                        ShapeService.point_shape.write(feature)
                        ShapeService.point_feature = True
                    elif (isinstance(geom, Polygon)
                          or isinstance(geom, MultiPolygon)):
                        ShapeService.polygone_shape.write(props)
                        ShapeService.polygon_feature = True
                    else:
                        ShapeService.polyline_shape.write(props)
                        ShapeService.polyline_feature = True

                ShapeService.save_and_zip_shapefiles()

                return send_from_directory(
                    SHAPEFILES_DIR, fname + '.zip', as_attachment=True)

    except NoResultFound as e:
        return to_json_resp({'api_error': 'NoResultFound',
                             'message': str(e)}, status=404)
    except InsufficientRightsError:
        return to_json_resp(
            {'api_error': 'InsufficientRightsError'}, status=403)
    except Exception as e:
        logger.critical('%s', e)
        raise
        return to_json_resp({'api_error': 'LoggedError'}, status=400)
        # return render_template(
        #     'error.html',
        #     error=message,
        #     redirect=current_app.config['URL_APPLICATION']+"/#/exports"
        # )


@blueprint.route('/<int:id_export>', methods=['POST', 'PUT'])
@fnauth.check_auth(1, True)
@json_resp
def update(id_export, id_role):
    payload = request.get_json()
    label = payload.get('label', None)
    view_name = payload.get('view_name', None)
    schema_name = payload.get('schema_name', DEFAULT_SCHEMA)
    desc = payload.get('desc', None)

    if not all(label, schema_name, view_name, desc):
        return {
            'error': 'MissingParameter',
            'message': 'Missing parameter: {}'. format(
                'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa: E501

    repo = ExportRepository()
    try:
        export = repo.update(
            id_export=id_export,
            label=label,
            schema_name=schema_name,
            view_name=view_name,
            desc=desc)
    except NoResultFound as e:
        logger.warn('%s', e)
        return {'api_error': 'NoResultFound',
                'message': str(e)}, 404
    except Exception as e:
        logger.critical('%s', e)
        return {'api_error': 'LoggedError'}, 400
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
        return {'api_error': 'NoResultFound',
                'message': str(e)}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'api_error': 'LoggedError'}, 400
    else:
        # return '', 204 -> 404 client side, interceptors ?
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
    geometry_field = payload.get('geometry_field'),
    geometry_srid = payload.get('geometry_srid')

    if not(label and schema_name and view_name):
        return {
            'error': 'MissingParameter',
            'message': 'Missing parameter: {}'. format(
                'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa: E501

    repo = ExportRepository()
    try:
        export = repo.create({
            'label': label,
            'schema_name': schema_name,
            'view_name': view_name,
            'desc': desc,
            'geometry_field': geometry_field,
            'geometry_srid': geometry_srid})
    except IntegrityError as e:
        if '(label)=({})'.format(label) in str(e):
            return {'api_error': 'RegisteredLabel',
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
        exports = repo.list()
        logger.debug(exports)
    except NoResultFound:
        return {'api_error': 'NoResultFound',
                'message': 'Configure one or more export'}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'api_error': 'LoggedError'}, 400
    else:
        return [export.as_dict() for export in exports]


@blueprint.route('/Collections/')
@json_resp
def getCollections():
    repo = ExportRepository()
    return repo.getCollections()


@blueprint.route('/testview')
def test_view():
    import re
    import sqlalchemy
    from geonature.utils.env import DB
    from .utils.views import mkView
    from .utils.query import ExportQuery
    from pypnnomenclature.models import TNomenclatures

    def slugify(s):
        # FIXME: slugify
        return re.sub(r'([A-Z ])', r'_\1', s).lstrip('_')\
                                             .replace(' ', '')\
                                             .lower()

    metadata = DB.MetaData(schema=DEFAULT_SCHEMA, bind=DB.engine)
    _tname = slugify('StuffView')
    StuffView = mkView(
            _tname, metadata,
            sqlalchemy.sql.expression.select([TNomenclatures]))
    metadata.create_all()
    assert StuffView.__tablename__ == 'stuff_view' == _tname

    try:
        # from geonature.utils.utilssqlalchemy import GenericQuery
        # q = GenericQuery(
        q = ExportQuery(
            1,
            DB.session,
            StuffView.__tablename__,
            StuffView.__table__.schema if getattr(StuffView.__table__, 'schema', None) else DEFAULT_SCHEMA,  # noqa: E501
            geometry_field=None,
            filters=[('id_nomenclature', 'GREATER_THAN', 0)],
            # filters={'filter_n_up_id_nomenclature': 1},
            limit=1000)
        # res = q.return_query()
        # metadata.drop_all(tables=[StuffView.__table__])
        # return to_json_resp(res)
        return to_json_resp(q.return_query())
    except Exception as e:
        # StuffView.__table__.drop() ... hmmmmmm, nope
        # metadata.drop_all(tables=[StuffView.__table__])
        logger.critical('error: %s', str(e))
        raise
        return to_json_resp({'error': str(e)}, status=400)
