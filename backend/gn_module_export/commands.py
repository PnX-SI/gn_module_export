import os
import click
import logging
from pathlib import Path
from datetime import datetime

from flask.cli import with_appcontext
from click import ClickException
from werkzeug.exceptions import NotFound, Forbidden

from flask import url_for, current_app
from pypnusershub.db.models import User
from gn_module_export.tasks import generate_export
from gn_module_export.models import Export, ExportSchedules
from gn_module_export.utils_export import (
    ExportGenerationNotNeeded,
    ExportRequest,
)


@click.command()
@click.option("--format", "export_format", default="csv")
@click.option(
    "--user-id",
    default=None,
    help="Identifiant de l'utilisateur.",
)
@click.option(
    "--skip-newer-than",
    type=int,
    help="Ne pas regénérer les fichiers récents (en minutes).",
)
@click.argument("export_id")
@with_appcontext
def generate(export_id, export_format, user_id, skip_newer_than):
    """
    Lance la génération d’un fichier d’export
    """
    scheduled_export = None
    user = None

    if user_id:
        user = User.query.get(user_id)
        if not user:
            raise ClickException(f"User {user_id} not found.")
    else:
        # If not user_id => scheduled
        scheduled_export = (
            ExportSchedules.query.filter(ExportSchedules.id_export == export_id)
            .filter(ExportSchedules.format == export_format)
            .first()
        )
        if not scheduled_export:
            raise ClickException(f"Schedule export {export_id} format {export_format} not found.")
        # Parameter skip_newer_than overide scheduled_export.skip_newer_than property
        if not skip_newer_than:
            skip_newer_than = scheduled_export.skip_newer_than
    try:
        export_request = ExportRequest(
            id_export=export_id,
            user=user,
            format=export_format,
            skip_newer_than=skip_newer_than,
        )
    except NotFound:
        raise ClickException(f"Export {export_id} not found.")
    except Forbidden:
        raise ClickException(f"Export {export_id} not allow for user id {user_id}.")
    except ExportGenerationNotNeeded:
        raise ClickException(f"Export {export_id} sufficiently recent, skip generation.")

    generate_export(
        export_id=export_request.export.id,
        file_name=export_request.get_full_path_file_name(),
        export_url=None,
        format=export_request.format,
        id_role=None,
        filters=None,
    )


@click.command()
@click.option(
    "--limit",
    required=False,
    default=-1,
    help="Nombre de résultats à retourner",
)
@click.option(
    "--offset",
    required=False,
    default=0,
    help="Numéro du premier enregistrement à retourner",
)
@with_appcontext
def generate_dsw(limit, offset):
    """
    Export des données de la synthese au format Darwin-SW (ttl)

    Exemples

    - geonature exports generate-dsw

    - geonature exports generate-dsw --limit=2 --offset=1
    """

    click.echo("START Darwin-SW export task")

    from flask import current_app
    from .rdf import generate_store_dws

    conf = current_app.config.get("EXPORTS")
    export_dsw_dir = str(
        Path(
            current_app.config["MEDIA_FOLDER"],
            conf.get("export_dsw_dir"),
            conf.get("export_dsw_filename"),
        )
    )

    # Get data and generate semantic data structure
    store = generate_store_dws(limit=limit, offset=offset, filters={})

    # Store file
    Path(current_app.config["MEDIA_FOLDER"], conf.get("export_dsw_dir")).mkdir(
        parents=True, exist_ok=True
    )
    with open(export_dsw_dir, "w+b") as xp:
        store.save(store_uri=xp)

    click.echo("Export done with success data are available here: {}".format(export_dsw_dir))
    click.echo("END schedule export task")


commands = [
    generate,
    generate_dsw,
]
