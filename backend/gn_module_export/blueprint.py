"""
    Définition des routes du module export
"""

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import contains_eager

from flask import (
    Blueprint,
    Response,
    current_app,
    g,
    jsonify,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_cors import cross_origin
from geonature.core.gn_permissions import decorators as permissions
from geonature.core.gn_permissions.tools import get_scopes_by_action


from gn_module_export.repositories import generate_swagger_spec
from geonature.utils.config import config_frontend as public_config
from gn_module_export.commands import commands
from gn_module_export.models import Export
from gn_module_export.repositories import generate_swagger_spec
from gn_module_export.tasks import generate_export
from gn_module_export.schemas import ExportSchema
from .utils_export import ExportRequest
from sqlalchemy.orm.exc import NoResultFound
from utils_flask_sqla.response import json_resp, to_json_resp
from werkzeug.exceptions import Forbidden

LOGGER = current_app.logger
LOGGER.setLevel(logging.DEBUG)

blueprint = Blueprint("exports", __name__, cli_group="exports")

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

from .admin import *

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
            current_app.config["API_ENDPOINT"] + current_app.config["EXPORTS"]["MODULE_URL"]
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
    except NoResultFound:
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
        export_path="{}/api/{}".format(current_app.config["EXPORTS"]["MODULE_URL"], id_export),
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
@permissions.check_cruved_scope("R", module_code="EXPORTS", get_scope=True)
def getOneExportThread(scope, id_export, export_format):
    """
    Run export with thread
    """

    filters = {f: request.args.get(f) for f in request.args}
    user = g.current_user

    # Test format
    if export_format not in current_app.config["EXPORTS"]["export_format_map"]:
        return to_json_resp(
            {
                "api_error": "invalid_export",
                "message": "Invalid export format",
            },
            status=500,
        )

    export_request = ExportRequest(id_export=id_export, user=user, format=export_format)

    generate_export.delay(
        export_id=export_request.export.id,
        file_name=str(export_request.get_full_path_file_name()),
        export_url=export_request.get_export_url(),
        format=export_request.format,
        id_role=user.id_role,
        filters=filters,
    )

    return to_json_resp(
        {
            "api_success": "in_progress",
            "message": "La génération du fichier est en cours ! Vous recevrez une notification quand le fichier sera prêt",  # noqa 501
        },
        status=200,
    )


@blueprint.route("/", methods=["GET"])
@permissions.check_cruved_scope("R", module_code="EXPORTS", get_scope=True)
@json_resp
def get_exports(scope):
    """
    Fonction qui renvoie la liste des exports
    accessibles pour un role donné
    """
    exports = Export.query.filter_by_scope(scope).all()
    return ExportSchema(many=True, only=["licence", "cor_roles_exports"]).dump(exports)


@blueprint.route("/api/<int:id_export>", methods=["GET"])
@json_resp
def get_one_export_api(id_export):
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
    token : clé de l'API permettant de se passer de la connexion via un
        cookie. Peut aussi être transmis dans un entête HTTP
        `Authorization: Bearer <token>`.

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
    limit = request.args.get("limit", default=1000, type=int)
    offset = request.args.get("offset", default=0, type=int)
    token = request.args.get("token", default=None, type=str)

    # Try to extract token from Bearer Authorization HTTP Header
    bearer = request.headers.get("Authorization", default=None, type=str)
    if token is None and bearer is not None:
        token = bearer.lstrip("Bearer ")

    user = g.current_user

    export = Export.query.get_or_404(id_export)
    scope = None
    if user:
        scope = get_scopes_by_action(user.id_role, "EXPORTS")["R"]
    if not export.has_instance_permission(user=user, token=token, scope=scope):
        raise Forbidden

    if limit > 1000:
        limit = 1000

    args = request.args.to_dict()
    if "limit" in args:
        args.pop("limit")
    if "offset" in args:
        args.pop("offset")
    if "token" in args:
        args.pop("token")
    filters = {f: args.get(f) for f in args}

    if not "orderby" in filters:
        filters["orderby"] = export.view_pk_column

    query = export.get_view_query(limit=limit, offset=offset, filters=filters)

    data = query.return_query()

    export_license = export.licence
    data["license"] = dict()
    data["license"]["name"] = getattr(export_license, "name_licence", None)
    data["license"]["href"] = getattr(export_license, "url_licence", None)

    return data


if public_config.get("EXPORTS", False) and public_config["EXPORTS"]["expose_dsw_api"]:

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
        export_dsw_dir = os.path.join(
            current_app.config["MEDIA_FOLDER"], conf.get("export_dsw_dir")
        )
        export_dsw_fullpath = str(Path(export_dsw_dir, conf.get("export_dsw_filename")))
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
            os.path.dirname(export_dsw_fullpath),
            os.path.basename(export_dsw_fullpath),
        )
