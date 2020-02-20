
import click
import logging
import datetime

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
        Export cron d'un fichier
    """
    gne_logger.info(datetime.datetime.now())
    from ..utils_export import export_data_file
    export_data_file(id_export=2, export_format="json", filters={})
    gne_logger.info("export DONE")
