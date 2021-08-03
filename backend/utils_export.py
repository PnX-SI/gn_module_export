"""
    Fonctions permettant la génération des fichiers d'export
"""
import os
import json
import shutil
import time
import zipfile
import subprocess
import re

from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app

from geonature.utils.filemanager import removeDisallowedFilenameChars
from .repositories import ExportRepository
from .send_mail import export_send_mail, export_send_mail_error

EXPORT_FORMAT = {
    "gpkg": "GPKG",
    "shp": "ESRI Shapefile",
    "geojson": "GeoJSON",
    "json": "GeoJSON",
    "csv": "CSV",
}



def export_filename(export):
    """
    Génération du nom horodaté du fichier d'export
    """
    return "{}_{}".format(
        time.strftime("%Y-%m-%d_%H-%M-%S"),
        removeDisallowedFilenameChars(export.get("label")),
    )


def schedule_export_filename(export):
    """
    Génération du nom statique du fichier d'export programmé
    """
    return "{}".format(removeDisallowedFilenameChars(export.get("label")))


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
    rep_exp = ExportRepository(id_export)
    export = rep_exp.export.as_dict(["licence"])

    # Generate and store export file
    try:
        start_time = datetime.utcnow()
        full_file_name = export_data_file(id_export, export_format, filters, isScheduler=False)
        status = 1
        log = None
        # Send mail
        try:
            export_send_mail(mail_to=mail_to, export=export, file_name=full_file_name)
        except Exception as exp:
            export_send_mail_error(
                mail_to, export, "Error when sending email : {}".format(repr(exp))
            )
    except Exception as exp:
        export_send_mail_error(
            mail_to,
            export,
            "Error when creating the export file : {}".format(repr(exp)),
        )
        status = 0
        log = repr(exp)
    finally:
        end_time = datetime.utcnow()
        rep_exp.log_export(
                info_role.id_role,
                export_format,
                start_time,
                end_time,
                status,
                log
            )



def export_data_file(id_export, export_format, filters, isScheduler=False):
    """
    Fonction qui permet de générer un export fichier

    .. :quickref:  Fonction qui permet de générer un export fichier

    :query int id_export: Identifiant de l'export
    :query str export_format: Format de l'export (csv, json, shp)
    :query {} filters: Filtre à appliquer sur l'export


    **Returns:**
    .. str : nom du fichier
    """
    try:
        full_file_name = GenerateExport(
            format=export_format,
            id_export=id_export,
            filters=filters,
            limit=-1,
            offset=0,
            isScheduler=isScheduler,
        ).generate_data_export()
        return full_file_name

    except Exception as exp:
        raise (exp)


