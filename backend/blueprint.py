"""
    Définition des routes du module export
"""

import os
import logging
import threading
import json

from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import ForeignKeyViolation

from flask import (
    Blueprint,
    request,
    current_app,
    send_from_directory,
    Response,
    render_template,
    jsonify,
    flash,
    copy_current_request_context,
)
from flask_cors import cross_origin
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import is_form_submitted
from flask_admin.babel import gettext
from wtforms import validators, IntegerField

from pypnusershub.db.models import User

from geonature.core.admin.admin import admin as flask_admin, CruvedProtectedMixin
from utils_flask_sqla.response import json_resp, to_json_resp


from utils_flask_sqla.generic import GenericQuery
from utils_flask_sqla_geo.generic import GenericQueryGeo

from geonature.core.gn_permissions import decorators as permissions
from geonature.utils.env import DB


from .repositories import (
    ExportRepository,
    EmptyDataSetError,
    generate_swagger_spec,
    get_allowed_exports,
)
from .models import Export, CorExportsRoles, Licences, ExportSchedules, UserRepr
from .utils_export import thread_export_data
from .commands.geonature_cmd import commands

LOGGER = current_app.logger
LOGGER.setLevel(logging.DEBUG)

blueprint = Blueprint("exports", __name__)
blueprint.template_folder = os.path.join(blueprint.root_path, "templates")
blueprint.static_folder = os.path.join(blueprint.root_path, "static")


"""
#################################################################
    Commandes
#################################################################
"""


blueprint.cli.short_help = "Commandes du module export"
for cmd in commands:
    blueprint.cli.add_command(cmd)



"""
#################################################################
    Configuration de l'admin
#################################################################
"""


class LicenceView(CruvedProtectedMixin, ModelView):
    """
    Surcharge de l'administration des licences
    """
    module_code = "EXPORTS"
    object_code = None

    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(LicenceView, self).__init__(Licences, session, **kwargs)

    # exclusion du champ exports
    form_excluded_columns = "exports"
    # Nom de colonne user friendly
    column_labels = dict(
        name_licence="Nom de la licence", url_licence="Description de la licence"
    )
    # Description des colonnes
    column_descriptions = dict(
        name_licence="Nom de la licence",
        url_licence="URL de la documentation de la licence",
    )


class ExportRoleView(CruvedProtectedMixin, ModelView):
    """
    Surcharge de l'administration de l'association role/export
    """
    module_code = "EXPORTS"
    object_code = None

    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(ExportRoleView, self).__init__(CorExportsRoles, session, **kwargs)

    # Nom de colonne user friendly
    column_labels = dict(export="Nom de l'export", role="Nom du role")
    # Description des colonnes
    column_descriptions = dict(role="Role associé à l'export")
    # Surcharge du formulaure
    form_args = {
        "role": {
            "query_factory": lambda: UserRepr.query.order_by(
                UserRepr.groupe.desc(), UserRepr.nom_role
            ).filter((UserRepr.groupe == True) | (UserRepr.identifiant.isnot(None)))
        }
    }


