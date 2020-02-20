"""
    Fonctions permettant la génération des fichiers d'export
"""
import json
import shutil

from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app
from geoalchemy2.shape import from_shape
from shapely.geometry import asShape

from utils_flask_sqla.response import generate_csv_content
from utils_flask_sqla_geo.serializers import FionaShapeService

from geonature.utils.filemanager import (
    removeDisallowedFilenameChars
)
from .repositories import (
    ExportRepository
)
from .send_mail import export_send_mail, export_send_mail_error


def export_filename(export):
    """
        Génération du nom du fichier d'export
    """
    return '{}'.format(
        removeDisallowedFilenameChars(export.get('label'))
    )


def thread_export_data(id_export, export_format, info_role, filters, user):
    """
        Lance un thread qui permet d'executer les fonctions d'export
            en arrière plan

        .. :quickref: Lance un thread qui permet d'executer les fonctions
            d'export en arrière plan

        :query int id_export: Identifiant de l'export
        :query str export_format: format de l'export (csv, json, shp)
        :query {} info_role: Information du role
        :query {} filters: Filtre à appliquer sur l'export
        :query User user: Objet user


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
            user,
            None,
            "Error when export data : {}".format(repr(exp))
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
            user,
            export,
            "Error when create export file : {}".format(repr(exp))
        )
        return

    # Send mail
    try:
        export_send_mail(
            role=user,
            export=export,
            file_name=full_file_name
        )
    except Exception as exp:
        export_send_mail_error(
            user,
            export,
            "Error when sending mail : {}".format(repr(exp))
        )


def export_data_file(id_export, export_format, filters, isScheduler=False):
    """
        Fonction qui permet de générer un export fichier

        .. :quickref:  Fonction qui permet de générer un export fichier

        :query int id_export: Identifiant de l'export
        :query str export_format: format de l'export (csv, json, shp)
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
        from .blueprint import EXPORTS_DIR, EXPORT_SCHEDULES_DIR
        self.export_dir = EXPORTS_DIR
        if isScheduler:
            self.export_dir = EXPORT_SCHEDULES_DIR

        # Nettoyage des anciens export clean_export_file()
        clean_export_file(
            dir_to_del=self.export_dir,
            nb_days=current_app.config['EXPORTS']['nb_days_keep_file']
        )

    def generate_data_export(self):
        """
            Génération des fichier d'export en fonction du format demandé
        """
        out = None

        if self.format not in ['json', 'csv', 'shp', 'geojson']:
            raise Exception('Unsuported format')

        if (self.format == 'shp' and self.has_geometry):
            self.generate_shp()
            return self.file_name + '.zip'
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
                    ), 'a'
            ) as file:
                file.write(out)
        return self.file_name + '.' + self.format

    def generate_csv(self):
        """
            transformation des données au format csv
        """
        return generate_csv_content(
            columns=[c.name for c in self.columns],
            data=self.data.get('items'),
            separator=','
        )

    def generate_json(self):
        """
            transformation des données au format json/geojson
        """
        return json.dumps(
            self.data,
            ensure_ascii=False,
            indent=4
        )

    def generate_shp(self):
        """
            transformation des données au format shp
            et sauvegarde sous forme d'une archive
        """
        FionaShapeService.create_shapes_struct(
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

            FionaShapeService.create_feature(
                props, from_shape(
                    asShape(geom), self.export.get('geometry_srid')
                )
            )

        FionaShapeService.save_and_zip_shapefiles()

        # Suppression des fichiers générés et non compressé
        for gtype in ['POINT', 'POLYGON', 'POLYLINE']:
            file_path = Path(self.export_dir, gtype + '_' + self.file_name)
            if file_path.is_dir():
                shutil.rmtree(file_path)

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
                shutil.rmtree(item)
            if item.is_file():
                item.unlink()
