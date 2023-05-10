import os
import click
import logging
from pathlib import Path
from datetime import datetime

from flask.cli import with_appcontext
from click import ClickException

from gn_module_export.tasks import generate_export
from gn_module_export.models import Export
from gn_module_export.utils_export import ExportGenerationNotNeeded


@click.command()
@click.option("--format", "export_format", default="csv")
@click.option(
    "--scheduled/--user",
    default=False,
    help="Générer un export de type planifié ou utilisateur.",
)
@click.option(
    "--skip-newer-than",
    type=int,
    help="Ne pas regénérer les fichiers récents (en minutes).",
)
@click.argument("export_id")
@with_appcontext
def generate(export_id, export_format, scheduled, skip_newer_than):
    """
    Lance la génération d’un fichier d’export
    """
    export = Export.query.get(export_id)
    if export is None:
        raise ClickException(f"Export {export_id} not found.")
    try:
        generate_export(
            export_id,
            export_format,
            filename="",
            user=None,
            scheduled=scheduled,
            skip_newer_than=skip_newer_than,
        )
    except ExportGenerationNotNeeded:
        click.echo(f"Export {export_id} sufficiently recent, skip generation.")


@click.command()
@click.option(
    "--limit", required=False, default=-1, help="Nombre de résultats à retourner"
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

    click.echo(
        "Export done with success data are available here: {}".format(export_dsw_dir)
    )
    click.echo("END schedule export task")


commands = [
    generate,
    generate_dsw,
]
