import os
import click
import logging

from pathlib import Path
from datetime import datetime, timedelta
from flask.cli import with_appcontext

from geonature.core.command import main
from geonature.utils.env import ROOT_DIR

# #######################
#  Configuration logger
# #######################
# Test if directory exists
LOG_DIR = ROOT_DIR / "var/log/gn_export"

Path(LOG_DIR).mkdir(
    parents=True, exist_ok=True
)
gne_handler = logging.FileHandler(
    str(LOG_DIR / "cron.log"), mode="w"
)
formatter = logging.Formatter(
    fmt='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
gne_handler.setLevel(logging.INFO)
gne_handler.setFormatter(formatter)

gne_logger = logging.getLogger('gn_export')
gne_logger.addHandler(gne_handler)


@main.command()
@with_appcontext
def gn_exports_run_cron_export():
    """
        Export planifié d'un fichier
    """
    gne_logger.info("START schedule export task")
    from ..utils_export import export_data_file, schedule_export_filename
    from ..repositories import get_export_schedules

    # Liste des exports automatiques
    try:
        export_schedules = get_export_schedules()

        for schedule in export_schedules:
            # Generation nom du fichier export
            schedule_filename = schedule_export_filename(schedule.export.as_dict())

            # Test si le fichier doit être regénéré
            filename = "{}.{}".format(schedule_filename, schedule.format)
            file_is_to_updated = is_to_updated(schedule.frequency, filename)

            if file_is_to_updated:
                # Fonction qui permet de générer un export fichier
                try:
                    export_data_file(
                        id_export=schedule.id_export,
                        export_format=schedule.format,
                        filters={},
                        isScheduler=True
                    )
                    gne_logger.info(
                        "Export {} with frequency {} day is done".format(
                            schedule.export.label, schedule.frequency
                        )
                    )
                except Exception as exception:
                    gne_logger.error("exception export_data_file: {}".format(exception))
            else:
                gne_logger.info(
                    "Export {} with frequency {} day not need to be updated".format(
                        schedule.export.label, schedule.frequency
                    )
                )
        gne_logger.info("END schedule export task")
    except Exception as exception:
        raise (exception)
        gne_logger.error("exception export auto: {}".format(exception))


@main.command()
@click.option("--limit", required=False, default=-1)
@click.option("--offset", required=False, default=0)
@with_appcontext
def gn_exports_run_cron_export_dsw(limit, offset):
    """
        Export des données de la synthese au format Darwin-SW (ttl)

        Exemples

        - geonature gn_exports_run_cron_export_dsw

        - geonature gn_exports_run_cron_export_dsw --limit=2 --offset=1
    """

    gne_logger.info("START schedule Darwin-SW export task")

    from flask import current_app
    from ..rdf import generate_store_dws

    try:

        conf = current_app.config.get('EXPORTS')
        export_dsw_dir = str(Path(
            conf.get('export_dsw_dir'),
            conf.get('export_dsw_filename')
        ))

        # Get data and generate semantic data structure
        store = generate_store_dws(limit=limit, offset=offset, filters={})

        # Store file
        try:
            Path(conf.get('export_dsw_dir')).mkdir(
                parents=True, exist_ok=True
            )
            with open(export_dsw_dir, 'w+b') as xp:
                store.save(store_uri=xp)
        except FileNotFoundError as exception:
            gne_logger.error(
                "Exception when saving file {}: ".format(
                    export_dsw_dir
                ),
                exception
                )

        gne_logger.info(
            "Export done with success data are available here: {}".format(
                export_dsw_dir
                )
        )
        gne_logger.info("END schedule export task")
    except Exception as exception:
        gne_logger.error("exception export scheduled: {}".format(exception))


@with_appcontext
def modification_date(filename):
    from flask import current_app
    conf = current_app.config.get('EXPORTS')
    EXPORT_SCHEDULES_DIR = conf.get('export_schedules_dir')
    try:
        full_path = os.path.join(EXPORT_SCHEDULES_DIR, filename)
        t = os.path.getmtime(full_path)
        modif_date = datetime.fromtimestamp(t)

        return modif_date
    except Exception as exception:
        gne_logger.error("exception modification_date: {} ".format(exception))


@with_appcontext
def check_file_exists(filename):
    from flask import current_app
    conf = current_app.config.get('EXPORTS')
    EXPORT_SCHEDULES_DIR = conf.get('export_schedules_dir')
    try:
        full_path = os.path.join(EXPORT_SCHEDULES_DIR, filename)
        exists = os.path.exists(full_path)
        return exists
    except Exception as exception:
        gne_logger.error("exception modification_date: {} ".format(exception))


@with_appcontext
def is_to_updated(frequency, schedule_filename):

    file_exists = check_file_exists(schedule_filename)
    file_is_to_updated = True
    if file_exists:
        file_date = modification_date(schedule_filename)
        # Vérifie si la date du fichier
        #           est inférieure à la date courante + frequency
        file_is_to_updated = file_date and file_date + timedelta(days=frequency) < datetime.now()  # noqa E501
    return file_is_to_updated
