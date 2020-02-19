
import click

from flask.cli import with_appcontext

from geonature.core.command import main

@main.command()
@with_appcontext
def gn_exports_run_cron_export():
    """
        Export cron d'un fichier
    """
    from ..utils_export import export_data_file
    export_data_file(id_export=2, export_format="csv", filters={})