class GenerateExport:
    """
    Classe permettant de générer un fichier d'export dans le format spécfié
    """

    def __init__(
        self,
        format,
        id_export,
        filters,
        limit=-1,
        offset=0,
        isScheduler=False,
    ):
        self.format = format

        self.exprep = ExportRepository(id_export)
        self.columns = self.exprep._get_query_def(filters=filters, limit=-1, offset=0)
        self.export = self.exprep.export.as_dict(fields=["licence"])

        # self.data = data
        self.has_geometry = self.export.get("geometry_field", None)

        conf = current_app.config.get("EXPORTS")

        if isScheduler:
            self.file_name = schedule_export_filename(self.export)
        else:
            self.file_name = export_filename(self.export)

        if isScheduler:
            self.export_dir = conf.get("export_schedules_dir")
        else:
            self.export_dir = os.path.join(
                current_app.static_folder, "exports", conf.get("usr_generated_dirname")
            )

        os.makedirs(self.export_dir, exist_ok=True)

        # Nettoyage des anciens exports clean_export_file()
        clean_export_file(
            dir_to_del=self.export_dir,
            nb_days=current_app.config["EXPORTS"]["nb_days_keep_file"],
        )

    def generate_data_export(self):
        """
        Génération des fichiers d'export en fonction du format demandé
        """

        format_list = [
            k for k in current_app.config["EXPORTS"]["export_format_map"].keys()
        ]

        if self.format not in format_list:
            raise Exception("Unsupported format")

        if self.format == "shp" and self.has_geometry:
            self.generate_shp()
            return self.file_name + ".zip"
        if self.format == "gpkg" and self.has_geometry:
            self.export_with_ogr()
        elif self.format == "geojson" and self.has_geometry:
            self.export_with_ogr()
        elif self.format == "json":
            self.generate_json()
        elif self.format == "csv":
            self.export_with_ogr()
        else:
            raise Exception(
                "Export generation is impossible with the specified format"
            )  # noqa E501

        return self.file_name + "." + self.format

    def export_with_ogr(self, file_name=None, custom_where=None):

        if not file_name:
            file_name = self.file_name

        if custom_where:
            where_clause = f" WHERE {custom_where}"
        else:
            where_clause = ""

        db_host, db_port, db_user, db_pass, db_name = decompose_database_uri()
        exp_query = "SELECT * FROM {schema}.{view} {where} LIMIT 10".format(
            schema=self.export["schema_name"],
            view=self.export["view_name"],
            where=where_clause
        )

        ogr_export_pg_table(
            self.format,
            export_path=self.export_dir,
            file_name=file_name,
            host=db_host,
            username=db_user,
            password=db_pass,
            db=db_name,
            port=db_port,
            pg_sql_select=exp_query,
        )
        return True

    def generate_json(self):
        """
        Transformation des données au format JSON
        """
        columns, data = self.exprep._get_data(
            filters=None, limit=-1, offset=0, format="json"
        )
        out = json.dumps(data, ensure_ascii=False, indent=4)

        if out:
            with open(
                f"{self.export_dir}/{self.file_name}.{self.format}", "w"
            ) as file:
                file.write(out)

        return f"{self.file_name}.{self.format}"

    def generate_shp(self):
        """
            Transformation des données au format SHP
            et sauvegarde sous forme d'une archive
        """

        geo_type = {
            "POLYGON": "Polygon",
            "POINT": "Point",
            "POLYLINE": "LineString"
        }
        shp_extentions = ("dbf", "shx", "shp", "prj")

        zip_shp = zipfile.ZipFile(f"{self.export_dir}/{self.file_name}.zip", 'w')

        for gtype in geo_type:
            # Génération des fichiers en fonction du type de géométrie
            file_name = f"{gtype}_{self.file_name}"
            file_path = f"{self.export_dir}/{file_name}"
            base_where = f"st_geometrytype({self.has_geometry})"
            self.export_with_ogr(
                file_name=file_name,
                custom_where=f"{base_where} = 'ST_{geo_type[gtype]}' OR {base_where} = 'ST_Multi{geo_type[gtype]}'"
            )

            for ext in shp_extentions:
                # compression dans fichier zip
                zip_shp.write(
                    f"{file_path}.{ext}",
                    f"{file_name}.{ext}"
                )
                # Suppression des fichiers générés et non compressés
                Path(f"{file_path}.{ext}").unlink()
        zip_shp.close()
        return f"{self.file_name}.zip"


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


def ogr_export_pg_table(
    format, export_path, file_name, host, username, password, db, port, pg_sql_select
):
    cmd = [
        "ogr2ogr",
        "-overwre",
        "-f",
        f"{EXPORT_FORMAT[format]}",
        f"{export_path}/{file_name}.{format}",
        f"PG:host={host} user={username} dbname={db} password={password} port={port}",
        "-sql",
        f"{pg_sql_select}",
    ]
    output = subprocess.run(cmd, capture_output=True)

    output_msg = output.stderr.decode('utf8')
    if "ERROR" in output_msg:
        raise Exception(output_msg)


def decompose_database_uri():
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    m = re.search("postgresql:\/\/(.+)\:(.+)@(.+):(\d+)\/(\w+)", uri)
    db_host = m.group(3)
    db_port = m.group(4)
    db_user = m.group(1)
    db_pass = m.group(2)
    db_name = m.group(5)
    return db_host, db_port, db_user, db_pass, db_name