class ExportView(CruvedProtectedMixin, ModelView):
    """
    Surcharge du formulaire d'administration Export
    """
    module_code = "EXPORTS"
    object_code = None

    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(ExportView, self).__init__(Export, session, **kwargs)

    # Ordonne les colonnes pour avoir la licence à la fin de la liste
    column_list = [
        "id",
        "label",
        "schema_name",
        "view_name",
        "desc",
        "geometry_field",
        "geometry_srid",
        "public",
        "licence",
    ]
    # Nom de colonne user friendly
    column_labels = dict(
        id="Identifiant",
        label="Nom de l'export",
        schema_name="Nom du schema PostgreSQL",
        view_name="Nom de la vue SQL",
        desc="Description",
        geometry_field="Nom de champ géométrique",
        geometry_srid="SRID du champ géométrique",
    )
    # Description des colonnes
    column_descriptions = dict(
        label="Nom libre de l'export",
        schema_name="Nom exact du schéma postgreSQL contenant la vue SQL.",
        view_name="Nom exact de la vue SQL permettant l'export de vos données.",  # noqa E501
        desc="Décrit la nature de l'export",
        public="L'export est accessible à tous",
    )
    # Ordonne des champs pour avoir la licence à la fin du formulaire
    form_columns = (
        "label",
        "schema_name",
        "view_name",
        "desc",
        "geometry_field",
        "geometry_srid",
        "public",
        "licence",
    )

    def validate_form(self, form):
        """
        Validation personnalisée du form
        """
        # Essai de récupérer en BD la vue sql déclarée
        # Delete n'a pas d'attribut view_name
        view_name = getattr(form, "view_name", "")
        schema_name = getattr(form, "schema_name", "")
        geometry_field = getattr(form, "geometry_field", None)
        geometry_srid = getattr(form, "geometry_srid", None)
        if is_form_submitted() and view_name and schema_name:
            try:
                if geometry_field.data and geometry_srid.data is None:
                    raise KeyError(
                        "Field Geometry SRID is mandatory with Geometry field"
                    )

                query = GenericQueryGeo(
                    DB,
                    view_name.data,
                    schema_name.data,
                    geometry_field=geometry_field.data,
                    filters=[],
                )
                query.return_query()

            except Exception as exp:
                flash(exp, category="error")
                return False

        return super(ExportView, self).validate_form(form)

    def handle_view_exception(self, exc):
        """
            Customisation du message d'erreur en cas de suppresion de l'export
            s'il est toujours référencé dans les tables de logs
        """
        if isinstance(exc, IntegrityError):
            if isinstance(exc.orig, ForeignKeyViolation):
                flash(gettext("L'export ne peut pas être supprimé car il est toujours référencé (table de log)"), 'error')
                return True

        return super(ModelView, self).handle_view_exception(exc)


class ExportSchedulesView(CruvedProtectedMixin, ModelView):
    """
    Surcharge de l'administration de l'export Schedules
    """
    module_code = "EXPORTS"
    object_code = None

    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(ExportSchedulesView, self).__init__(ExportSchedules, session, **kwargs)

    # Description des colonnes
    column_descriptions = dict(
        export="Nom de l'export à planifier",
        frequency="Fréquence de la génération de l'export (en jours)",
        format="Format de l'export à générer",
    )

    form_args = {
        "export": {"validators": [validators.Required()]},
        "frequency": {"validators": [validators.NumberRange(1, 365)]},
    }

    if "EXPORTS" in current_app.config:
        format_list = [
            (k, k) for k in current_app.config["EXPORTS"]["export_format_map"].keys()
        ]
        form_choices = {"format": format_list}


# Add views
flask_admin.add_view(ExportView(DB.session, name="Exports", category="Export"))
flask_admin.add_view(
    ExportRoleView(DB.session, name="Associer un rôle à un export", category="Export")
)
flask_admin.add_view(LicenceView(DB.session, name="Licences", category="Export"))
flask_admin.add_view(
    ExportSchedulesView(DB.session, name="Planification des exports", category="Export")
)


"""
#################################################################
    Configuration de Swagger
#################################################################
"""


@blueprint.route("/swagger/")
@blueprint.route("/swagger/<int:id_export>", methods=["GET"])
def swagger_ui(id_export=None):
    """
    Génération de l'interface de Swagger
    """
    if not id_export:
        id_export = ""

    return render_template(
        "index.html",
        API_ENDPOINT=(
            current_app.config["API_ENDPOINT"]
            + current_app.config["EXPORTS"]["MODULE_URL"]
        ),
        id_export=id_export,
    )


@blueprint.route("/swagger-ressources/", methods=["GET"])
@blueprint.route("/swagger-ressources/<int:id_export>", methods=["GET"])
def swagger_ressources(id_export=None):
    """
    Génération des spécifications Swagger
    """

    # return jsonify(swagger_example)
    if not id_export:
        swagger_spec = render_template("/swagger/main_swagger_doc.json")
        return Response(swagger_spec)

    # Si l'id export existe et que les droits sont définis
    try:
        export = Export.query.filter(Export.id == id_export).one()
    except (NoResultFound, EmptyDataSetError):
        return jsonify({"message": "no export with this id"}), 404

    # Si un fichier de surcouche est défini
    file_name = "api_specification_" + str(id_export) + ".json"
    path = Path(blueprint.template_folder, "swagger", file_name)

    if path.is_file():
        swagger_spec = render_template("/swagger/" + file_name)
        return Response(swagger_spec)

    # Génération automatique des spécifications
    export_parameters = generate_swagger_spec(id_export)

    # Récupération des paramètres URL du backend
    backend_url = urlparse(current_app.config["API_ENDPOINT"])

    if backend_url.scheme:
        scheme = [backend_url.scheme]
    else:
        scheme = ["https", "http"]

    swagger_spec = render_template(
        "/swagger/generic_swagger_doc.json",
        export_nom=export.label,
        export_description=export.desc,
        export_path="{}/api/{}".format(
            current_app.config["EXPORTS"]["MODULE_URL"], id_export
        ),
        export_parameters=export_parameters,
        licence_nom=export.licence.name_licence,
        licence_description=export.licence.url_licence,
        host=backend_url.netloc,
        base_path=backend_url.path,
        schemes=scheme,
    )

    return Response(swagger_spec)


