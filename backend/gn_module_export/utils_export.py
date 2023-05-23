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
from utils_flask_sqla_geo.utilsgeometry import (
    FionaShapeService,
    FionaGpkgService,
)

from geonature.utils.filemanager import removeDisallowedFilenameChars
from geonature.utils.env import DB
from geonature.core.notifications.utils import dispatch_notifications
from pypnusershub.db.models import User

from .models import Export

from gn_module_export.utils.export import export_as_file


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

    def __init__(self, id_export, scheduled_export=None, user=None, format=None):
        self.id_export = id_export
        self.user = user
        self.format = format
        self.export = Export.query.get_or_404(self.id_export)

        if user and not self.export.has_instance_permission(user):
            raise Forbidden

        if scheduled_export:
            self.scheduled_export = scheduled_export
            self.format = scheduled_export.format
            self.test_schedule_needed()

        self.generate_file_name()

    def generate_file_name(self):
        if self.file_name:
            return Path(self.export_dir) / self.file_name

        if not self.user:
            self.export_dir = Path(current_app.config["MEDIA_FOLDER"]) / "exports/schedules"
            self.file_name = "{}.{}".format(
                removeDisallowedFilenameChars(self.export.label), self.format
            )
        else:
            self.export_dir = Path(current_app.config["MEDIA_FOLDER"]) / "exports/usr_generated"
            self.file_name = "{}_{}.{}".format(
                datetime.now().strftime("%Y_%m_%d_%Hh%Mm%S"),
                removeDisallowedFilenameChars(self.export.label),
                self.format,
            )
        os.makedirs(self.export_dir, exist_ok=True)

        return Path(self.export_dir) / self.file_name

    def test_schedule_needed(self):
        self.generate_file_name()
        skip_newer_than = timedelta(minutes=self.scheduled_export.frequency * 24 * 60)
        file_path = Path(self.export_dir) / self.file_name
        if skip_newer_than is not None and file_path.exists():
            age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            if age < skip_newer_than:
                raise ExportGenerationNotNeeded(self.export.id, skip_newer_than - age)


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
        export_as_file(
            export=export,
            file_format=format,
            filename=file_name,
            generic_query_geo=export.get_view_query(limit=-1, offset=0, filters=None),
        )
    except Exception as exp:
        notify_export_file_generated(
            export=export,
            user=id_role,
            export_url=export_url,
            export_failed=True,
        )
        raise exp
    notify_export_file_generated(export=export, user=id_role, export_url=export_url)
