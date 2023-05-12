from datetime import datetime, timedelta

from sqlalchemy import func
from celery.utils.log import get_task_logger
from celery.schedules import crontab

from geonature.utils.celery import celery_app

from .models import Export, ExportSchedules
from .utils_export import export_data_file, ExportGenerationNotNeeded


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
            scheduled=True,
            skip_newer_than=scheduled_export.frequency * 24 * 60,
        )


@celery_app.task(bind=True, throws=ExportGenerationNotNeeded)
def generate_export(
    self, export_id, export_format, scheduled=False, skip_newer_than=None
):
    from memory_profiler import memory_usage
    import tracemalloc

    tracemalloc.start()

    mem_usage_before = memory_usage()
    logger.info(f"Memory usage before export {export_id}: {mem_usage_before} MiB")
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
        isScheduler=scheduled,
        skip_newer_than=skip_newer_than,
    )
    logger.info(f"Export {export_id} generated.")
    mem_usage_after = memory_usage()
    logger.info(f"Memory usage after export {export_id}: {mem_usage_after}")
    logger.info(f"Memory usage delta: {mem_usage_after[0] - mem_usage_before[0]} MiB")

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    logger.info(
        f"Total tracemalloc in `generate_export` : {sum(stat.size for stat in top_stats) / 1024 / 1024} MiB"
    )


from memory_profiler import profile


@profile()
def generate_export_synchronous(
    export_id,
    export_format,
    scheduled=False,
    skip_newer_than=None,
):
    from memory_profiler import memory_usage
    import tracemalloc

    tracemalloc.start()

    mem_usage_before = memory_usage()

    print(f"Memory usage before export {export_id}: {mem_usage_before} MiB")
    print(f"Generate export {export_id}...")
    export = Export.query.get(export_id)
    if export is None:
        logger.warning("Export {export_id} does not exist")
        return
    if skip_newer_than is not None:
        skip_newer_than = timedelta(minutes=skip_newer_than)
    export_data_file(
        id_export=export_id,
        export_format=export_format,
        isScheduler=scheduled,
        skip_newer_than=skip_newer_than,
    )
    print(f"Export {export_id} generated.")
    mem_usage_after = memory_usage()
    print(f"Memory usage after export {export_id}: {mem_usage_after}")
    print(f"Memory usage delta: {mem_usage_after[0] - mem_usage_before[0]} MiB")

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    print(
        f"Total tracemalloc in `generate_export` : {sum(stat.size for stat in top_stats) / 1024 / 1024} MiB"
    )