"""
#################################################################
    Configuration des routes qui permettent de réaliser les exports
#################################################################
"""


@blueprint.route("/<int:id_export>/<export_format>", methods=["POST"])
@cross_origin(
    supports_credentials=True,
    allow_headers=["content-type", "content-disposition"],
    expose_headers=["Content-Type", "Content-Disposition", "Authorization"],
)
@permissions.check_cruved_scope(
    "E",
    True,
    module_code="EXPORTS"
)
def getOneExportThread(id_export, export_format, info_role):
    """
    Run export with thread
    """
    # Test if export exists
    if (
        id_export < 1
        or export_format not in current_app.config["EXPORTS"]["export_format_map"]
    ):
        return to_json_resp(
            {
                "api_error": "invalid_export",
                "message": "Invalid export or export not found",
            },
            status=404,
        )

    filters = {f: request.args.get(f) for f in request.args}
    data = dict(request.get_json())

    # Alternative email in payload
    email_to = None
    if "email" in data:
        email_to = data["email"]

    try:

        @copy_current_request_context
        def get_data(id_export, export_format, info_role, filters, email_to):
            thread_export_data(id_export, export_format, info_role, filters, email_to)

        exp = ExportRepository(id_export)
        # Test if export is allowed
        try:
            exp.get_export_is_allowed(info_role)
        except Exception as e:
            return to_json_resp({"message": "Not Allowed"}, status=403)

        # Test if user have an email
        try:
            user = (
                DB.session.query(User).filter(User.id_role == info_role.id_role).one()
            )
            if not user.email and not email_to:  # TODO add more test
                return to_json_resp(
                    {
                        "api_error": "no_email",
                        "message": "User doesn't have email",
                    },  # noqa 501
                    status=500,
                )
        except NoResultFound:
            return to_json_resp(
                {"api_error": "no_user", "message": "User doesn't exist"}, status=404
            )

        # Run export
        a = threading.Thread(
            name="export_data",
            target=get_data,
            kwargs={
                "id_export": id_export,
                "export_format": export_format,
                "info_role": info_role,
                "filters": filters,
                "email_to": [email_to] if (email_to) else [user.email],
            },
        )
        a.start()

        return to_json_resp(
            {
                "api_success": "in_progress",
                "message": "The Process is in progress ! You will receive an email shortly",  # noqa 501
            },
            status=200,
        )

    except Exception as e:
        LOGGER.critical("%s", e)
        if current_app.config["DEBUG"]:
            raise
        return to_json_resp({"api_error": "logged_error"}, status=400)


@blueprint.route("/", methods=["GET"])
@permissions.check_cruved_scope(
    "R",
    True,
    module_code="EXPORTS"
)
@json_resp
def getExports(info_role):
    """
    Fonction qui renvoie la liste des exports
    accessibles pour un role donné
    """
    try:
        exports = get_allowed_exports(info_role)
    except NoResultFound:
        return {
            "api_error": "no_result_found",
            "message": "Configure one or more export",
        }, 404
    except Exception as e:
        LOGGER.critical("%s", str(e))
        return {"api_error": "logged_error"}, 400
    else:

        return [export.as_dict(fields=["licence"]) for export in exports]


