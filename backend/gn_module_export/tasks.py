import os

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func
from celery.utils.log import get_task_logger
from celery.schedules import crontab

from flask import current_app
from geonature.utils.celery import celery_app

from .models import Export, ExportSchedules
from .utils_export import (
    export_data_file,
    ExportGenerationNotNeeded,
    ExportRequest,
)

from geonature.core.notifications.utils import dispatch_notifications

logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute="0", hour="2"),
        clean_export_file.s(),
        name="scheduled exports clean",
    )
    sender.add_periodic_task(
        crontab(minute="0", hour="3"),
        generate_scheduled_exports.s(),
        name="generate scheduled exports",
    )


@celery_app.task(bind=True)
def generate_scheduled_exports(self):
    for scheduled_export in ExportSchedules.query.all():
        export_request = ExportRequest(
            id_export=scheduled_export.id_export,
            scheduled_export=scheduled_export,
        )
        generate_export.delay(
            export_id=export_request.export.id,
            file_name=export_request.generate_file_name(),
            export_url=None,
            format=export_request.format,
            id_role=None,
            filters=None,
        )


@celery_app.task(bind=True, throws=ExportGenerationNotNeeded)
def generate_export(self, export_id, file_name, export_url, format, id_role, filters):
    logger.info(f"Generate export {export_id}...")
    export = Export.query.get(export_id)
    if export is None:
        logger.warning("Export {export_id} does not exist")
        return

    export_data_file(export_id, file_name, export_url, format, id_role, filters)
    logger.info(f"Export {export_id} generated.")


@celery_app.task(bind=True)
def clean_export_file(self):
    """
    Fonction permettant de supprimer les fichiers générés
    par le module export ayant plus de X jours

    .. :quickref: Fonction permettant de supprimer les
        fichiers générés par le module export ayant plus de X jours

    """

    dirs_to_del_from = [
        Path(current_app.config["MEDIA_FOLDER"]) / "exports/schedules",
        Path(current_app.config["MEDIA_FOLDER"]) / "exports/usr_generated",
    ]
    # Date limite de suppression
    time_to_del = datetime.timestamp(
        datetime.today() - timedelta(days=current_app.config["EXPORTS"]["nb_days_keep_file"])
    )
    for dir in dirs_to_del_from:
        for item in Path(dir).glob("**/*"):
            item_time = item.stat().st_mtime
            if item_time < time_to_del:
                if item.is_file():
                    item.unlink()
