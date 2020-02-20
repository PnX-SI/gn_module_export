import os
from datetime import datetime, timedelta
import logging

from flask.cli import with_appcontext

from geonature.core.command import main

from geonature.utils.env import ROOT_DIR

# Configuration logger
gne_handler = logging.FileHandler(
    str(ROOT_DIR / "var/log/gn_export/cron.log"), mode="w"
)
gne_handler.setLevel(logging.INFO)

gne_logger = logging.getLogger('gn_export')

gne_logger.addHandler(gne_handler)


@main.command()
@with_appcontext
def gn_exports_run_cron_export():
    """
        Export planifié d'un fichier
    """
    gne_logger.info(datetime.now())
    from ..utils_export import export_data_file
    from ..repositories import get_export_schedules

    # Liste des exports automatiques
    try:
        export_schedules = get_export_schedules()

        for schedule in export_schedules:

            file_is_to_updated = is_to_updated(schedule)

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
                        "Export {} whith frequency {} is done".format(
                            schedule.file_name, schedule.frequency
                        )
                    )
                except Exception as exception:
                    gne_logger.info("exception export_data_file: ", exception)

    except Exception as exception:
        gne_logger.info("exception export auto: ", exception)


@with_appcontext
def modification_date(filename):
    from ..blueprint import EXPORT_SCHEDULES_DIR
    try:
        full_path = os.path.join(EXPORT_SCHEDULES_DIR, filename)
        t = os.path.getmtime(full_path)
        modif_date = datetime.fromtimestamp(t)

        return modif_date
    except Exception as exception:
        gne_logger.info("exception modification_date: ", exception)


@with_appcontext
def check_file_exists(filename):
    from ..blueprint import EXPORT_SCHEDULES_DIR
    try:
        full_path = os.path.join(EXPORT_SCHEDULES_DIR, filename)
        exists = os.path.exists(full_path)
        return exists
    except Exception as exception:
        gne_logger.info("exception modification_date: ", exception)


def is_to_updated(schedule):
    file_exists = check_file_exists(schedule.file_name)
    file_is_to_updated = True
    if file_exists:
        file_date = modification_date(schedule.file_name)
        # Vérifie si la date du fichier
        #           est inférieure à la date courante + frequency
        file_is_to_updated = file_date and file_date + timedelta(hours=schedule.frequency) < datetime.now()  # noqa E501
    return file_is_to_updated