@blueprint.route("/api/<int:id_export>", methods=["GET"])
@permissions.check_cruved_scope(
    "R",
    True,
    module_code="EXPORTS"
)
@json_resp
def get_one_export_api(id_export, info_role):
    """
    Fonction qui expose les exports disponibles à un role
        sous forme d'api

    Le requetage des données se base sur la classe GenericQuery qui permet
        de filter les données de façon dynamique en respectant des
        conventions de nommage

    Parameters
    ----------
    limit : nombre limite de résultats à retourner
    offset : numéro de page

    FILTRES :
        nom_col=val: Si nom_col fait partie des colonnes
            de la vue alors filtre nom_col=val
        ilikenom_col=val: Si nom_col fait partie des colonnes
            de la vue et que la colonne est de type texte
            alors filtre nom_col ilike '%val%'
        filter_d_up_nom_col=val: Si nom_col fait partie des colonnes
            de la vue et que la colonne est de type date
            alors filtre nom_col >= val
        filter_d_lo_nom_col=val: Si nom_col fait partie des colonnes
            de la vue et que la colonne est de type date
            alors filtre nom_col <= val
        filter_d_eq_nom_col=val: Si nom_col fait partie des colonnes
            de la vue et que la colonne est de type date
            alors filtre nom_col == val
        filter_n_up_nom_col=val: Si nom_col fait partie des colonnes
            de la vue et que la colonne est de type numérique
            alors filtre nom_col >= val
        filter_n_lo_nom_col=val: Si nom_col fait partie des colonnes
            de la vue et que la colonne est de type numérique
            alors filtre nom_col <= val
    ORDONNANCEMENT :
        orderby: char
            Nom du champ sur lequel baser l'ordonnancement
        order: char (asc|desc)
            Sens de l'ordonnancement

    Returns
    -------
    json
    {
        'total': Nombre total de résultats,
        'total_filtered': Nombre total de résultats après filtration,
        'page': Numéro de la page retournée,
        'limit': Nombre de résultats,
        'items': Données au format Json ou GeoJson
    }


        order by : @TODO
    """
    exprep = ExportRepository(id_export)

    # Test if export is allowed
    try:
        exprep.get_export_is_allowed(info_role)
    except Exception:
        return ({"message": "Not Allowed"}, 403)

    limit = request.args.get("limit", default=1000, type=int)
    offset = request.args.get("offset", default=0, type=int)

    args = request.args.to_dict()
    if "limit" in args:
        args.pop("limit")
    if "offset" in args:
        args.pop("offset")
    filters = {f: args.get(f) for f in args}

    (export, columns, data) = exprep.get_export_with_logging(
        info_role, with_data=True, filters=filters, limit=limit, offset=offset
    )
    return data


try:
    expose_api = current_app.config.get("EXPORTS").get("expose_dsw_api")
except AttributeError:
    # test permettant de s'assurer que la configuration du module soit accessible
    LOGGER.info("Configuration du module non accéssible (installation en cours)")
else:
    if expose_api:

        @blueprint.route("/semantic_dsw", methods=["GET"])
        def semantic_dsw():
            """
            Fonction qui expose un export RDF basé sur le vocabulaire Darwin-SW
                sous forme d'api

            Le requetage des données se base sur la classe GenericQuery qui permet
                de filter les données de façon dynamique en respectant des
                conventions de nommage

            Parameters
            ----------
            limit : nombre limite de résultats à retourner
            offset : numéro de page

            FILTRES :
                nom_col=val: Si nom_col fait partie des colonnes
                    de la vue alors filtre nom_col=val

            Returns
            -------
            turle
            """
            conf = current_app.config.get("EXPORTS")
            export_dsw_dir = conf.get("export_dsw_dir")
            export_dsw_fullpath = str(
                Path(conf.get("export_dsw_dir"), conf.get("export_dsw_filename"))
            )
            os.makedirs(export_dsw_dir, exist_ok=True)

            if not export_dsw_fullpath:
                return to_json_resp(
                    {
                        "api_error": "dws_disabled",
                        "message": "Darwin-SW export is disabled",
                    },
                    status=501,
                )

            from .rdf import generate_store_dws

            limit = request.args.get("limit", default=1000, type=int)
            offset = request.args.get("offset", default=0, type=int)

            args = request.args.to_dict()
            if "limit" in args:
                args.pop("limit")
            if "offset" in args:
                args.pop("offset")
            filters = {f: args.get(f) for f in args}

            store = generate_store_dws(limit, offset, filters)
            try:
                with open(export_dsw_fullpath, "w+b") as xp:
                    store.save(store_uri=xp)
            except FileNotFoundError:
                response = Response(
                    response="FileNotFoundError : {}".format(export_dsw_fullpath),
                    status=500,
                    mimetype="application/json",
                )
                return response

            return send_from_directory(
                os.path.dirname(export_dsw_fullpath), os.path.basename(export_dsw_fullpath)
            )
