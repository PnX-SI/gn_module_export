import os

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func
from celery.utils.log import get_task_logger
from celery.schedules import crontab

from flask import current_app
from flask.cli import with_appcontext
from geonature.utils.celery import celery_app

from geonature.utils.env import db

from .models import Export, ExportSchedules
from .utils_export import (
    export_data_file,
    ExportGenerationNotNeeded,
    ExportGenerationInProcess,
    ExportRequest,
)

logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
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
            user=None,
            format=scheduled_export.format,
            skip_newer_than=scheduled_export.skip_newer_than,
        )
        generate_export.delay(
            export_id=export_request.export.id,
            file_name=export_request.get_full_path_file_name(),
            export_url=None,
            format=export_request.format,
            id_role=None,
            filters=None,
            schedule_id=scheduled_export.scheduled_export_id,
        )


@celery_app.task(bind=True, throws=ExportGenerationNotNeeded)
def generate_export(self, export_id, file_name, export_url, format, id_role, filters, schedule_id):
    logger.info(f"Generate export {export_id} {schedule_id}...")
    export = db.session.get(Export, export_id)
    if export is None:
        logger.warning("Export {export_id} does not exist")
    if schedule_id:
        schedule_export = db.session.get(ExportSchedules, schedule_id)
        if schedule_export.in_process:
            raise ExportGenerationInProcess("Export {export_id} in process")
        schedule_export.in_process = True
        db.session.add(schedule_export)
        db.session.commit()
    export_data_file(export_id, file_name, export_url, format, id_role, filters, schedule_id)
    if schedule_id:
        schedule_export.in_process = False
        db.session.add(schedule_export)
        db.session.commit()
    logger.info(f"Export {export_id} generated.")
