# Fonctions permettant la génération des fichiers d'export
import json
import shutil

from datetime import datetime

from pathlib import Path
from geoalchemy2.shape import from_shape
from shapely.geometry import asShape

from geonature.utils.utilssqlalchemy import generate_csv_content
from geonature.utils.utilsgeometry import FionaShapeService

from geonature.utils.filemanager import (
    removeDisallowedFilenameChars
)
from .repositories import (
    ExportRepository
)
from .send_mail import export_send_mail


def export_filename(export):
    return '{}_{}'.format(
        removeDisallowedFilenameChars(export.get('label')),
        datetime.now().strftime('%Y_%m_%d_%Hh%Mm%S')
    )


def thread_export_data(id_export, export_format, info_role, filters, user):
    """
        Lance un thread qui permet d'executer les fonctions d'export
            en arrière plan

        .. :quickref: Lance un thread qui permet d'executer les fonctions d'export
            en arrière plan

        :query int id_export: Identifiant de l'export
        :query str export_format: format de l'export (csv, json, shp)
        :query {} info_role: Information du role
        :query {} filters: Filtre à appliquer sur l'export
        :query User user: Objet user


        **Returns:**
        .. void
    """

    repo = ExportRepository()

    # export data
    export, columns, data = repo.get_by_id(
        info_role, id_export, with_data=True,
        export_format=export_format,
        filters=filters, limit=-1, offset=0
    )
    # Generate and store export file
    file_name = export_filename(export)
    full_file_name = GenerateExport(
        file_name=file_name,
        format=export_format,
        data=data,
        columns=columns,
        export=export
    ).generate_data_export()

    # Send mail
    export_send_mail(
        role=user,
        export=export,
        file_name=full_file_name
    )


class GenerateExport():
    def __init__(self, file_name, format, data, columns, export):
        self.file_name = file_name
        self.format = format
        self.data = data
        self.columns = columns
        self.export = export
        self.has_geometry = export.get('geometry_field', None)


    def generate_data_export(self):
        from .blueprint import EXPORTS_DIR
        out = None

        if self.format not in ['json', 'csv', 'shp']:
            raise Exception('Unsuported format')

        if (
            self.format == 'shp' and
            self.has_geometry
        ):
            self.generate_shp()
            return self.file_name + '.zip'
        if self.format == 'json':
            out = self.generate_json()
        elif self.format == 'csv':
            out = self.generate_csv()

        if out:
            with open(
                Path(EXPORTS_DIR, self.file_name + '.' + self.format),
                'a'
            ) as f:
                f.write(out)
        return self.file_name + '.' + self.format

    def generate_csv(self):
        return generate_csv_content(
            columns=[c.name for c in self.columns],
            data=self.data.get('items'),
            separator=','
        )

    def generate_json(self):
        return json.dumps(
            self.data,
            ensure_ascii=False,
            indent=4
        )

    def generate_shp(self):
        from .blueprint import EXPORTS_DIR
        FionaShapeService.create_shapes_struct(
            db_cols=self.columns,
            srid=self.export.get('geometry_srid'),
            dir_path=EXPORTS_DIR,
            file_name=self.file_name
        )

        items = self.data.get('items')

        for feature in items['features']:
            geom, props = (
                feature.get(field) for field in ('geometry', 'properties')
            )

            FionaShapeService.create_feature(
                props, from_shape(
                    asShape(geom), self.export.get('geometry_srid')
                )
            )

        FionaShapeService.save_and_zip_shapefiles()

        # Suppression des fichiers générés et non compressé
        for gtype in ['POINT', 'POLYGON', 'POLYLINE']:
            p = Path(EXPORTS_DIR, gtype + '_' + self.file_name)
            if p.is_dir():
                shutil.rmtree(p)

        return True


