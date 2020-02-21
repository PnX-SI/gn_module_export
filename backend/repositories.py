"""
    Module de gestion des exports
"""

import sys
import logging

from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound

from flask import current_app

from pypnusershub.db.tools import InsufficientRightsError
from pypnusershub.db.models import User

from geonature.utils.env import DB

# from utils_flask_sqla.generic import GenericQuery, GenericTable
from utils_flask_sqla_geo.generic import GenericQueryGeo, GenericTableGeo

from geonature.core.users.models import CorRole


from .models import (Export, ExportLog, CorExportsRoles, ExportSchedules)

LOGGER = current_app.logger
LOGGER.setLevel(logging.DEBUG)


class EmptyDataSetError(Exception):
    """
        Erreur : Pas de données pour le jeu de données en question
    """

    def __init__(self, message=None):
        self.message = message






class ExportRepository():
    """
        Classe permetant de manipuler un export
    """

    def __init__(self, id_export, session=DB.session):
        self.session = session
        # Récupération de l'export
        self.id_export = id_export
        try:
            self.export = Export.query.filter_by(id=id_export).one()
        except NoResultFound:
            raise

    def _get_data(self, filters=None, limit=1000, offset=0, format="csv"):
        """
            Fonction qui retourne les données de l'export passé en paramètre
            en applicant des filtres s'il y a lieu

            .. :quickref: lance une requete qui récupère les données
                    pour un export donné


            :query Export export_: Définition de l'export
            :query str geom_column_header: Nom de la colonne géometry
                        si elle existe
            :query {} filters: Filtres à appliquer sur les données
            :query int limit: Nombre maximum de données à retourner
            :query int offset: Numéro de page à retourner

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

        if not filters:
            filters = dict()

        query = GenericQueryGeo(
            DB,
            self.export.view_name, self.export.schema_name,
            filters,
            limit, offset,
            self.export.geometry_field
        )

        # Export différent selon le format demandé
        #   shp ou geojson => geo_feature
        #   json =>

        EXPORT_FORMAT = current_app.config['EXPORTS']['export_format_map']
        if (
            self.export.geometry_field
            and
            EXPORT_FORMAT[format]['geofeature']
        ):
            data = query.as_geofeature()
        else:
            data = query.return_query()
        # Ajout licence
        if self.export:
            export_license = (self.export.as_dict(True)).get('licence', None)
            data['license'] = dict()
            data['license']['name'] = export_license.get('name_licence', None)
            data['license']['href'] = export_license.get('url_licence', None)

        return (query.view.db_cols, data)

    def get_export_with_logging(self,
        info_role,
        with_data=False,
        filters=None,
        limit=1000,
        offset=0,
        export_format="json"
    ):
        """
            Fonction qui retourne les données pour un export données

        .. :quickref: retourne les données pour un export données


        :query {} info_role: Role ayant demandé l'export
        :query boolean with_data: Indique si oui ou non la fonction
                retourne les données associées à l'export.
                Si non retourne la définition de l'export
        :query {} filters: Filtres à appliquer sur les données
        :query int limit: Nombre maximum de données à retourner
        :query int offset: Numéro de page à retourner
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
        result = None
        end_time = None
        log = None
        status = -2
        start_time = datetime.utcnow()

        if not filters:
            filters = dict()

        try:
            # Test si l'export est autorisé
            try:
                self.get_export_is_allowed(info_role)
            except (NoResultFound) as exp:
                LOGGER.warn('repository.get_by_id(): %s', str(exp))
                raise

            if not with_data or not export_format:
                return self.export.as_dict(True)

            columns, data = self._get_data(
                filters=filters,
                limit=limit,
                offset=offset,
                format=export_format
            )

            if len(data.get('items')) == 0:
                raise EmptyDataSetError(
                    'Empty dataset for export id {} with id_role {}.'.format(
                        self.id_export, info_role.id_role
                    )
                )

            status = 0

            result = (self.export.as_dict(True), columns, data)

            end_time = datetime.utcnow()

            ExportLog.record({
                'id_role': info_role.id_role,
                'id_export': self.export.id,
                'format': export_format,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'log': log
            })
            return result
        except (
                InsufficientRightsError,
                NoResultFound,
                EmptyDataSetError
        ) as e:
            LOGGER.warn('repository.get_by_id(): %s', str(e))
            raise
        except Exception as e:
            LOGGER.critical('exception: %s', e)
            raise

    def get_export_is_allowed(self, info_role):
        """
            Test si un role à les droits sur un export
        """
        q = Export.query.outerjoin(
            CorExportsRoles
        ).filter(
            Export.id == self.id_export
        ).filter(
            get_filter_corexportsroles_clause(info_role)
        )
        return q.one()


def get_allowed_exports(info_role):
    """
        Liste des exports autorisés pour un role
    """
    q = Export.query\
        .outerjoin(CorExportsRoles)\
        .filter(get_filter_corexportsroles_clause(info_role))\
        .order_by(Export.id.desc())

    result = q.all()
    if not result:
        raise NoResultFound('No configured export')
    return result


def get_filter_corexportsroles_clause(info_role):
    """
        Fonction qui construit une clause where qui permet de savoir
        si un role à des droits sur les exports
    """
    return DB.or_(
        CorExportsRoles.id_role == info_role.id_role,
        CorExportsRoles.id_role == info_role.id_organisme,
        CorExportsRoles.id_role.in_(
            User.query.with_entities(User.id_role)
            .join(CorRole, CorRole.id_role_groupe == User.id_role)
            .filter(CorRole.id_role_utilisateur == info_role.id_role)
        ),
        Export.public == True
    )

SWAGGER_TYPE_COR = {
    "INTEGER": {"type": "int", "format": "int32"},
    "BIGINT": {"type": "int", "format": "int64"},
    "TEXT": {"type": "string"},
    "UUID": {"type": "string", "format": "uuid"},
    "VARCHAR": {"type": "string"},
    "TIMESTAMP": {"type": "string", "format": "date-time"},
    "TIME": {"type": "string", "format": "date-time"},
    "DATE": {"type": "string", "format": "date"}
}


def generate_swagger_spec(id_export):
    """
        Fonction qui permet de générer dynamiquement
        les spécifications swagger d'un export
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
        srid=export.geometry_srid
    )

    for column in export_table.tableDef.columns:
        type = {"type": "string"}
        if column.type.__class__.__name__ in SWAGGER_TYPE_COR:
            type = SWAGGER_TYPE_COR[column.type.__class__.__name__]
        swagger_parameters.append({
            "in": "query",
            "name": column.name,
            "description": column.comment,
            **type
        })
    general_params = [
        {
            "in": "query",
            "name": "limit",
            "type": "int",
            "description": "nombre maximum de résultats à retourner"
        },
        {
            "in": "query",
            "name": "offset",
            "type": "int",
            "description": "numéro de page"
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
