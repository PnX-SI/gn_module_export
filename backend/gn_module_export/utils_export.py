"""
    Fonctions permettant la génération des fichiers d'export
"""
import os
import json
import shutil
import time

from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app, g, url_for
from geoalchemy2.shape import from_shape
from shapely.geometry import asShape

from werkzeug.exceptions import Forbidden

from utils_flask_sqla.response import generate_csv_content
from utils_flask_sqla_geo.utilsgeometry import FionaShapeService, FionaGpkgService

from geonature.utils.filemanager import removeDisallowedFilenameChars
from geonature.utils.env import DB
from geonature.core.notifications.utils import dispatch_notifications
from .models import Export


class ExportGenerationNotNeeded(Exception):
    pass


def notify_export_file_generated(export, user, export_url, export_failed=False):
    if user:
        dispatch_notifications(
            code_categories=["EXPORT-DONE"],
            id_roles=[user],
            url=export_url,
            context={
                "export": export,
                "nb_keep_day": str(current_app.config["EXPORTS"]["nb_days_keep_file"]),
                "export_failed": export_failed,
            },
        )
        DB.session.commit()


class ExportRequest:
    """
    Classe correspondant à la génération d'un fichier d'export
    """

    export_dir = None
    file_name = None
    export_url = None

    def __init__(self, id_export, scheduled_export=None, id_role=None, format=None):
        self.id_export = id_export
        self.id_role = id_role
        self.format = format
        print(format)
        self.export = Export.query.get_or_404(self.id_export)

        if id_role and not self.export.has_instance_permission(id_role):
            raise Forbidden

        if scheduled_export:
            self.format = scheduled_export.format
            self.test_schedule_needded()

    def generate_file_name(self):
        if self.file_name:
            return self.export_dir + self.file_name

        conf = current_app.config.get("EXPORTS")
        if self.id_role:
            """
            Génération du nom horodaté du fichier d'export
            """
            self.export_dir = os.path.join(
                current_app.config["MEDIA_FOLDER"],
                conf.get("export_schedules_dir"),
            )
            self.file_name = "{}_{}.{}".format(
                datetime.now().strftime("%Y_%m_%d_%Hh%Mm%S"),
                removeDisallowedFilenameChars(self.export.label),
                self.format,
            )
        else:
            """
            Génération du nom statique du fichier d'export programmé
            """
            self.export_dir = os.path.join(
                current_app.config["MEDIA_FOLDER"], conf.get("usr_generated_dirname")
            )
            self.file_name = "{}.{}".format(
                removeDisallowedFilenameChars(self.export.get("label")), self.format
            )
        print(self.file_name)
        os.makedirs(self.export_dir, exist_ok=True)

        return self.export_dir + self.file_name

    def generate_url(self):
        self.generate_file_name()
        module_conf = current_app.config["EXPORTS"]
        if module_conf.get("export_web_url"):
            return "{}/{}".format(module_conf.get("export_web_url"), self.file_name)
        else:
            return url_for(
                "media",
                filename=module_conf.get("usr_generated_dirname")
                + "/"
                + self.file_name,
                _external=True,
            )

    def test_schedule_needded(self):
        self.generate_file_name()
        skip_newer_than = timedelta(minutes=self.scheduled_export.frequency * 24 * 60)
        file_path = Path(self.export_dir) / self.file_name
        if skip_newer_than is not None and file_path.exists():
            age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            if age < skip_newer_than:
                raise ExportGenerationNotNeeded(
                    self.export["id"], skip_newer_than - age
                )


def export_data_file(export_id, file_name, export_url, format, id_role, filters):
    """
    Fonction qui permet de générer un export fichier

    .. :quickref:  Fonction qui permet de générer un export fichier

    :query int id_export: Identifiant de l'export
    :query str export_format: Format de l'export (csv, json, shp)
    :query {} filters: Filtre à appliquer sur l'export


    **Returns:**
    .. str : nom du fichier
    """

    export = Export.query.get(export_id)

    try:
        full_file_name = GenerateExport(
            query=export.get_view_query(limit=-1, offset=0, filters=None),
            file_name=file_name,
            format=format,
            primary_key=None,  # TODO change with PR  151
        )
    except Exception as exp:
        notify_export_file_generated(
            export=export, user=id_role, export_url=export_url, export_failed=True
        )
        raise exp

    notify_export_file_generated(export=export, user=id_role, export_url=export_url)

    return full_file_name


class GenerateExport:
    """
    Classe permettant de générer un fichier d'export dans le format spécfié
    """

    def __init__(self, query, file_name, format, primary_key):
        print("TODO")


def clean_export_file(dir_to_del, nb_days):
    """
    Fonction permettant de supprimer les fichiers générés
    par le module export ayant plus de X jours

    .. :quickref: Fonction permettant de supprimer les
        fichiers générés par le module export ayant plus de X jours


    :query str dir_to_del: Répertoire où les fichiers doivent
        être supprimés
    :query int nb_days: Nb de jours à partir duquel les fichiers
        sont considérés comme à supprimer



    """
    # Date limite de suppression
    time_to_del = datetime.timestamp(datetime.today() - timedelta(days=nb_days))

    for item in Path(dir_to_del).glob("*"):
        item_time = item.stat().st_mtime
        if item_time < time_to_del:
            if item.is_dir():
                shutil.rmtree(str(item))
            if item.is_file():
                item.unlink()
