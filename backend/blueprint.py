import os
from datetime import datetime
import logging
from sqlalchemy.orm.exc import NoResultFound
from flask import (
    Blueprint,
    request,
    current_app,
    send_from_directory, 
    Response
)
from flask_cors import cross_origin
from geonature.utils.utilssqlalchemy import (
    json_resp, to_json_resp, to_csv_resp)
from geonature.utils.utilstoml import load_toml, load_and_validate_toml
from geonature.utils.filemanager import (
    removeDisallowedFilenameChars, delete_recursively)
from pypnusershub.db.tools import InsufficientRightsError
from geonature.core.gn_permissions import decorators as permissions

from .repositories import ExportRepository, EmptyDataSetError

from flask_admin.contrib.sqla import ModelView
from .models import Export, CorExportsRoles
from pypnnomenclature.admin import admin
from geonature.utils.env import DB

logger = current_app.logger
logger.setLevel(logging.DEBUG)
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
# current_app.config['DEBUG'] = True

blueprint = Blueprint('exports', __name__)
repo = ExportRepository()


"""
    Configuration de l'admin
"""

admin.add_view(ModelView(Export, DB.session))
admin.add_view(ModelView(CorExportsRoles, DB.session))

EXPORTS_DIR = os.path.join(current_app.static_folder, 'exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)
SHAPEFILES_DIR = os.path.join(current_app.static_folder, 'shapefiles')
MOD_CONF_PATH = os.path.join(blueprint.root_path, os.pardir, 'config')

#HACK when install the module, the config of the module is not yet available
# we cannot use current_app.config['EXPORT']
try:
    MOD_CONF = current_app.config['EXPORTS']
    API_URL = MOD_CONF['MODULE_URL']
except KeyError:
    API_URL = ''

ASSETS = os.path.join(blueprint.root_path, 'assets')

# extracted from dummy npm install
SWAGGER_UI_DIST_DIR = os.path.join(ASSETS, 'swagger-ui-dist')
SWAGGER_UI_SAMPLE_INDEXHTML = 'swagger-ui_index.template.html'
SWAGGER_UI_INDEXHTML = 'index.html'
SWAGGER_API_SAMPLE_YAML = 'swagger-ui_api.template.yml'
SWAGGER_API_YAML = 'api.yml'

for template, serving in {
        os.path.join(
            MOD_CONF_PATH, SWAGGER_API_SAMPLE_YAML): os.path.join(
                ASSETS, SWAGGER_API_YAML),
        os.path.join(
            MOD_CONF_PATH, SWAGGER_UI_SAMPLE_INDEXHTML): os.path.join(
                SWAGGER_UI_DIST_DIR, SWAGGER_UI_INDEXHTML)
        }.items():
    with open(template, 'r') as input_:
        content = input_.read()
        host, base_path, *_ = current_app.config['API_ENDPOINT']\
                                         .replace('https://', '')\
                                         .replace('http://', '')\
                                         .split('/', 1) + ['']
        for k, v in ({
                'API_ENDPOINT': current_app.config['API_ENDPOINT'],
                'HOST': host,
                'BASE_PATH': '/' + base_path if base_path else '',
                'API_URL': API_URL.lstrip('/') if API_URL else '',
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


@blueprint.route('/<int:id_export>/<export_format>', methods=['GET'])
@cross_origin(
    supports_credentials=True,
    allow_headers=['content-type', 'content-disposition'],
    expose_headers=['Content-Type', 'Content-Disposition', 'Authorization'])
@permissions.check_cruved_scope(
    'E', True, module_code='EXPORTS',
    redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
    redirect_on_invalid_token=current_app.config.get('URL_APPLICATION')
    )
def getOneExport(id_export, export_format, info_role):
    if (id_export < 1
            or export_format not in blueprint.config.get('export_format_map')):
        return to_json_resp({'api_error': 'InvalidExport'}, status=404)

    current_app.config.update(
        export_format_map=blueprint.config['export_format_map'])
    filters = {f: request.args.get(f) for f in request.args}
    try:
        export, columns, data = repo.get_by_id(
            info_role, id_export, with_data=True, export_format=export_format,
            filters=filters, limit=10000, offset=0)

        if export:
            fname = export_filename(export)
            has_geometry = export.get('geometry_field', None)

            if export_format == 'json':
                return to_json_resp(
                    data.get('items'),
                    as_file=True,
                    filename=fname,
                    indent=4)

            if export_format == 'csv':
                return to_csv_resp(
                    fname,
                    data.get('items'),
                    [c.name for c in columns],
                    separator=',')

            if (export_format == 'shp' and has_geometry):
                from geoalchemy2.shape import from_shape
                from shapely.geometry import asShape
                from geonature.utils.utilsgeometry import FionaShapeService as ShapeService  # noqa: E501

                delete_recursively(
                    SHAPEFILES_DIR, excluded_files=['.gitkeep'])

                ShapeService.create_shapes_struct(
                    db_cols=columns, srid=export.get('geometry_srid'),
                    dir_path=SHAPEFILES_DIR, file_name=''.join(['export_', fname]))  # noqa: E501

                items = data.get('items')

                for feature in items['features']:
                    geom, props = (feature.get(field)
                                   for field in ('geometry', 'properties'))

                    ShapeService.create_feature(
                            props, from_shape(
                                asShape(geom), export.get('geometry_srid')))

                ShapeService.save_and_zip_shapefiles()

                return send_from_directory(
                    SHAPEFILES_DIR, ''.join(['export_', fname, '.zip']),
                    as_attachment=True)

            else:
                return to_json_resp(
                    {'api_error': 'NonTransformableError'}, status=404)

    except NoResultFound as e:
        return to_json_resp(
            {'api_error': 'NoResultFound',
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
        if current_app.config['DEBUG']:
            raise
        return to_json_resp({'api_error': 'LoggedError'}, status=400)


@blueprint.route('/', methods=['GET'])
@permissions.check_cruved_scope(
    'R', True, module_code='EXPORTS',
    redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
    redirect_on_invalid_token=current_app.config.get('URL_APPLICATION')
    )
@json_resp
def getExports(info_role):
    try:
        exports = repo.getAllowedExports(info_role)
    except NoResultFound:
        return {'api_error': 'NoResultFound',
                'message': 'Configure one or more export'}, 404
    except Exception as e:
        logger.critical('%s', str(e))
        return {'api_error': 'LoggedError'}, 400
    else:
        return [export.as_dict() for export in exports]


@blueprint.route('/etalab', methods=['GET'])
def etalab_export():
    if not blueprint.config.get('etalab_export'):
        return to_json_resp(
            {'api_error': 'EtalabDisabled',
             'message': 'Etalab export is disabled'}, status=501)

    from datetime import time
    from geonature.utils.env import DB
    from geonature.utils.utilssqlalchemy import GenericQuery
    from .rdf import OccurrenceStore
    
    conf = current_app.config.get('EXPORTS')
    export_etalab = conf.get('etalab_export')
    seeded = False
    if os.path.isfile(export_etalab):
        seeded = True
        midnight = datetime.combine(datetime.today(), time.min)
        mtime = datetime.fromtimestamp(os.path.getmtime(export_etalab))
        ts_delta = mtime - midnight

    if not seeded or ts_delta.total_seconds() < 0:
        store = OccurrenceStore()
        query = GenericQuery(
            DB.session, 'export_occtax_sinp', 'pr_occtax',
            geometry_field=None, filters=[]
        )
        data = query.return_query()
        for record in data.get('items'):
            event = store.build_event(record)
            obs = store.build_human_observation(event, record)
            store.build_location(obs, record)
            occurrence = store.build_occurrence(event, record)
            organism = store.build_organism(occurrence, record)
            identification = store.build_identification(organism, record)
            store.build_taxon(identification, record)
        try:
            with open(export_etalab, 'w+b') as xp:
                store.save(store_uri=xp)
        except FileNotFoundError as e:
            response = Response(
                response="FileNotFoundError : {}".format(
                    export_etalab
                ),
                status=500,
                mimetype='application/json'
            )
            return response
        

    return send_from_directory(
        os.path.dirname(export_etalab), os.path.basename(export_etalab)
    )
