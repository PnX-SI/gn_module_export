"""
    Module de gestion des exports
"""

import sys
import logging

from werkzeug.exceptions import Forbidden
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound

from flask import current_app, g


from geonature.utils.env import DB

# from utils_flask_sqla.generic import GenericQuery, GenericTable
from utils_flask_sqla_geo.generic import GenericQueryGeo, GenericTableGeo


from .models import Export, ExportLog, ExportSchedules


class EmptyDataSetError(Exception):
    """
    Erreur : Pas de données pour le jeu de données en question
    """

    def __init__(self, message=None):
        self.message = message


class ExportObjectQueryRepository:
    def __init__(self, id_export, info_role=None, filters=None, limit=1000, offset=0):
        """
            Classe permettant de manipuler l'objet export
            Permet d'interroger la vue définie par l'export
            et de récupérer les données

        Args:
            id_export (int): Indentifiant de l'export (t_exports)
            session ([type], optional): [description]. Defaults to DB.session.
            filters ({}, optional):Filtres à appliquer sur les données. Defaults to None.
            limit (int, optional): Nombre maximum de données à retourner. Defaults to 1000.
            offset (int, optional): Numéro de page à retourner. Defaults to 0.
        """
        # Test si l'export est autorisé
        self.id_export = id_export
        self.info_role = info_role
        try:
            self.export = Export.query.get(self.id_export)
            if self.info_role:
                self.export = self.get_export_is_allowed()
        except NoResultFound:
            raise Forbidden(
                ('Not allowed to access to export : "{}"').format(
                    self.id_export,
                )
            )

        if not filters:
            filters = dict()

        self.exportobject_query_definition = GenericQueryGeo(
            DB,
            self.export.view_name,
            self.export.schema_name,
            filters,
            limit,
            offset,
            self.export.geometry_field,
        )

    def _get_export_columns_definition(self):
        """
        Export de la définition des colonnes de la vue

        """
        return self.exportobject_query_definition.view.db_cols

    def _get_data(self, format="csv"):
        """
        Fonction qui retourne les données de l'export passé en paramètre
        en appliquant des filtres s'il y a lieu

        .. :quickref: lance une requete qui récupère les données
                pour un export donné


        **Returns:**

        .. sourcecode:: http

            {
                'total': Number total of results,
                'total_filtered': Number of results after filteer ,
                'page': Page number,
                'limit': Limit,
                'items': data on GeoJson format
                'licence': information of licence associated to data
            }

        """

        # Export dilimitfférent selon le format demandé
        #   shp ou geojson => geo_feature
        #   json =>

        EXPORT_FORMAT = current_app.config["EXPORTS"]["export_format_map"]
        if self.export.geometry_field and EXPORT_FORMAT[format]["geofeature"]:
            data = self.exportobject_query_definition.as_geofeature()
        else:
            data = self.exportobject_query_definition.return_query()
        # Ajout licence
        if self.export:
            try:
                export_license = (self.export.as_dict(fields=["licence"])).get("licence", None)
                data["license"] = dict()
                data["license"]["name"] = export_license.get("name_licence", None)
                data["license"]["href"] = export_license.get("url_licence", None)
            except Exception as e:
                print(e)
                pass
        return data

    def get_export_with_logging(self, export_format="json"):
        """
            Fonction qui retourne les données pour un export données
            et qui enregistre l'opération dans la table des logs

        .. :quickref: retourne les données pour un export données


        :query str export_format: format de l'export (csv, json, shp)

        **Returns:**

        .. sourcecode:: http

            {
                'total': Number total of results,
                'total_filtered': Number of results after filteer ,
                'page': Page number,
                'limit': Limit,
                'items': data on GeoJson format
                'licence': information of licence associated to data
            }


        """
        log = None
        status = -2
        start_time = datetime.utcnow()
        end_time = None

        data = self._get_data(format=export_format)
        if len(data.get("items")) == 0:
            raise EmptyDataSetError(
                "Empty dataset for export id {} with id_role {}.".format(
                    self.id_export, g.user.id_role
                )
            )

        status = 0

        end_time = datetime.utcnow()

        ExportLog.record(
            {
                "id_role": self.info_role.id_role,
                "id_export": self.export.id,
                "format": export_format,
                "start_time": start_time,
                "end_time": end_time,
                "status": status,
                "log": log,
            }
        )
        return data

    def get_export_is_allowed(self):
        """
        Test si un role a les droits sur un export
        """
        q = Export.query.filter(Export.id == self.id_export).get_allowed_exports(
            user=self.info_role
        )
        return q.one()


SWAGGER_TYPE_COR = {
    "INTEGER": {"type": "int", "format": "int32"},
    "BIGINT": {"type": "int", "format": "int64"},
    "TEXT": {"type": "string"},
    "UUID": {"type": "string", "format": "uuid"},
    "VARCHAR": {"type": "string"},
    "TIMESTAMP": {"type": "string", "format": "date-time"},
    "TIME": {"type": "string", "format": "date-time"},
    "DATE": {"type": "string", "format": "date"},
}


def generate_swagger_spec(id_export):
    """
    Fonction qui permet de générer dynamiquement
    les spécifications Swagger d'un export
    """
    swagger_parameters = []
    try:
        export = Export.query.filter(Export.id == id_export).one()
    except (NoResultFound, EmptyDataSetError) as e:
        raise e

    export_table = GenericTableGeo(
        tableName=export.view_name,
        schemaName=export.schema_name,
        engine=DB.engine,
        geometry_field=export.geometry_field,
        srid=export.geometry_srid,
    )

    for column in export_table.tableDef.columns:
        type = {"type": "string"}
        if column.type.__class__.__name__ in SWAGGER_TYPE_COR:
            type = SWAGGER_TYPE_COR[column.type.__class__.__name__]
        swagger_parameters.append(
            {"in": "query", "name": column.name, "description": column.comment, **type}
        )
    general_params = [
        {
            "in": "query",
            "name": "limit",
            "type": "int",
            "description": "Nombre maximum de résultats à retourner",
        },
        {"in": "query", "name": "offset", "type": "int", "description": "Numéro de page"},
        {
            "in": "query",
            "name": "orderby",
            "type": "varchar",
            "description": "Nom d'un champ de la vue qui sera utilisé comme variable de tri. Une mention au sens du tri peut être ajoutée en utilisant la syntaxe suivante : nom_col[:ASC|DESC]",
        }
    ]
    return general_params + swagger_parameters


def get_export_schedules():
    """
    Liste des exports automatiques
    """
    try:
        q = DB.session.query(ExportSchedules)
        result = q.all()
    except Exception as exception:
        raise
    return result
