"""
    Fonctions permettant la génération des fichiers d'export
"""
import os
import json
import shutil
import time

from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app
from geoalchemy2.shape import from_shape
from shapely.geometry import asShape

from utils_flask_sqla.response import generate_csv_content
from utils_flask_sqla_geo.utilsgeometry import (
    FionaShapeService, FionaGpkgService
)

from geonature.utils.filemanager import (
    removeDisallowedFilenameChars
)
from .repositories import (
    ExportRepository
)
from .send_mail import export_send_mail, export_send_mail_error


def export_filename(export):
    """
        Génération du nom horodaté du fichier d'export
    """
    return '{}_{}'.format(
        time.strftime("%Y-%m-%d_%H-%M-%S"),
        removeDisallowedFilenameChars(export.get('label'))
    )


def schedule_export_filename(export):
    """
        Génération du nom statique du fichier d'export programmé
    """
    return '{}'.format(
        removeDisallowedFilenameChars(export.get('label'))
    )


def thread_export_data(id_export, export_format, info_role, filters, mail_to):
    """
        Lance un thread qui permet d'exécuter les fonctions d'export
            en arrière plan

        .. :quickref: Lance un thread qui permet d'exécuter les fonctions
            d'export en arrière plan

        :query int id_export: Identifiant de l'export
        :query str export_format: Format de l'export (csv, json, shp)
        :query {} info_role: Information du role
        :query {} filters: Filtre à appliquer sur l'export
        :query [str] mail_to: Email de reception


        **Returns:**
        .. void
    """

    exprep = ExportRepository(id_export)

    # export data
    try:
        export, columns, data = exprep.get_export_with_logging(
            info_role,
            with_data=True,
            export_format=export_format,
            filters=filters,
            limit=-1,
            offset=0
        )
    except Exception as exp:
        export_send_mail_error(
            mail_to,
            None,
            "Error when exporting data : {}".format(repr(exp))
        )
        return

    # Generate and store export file
    try:
        file_name = export_filename(export)
        full_file_name = GenerateExport(
            file_name=file_name,
            format=export_format,
            data=data,
            columns=columns,
            export=export
        ).generate_data_export()

    except Exception as exp:
        export_send_mail_error(
            mail_to,
            export,
            "Error when creating the export file : {}".format(repr(exp))
        )
        raise exp
        return

    # Send mail
    try:
        export_send_mail(
            mail_to=mail_to,
            export=export,
            file_name=full_file_name
        )
    except Exception as exp:
        export_send_mail_error(
            mail_to,
            export,
            "Error when sending email : {}".format(repr(exp))
        )


def export_data_file(id_export, export_format, filters, isScheduler=False):
    """
        TODO : REMOVE => NOT USE
        Fonction qui permet de générer un export fichier

        .. :quickref:  Fonction qui permet de générer un export fichier

        :query int id_export: Identifiant de l'export
        :query str export_format: Format de l'export (csv, json, shp)
        :query {} filters: Filtre à appliquer sur l'export


        **Returns:**
        .. str : nom du fichier
    """

    exprep = ExportRepository(id_export)

    # export data
    try:
        columns, data = exprep._get_data(
            filters=filters,
            limit=-1,
            offset=0,
            format=export_format
        )
    except Exception as exp:
        raise(exp)

    # Generate and store export file
    export_def = exprep.export.as_dict()
    try:
        if isScheduler:
            file_name = schedule_export_filename(export_def)
        else:
            file_name = export_filename(export_def)

        full_file_name = GenerateExport(
            file_name=file_name,
            format=export_format,
            data=data,
            columns=columns,
            export=export_def,
            isScheduler=isScheduler
        ).generate_data_export()

    except Exception as exp:
        raise(exp)
    return full_file_name


class GenerateExport():
    """
        Classe permettant de générer un fichier d'export dans le format spécfié
    """
    def __init__(self, file_name, format, data, columns, export, isScheduler=False):
        self.file_name = file_name
        self.format = format
        self.data = data
        self.columns = columns
        self.export = export
        self.has_geometry = export.get('geometry_field', None)

        conf = current_app.config.get('EXPORTS')

        if isScheduler:
            self.export_dir = conf.get('export_schedules_dir')
        else:
            self.export_dir = os.path.join(current_app.static_folder, 'exports')  # noqa E501

        os.makedirs(self.export_dir, exist_ok=True)

        # Nettoyage des anciens exports clean_export_file()
        clean_export_file(
            dir_to_del=self.export_dir,
            nb_days=current_app.config["EXPORTS"]['nb_days_keep_file']
        )

    def generate_data_export(self):
        """
            Génération des fichiers d'export en fonction du format demandé
        """
        out = None

        format_list = [
            k
            for k in current_app.config["EXPORTS"]["export_format_map"].keys()
        ]

        if self.format not in format_list:
            raise Exception('Unsupported format')

        if (self.format == 'shp' and self.has_geometry):
            self.generate_shp('shp')
            return self.file_name + '.zip'
        if (self.format == 'gpkg' and self.has_geometry):
            self.generate_shp('gpkg')
            return self.file_name + '.gpkg'
        elif (self.format == 'geojson' and self.has_geometry):
            self.data = self.data['items']
            out = self.generate_json()
        elif (self.format == 'json'):
            out = self.generate_json()
        elif self.format == 'csv':
            out = self.generate_csv()
        else:
            raise Exception('Export generation is impossible with the specified format')  # noqa E501

        if out:
            with open(
                    "{}/{}.{}".format(
                        self.export_dir, self.file_name, self.format
                    ), 'w'
            ) as file:
                file.write(out)
        return self.file_name + '.' + self.format

    def generate_csv(self):
        """
            Transformation des données au format CSV
        """
        return generate_csv_content(
            columns=[c.name for c in self.columns],
            data=self.data.get('items'),
            separator=','
        )

    def generate_json(self):
        """
            Transformation des données au format JSON/GeoJSON
        """
        return json.dumps(
            self.data,
            ensure_ascii=False,
            indent=4
        )

    def generate_shp(self, export_format):
        """
            Transformation des données au format SHP
            et sauvegarde sous forme d'une archive
        """

        if export_format == 'shp':
            fionaService = FionaShapeService
        else:
            fionaService = FionaGpkgService

        fionaService.create_fiona_struct(
            db_cols=self.columns,
            srid=self.export.get('geometry_srid'),
            dir_path=self.export_dir,
            file_name=self.file_name
        )

        items = self.data.get('items')

        for feature in items['features']:
            geom, props = (
                feature.get(field) for field in ('geometry', 'properties')
            )

            fionaService.create_feature(
                props, from_shape(
                    asShape(geom), self.export.get('geometry_srid')
                )
            )

        fionaService.save_files()

        # Suppression des fichiers générés et non compressés
        for gtype in ['POINT', 'POLYGON', 'POLYLINE']:
            file_path = Path(self.export_dir, gtype + '_' + self.file_name)
            if file_path.is_dir():
                shutil.rmtree(str(file_path))

        return True


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
    time_to_del = datetime.timestamp(
        datetime.today() - timedelta(days=nb_days)
    )

    for item in Path(dir_to_del).glob('*'):
        item_time = item.stat().st_mtime
        if item_time < time_to_del:
            if item.is_dir():
                shutil.rmtree(str(item))
            if item.is_file():
                item.unlink()
