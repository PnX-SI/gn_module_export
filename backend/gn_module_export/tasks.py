from datetime import datetime, timedelta

from sqlalchemy import func
from celery.utils.log import get_task_logger
from celery.schedules import crontab

from geonature.utils.celery import celery_app

from .models import Export, ExportSchedules
from .utils_export import export_data_file, ExportGenerationNotNeeded

from geonature.core.notifications.utils import dispatch_notifications

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
        export = scheduled_export.export
        generate_export.delay(
            export_id=export.id,
            export_format=scheduled_export.format,
            filename="",
            user=None,
            scheduled=True,
            skip_newer_than=scheduled_export.frequency * 24 * 60,
        )


@celery_app.task(bind=True, throws=ExportGenerationNotNeeded)
def generate_export(
    self,
    export_id,
    export_format,
    filename,
    user=None,
    scheduled=False,
    skip_newer_than=None,
):
    logger.info(f"Generate export {export_id}...")
    export = Export.query.get(export_id)
    if export is None:
        logger.warning("Export {export_id} does not exist")
        return
    if skip_newer_than is not None:
        skip_newer_than = timedelta(minutes=skip_newer_than)
    export_data_file(
        id_export=export_id,
        export_format=export_format,
        filename=filename,
        user=user,
        isScheduler=scheduled,
        skip_newer_than=skip_newer_than,
    )
    logger.info(f"Export {export_id} generated.")
