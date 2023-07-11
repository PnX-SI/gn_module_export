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
from geonature.core.gn_permissions.tools import get_scopes_by_action
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
    media_dir = None

    def __init__(
        self,
        id_export: int,
        user: User = None,
        format: str = None,
        skip_newer_than: int = None,
    ):
        self.export = Export.query.get_or_404(id_export)
        self.user = user
        self.format = format

        if user and not self.export.has_instance_permission(user, scope=get_scopes_by_action(user.id_role, "EXPORTS")["R"]):
            raise Forbidden

        self._generate_file_name_and_dir()
        if skip_newer_than:
            self.skip_newer_than = timedelta(minutes=skip_newer_than)
            self._test_export_needed()

    def _get_cst_file_name(self):
        return "{}.{}".format(removeDisallowedFilenameChars(self.export.label), self.format)

    def _generate_file_name_and_dir(self):
        if self.file_name:
            return

        if not self.user:
            self.media_dir = "exports/schedules"
            self.export_dir = Path(current_app.config["MEDIA_FOLDER"]) / self.media_dir
            self.file_name = self._get_cst_file_name()
        else:
            self.media_dir = "exports/usr_generated"
            self.export_dir = Path(current_app.config["MEDIA_FOLDER"]) / self.media_dir
            self.file_name = "{}_{}".format(
                datetime.now().strftime("%Y_%m_%d_%Hh%Mm%S"), self._get_cst_file_name()
            )

    def _test_export_needed(self):
        if not self.skip_newer_than:
            return

        for file in Path(self.export_dir).glob("*{}".format(self._get_cst_file_name())):
            age = datetime.now() - datetime.fromtimestamp(file.stat().st_mtime)
            if age < self.skip_newer_than:
                raise ExportGenerationNotNeeded(self.export.id, self.skip_newer_than - age)

    def get_export_url(self):
        return url_for(
            "media",
            filename=f"{self.media_dir}/{self.file_name}",
            _external=True,
        )

    def get_full_path_file_name(self):
        return str(Path(self.export_dir) / self.file_name)


def export_data_file(export_id, file_name, export_url, format, id_role, filters):
    """
    Fonction qui permet de générer un export fichier

    .. :quickref:  Fonction qui permet de générer un export fichier

    :query int id_export: Identifiant de l'export
    :query str export_format: Format de l'export (csv, json, gpkg)
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
