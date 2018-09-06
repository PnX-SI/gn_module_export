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
        return to_json_resp({'api_error': 'InvalidExport'}, status=404)

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
        return to_json_resp({'api_error': 'NoResultFound',
                             'message': str(e)}, status=404)
    except InsufficientRightsError:
        return to_json_resp(
            {'api_error': 'InsufficientRightsError'}, status=403)
    except Exception as e:
        logger.critical('%s', str(e))
        return to_json_resp({'api_error': 'LoggedError'}, status=400)


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
        logger.warn('%s', str(e))
        return {'api_error': 'NoResultFound',
                'message': str(e)}, 404
    except Exception as e:
        logger.critical('%s', str(e))
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

    if not(label and schema_name and view_name):
        return {
            'error': 'MissingParameter',
            'message': 'Missing parameter: {}'. format(
                'label' if not label else 'view name' if not view_name else 'desc')}, 400  # noqa: E501

    repo = ExportRepository()
    try:
        export = repo.create(
            label=label,
            schema_name=schema_name,
            view_name=view_name,
            desc=desc)
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
        exports = repo.get_list()
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
    # Note that the SQLAlchemy Table object is used to represent both
    # tables and views.
    # To introspect a view, create a Table with autoload=True,
    # and then use SQLAlchemy's get_view_definition method to
    # generate the second argument to CreateView.
    import re
    import sqlalchemy
    from geonature.utils.env import DB
    # from .utils.views import View  # , DropView
    from pypnnomenclature.models import TNomenclatures
    from sqlalchemy_views import CreateView, DropView

    def slugify(s):
        # FIXME: regex
        return re.sub(r'([A-Z])', r'_\1', s).lstrip('_').lower()

    def mkStuffView(
            name,
            metadata=DB.MetaData(),
            selectable=sqlalchemy.sql.expression.select([TNomenclatures])):
            # from geonature.core.gn_synthese.models import Synthese
            # selectable = sqlalchemy.sql.expression.select([TNomenclatures])
            # return View('stuff_view', metadata, selectable)

        def mkView(name, metadata, selectable):
            view = DB.Table(name, metadata)
            # logger.debug(selectable.columns)
            CreateView(view, selectable).execute_at('after-create', metadata)
            DropView(view).execute_at('before-drop', metadata)
            return view

        return type(
        name, (DB.Model,), {
            '__table__': mkView(slugify(name), metadata, selectable),
            '__table_args__': {
                'schema': metadata.schema if metadata.schema else DEFAULT_SCHEMA,
                'extend_existing': True,
                'autoload': True,
                'autoload_with': metadata.bind if metadata.bind else DB.engine
                }  # noqa: E133
            })

    # Won't do: StuffView.create(DB.engine) -> !Table
    #           StuffView.__table__.create(DB.engine)

    # if not hasattr(view, '_sa_class_manager'):
    #         orm.mapper(view, view.__view__)

    # after_models = [
    #     m.__name__
    #     for m in DB.Model._decl_class_registry.values()
    #     if hasattr(m, '__name__')]
    # logger.debug(after_models)
    # assert 'StuffView' in after_models
    # raise
    # q = DB.session.query(StuffView)
    # q = DB.session.query(TNomenclatures)

    # [t for t in meta.tables]

    # ERREUR:  le nom de la table « stuff_view » est spécifié plus d'une fois:
    # SELECT gn_exports.stuff_view.id_nomenclature ...
    # FROM gn_exports.stuff_view, gn_exports.stuff_view
    # WHERE gn_exports.stuff_view.id_nomenclature > %(id_nomenclature_1)s
    from .utils.query import ExportQuery
    # from geonature.utils.utilssqlalchemy import GenericQuery

    metadata = DB.MetaData(schema=DEFAULT_SCHEMA, bind=DB.engine)
    StuffView = mkStuffView('StuffView', metadata)
    # metadata.create_all(tables=[StuffView.__table__], bind=DB.engine)
    StuffView.__table__.create()

    assert StuffView.__tablename__ == 'stuff_view'
    assert StuffView.__table__.schema == DEFAULT_SCHEMA

    try:
        # q = GenericQuery(
        q = ExportQuery(
            1,
            DB.session,
            StuffView.__tablename__,
            StuffView.schema if StuffView.schema else DEFAULT_SCHEMA,
            geometry_field=None,
            filters=[('StuffView.id_nomenclature', 'GREATER_THAN', 0)],
            # filters=[('stuff_view.id_nomenclature', 'GREATER_THAN', 0)],
            # filters={'filter_n_up_id_nomenclature': 1},
            limit=0)
        # logger.debug('my stuff: %s', str(q))
        # print(str(q))
        # logger.debug(StuffView.__table_args__)
        res = q.return_query()
        # metadata.drop_all(tables=[StuffView.__table__])
        StuffView.__table__.drop()
        # raise
        return to_json_resp(res)
        # return to_json_resp(q.all())
    except Exception as e:
        StuffView.drop()
        # metadata.drop_all(tables=[StuffView.__table__])
        logger.critical('error: %s', str(e))
