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


from .models import (Export, ExportLog, CorExportsRoles)


LOGGER = current_app.logger
LOGGER.setLevel(logging.DEBUG)


class Error(Exception):
    """
        Erreur Générale qui ne lance rien
        TODO un peu dangereux à mon sens
    """
    pass


class EmptyDataSetError(Error):
    """
        Erreur : Pas de données pour le jeu de données en question
    """

    def __init__(self, message=None):
        self.message = message


class ExportRepository():
    """
        Classe permetant de manipuler un export
    """

    def __init__(self, session=DB.session):
        self.session = session

    def _get_data(
            self,
            export_,
            geom_column_header=None,
            filters=None,
            limit=10000, offset=0
    ):
        """
            Fonction qui retourne les données de l'export passé en paramètre
            en applicant des filtres s'il y a lieu

            .. :quickref: lance une requete qui récupère les données pour un export donné


            :query Export export_: Définition de l'export
            :query str geom_column_header: Nom de la colonne géometry si elle existe
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
            export_.view_name, export_.schema_name,
            filters,
            limit, offset,
            geom_column_header
        )
        data = query.return_query()

        # Ajout licence
        if export_:
            export_license = (export_.as_dict(True)).get('licence', None)
            data['license'] = dict()
            data['license']['name'] = export_license.get('name_licence', None)
            data['license']['href'] = export_license.get('url_licence', None)

        return (query.view.db_cols, data)

    def get_by_id(
            self,
            info_role,
            id_export,
            with_data=False,
            filters=None,
            limit=1000,
            offset=0,
            export_format=None
    ):
        """
            Fonction qui retourne les données pour un export données

        .. :quickref: retourne les données pour un export données


        :query {} info_role: Role ayant demandé l'export
        :query int id_export: Identifiant de l'export
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
        exc = None
        status = -2
        start_time = datetime.utcnow()
        if not filters:
            filters = dict()

        try:
            # Test si l'export est autorisé
            try:
                self.get_export_is_allowed(id_export, info_role)
            except (NoResultFound) as exp:
                LOGGER.warn('repository.get_by_id(): %s', str(exp))
                exc = exp
                raise

            # Récupération de l'export
            export_ = Export.query.filter_by(id=id_export).one()

            if not with_data or not export_format:
                return export_.as_dict(True)

            geometry = (
                export_.geometry_field
                if (
                    hasattr(export_, 'geometry_field')
                    and
                    current_app.config['export_format_map'][export_format]['geofeature']
                )
                else None
            )

            columns, data = self._get_data(
                export_,
                geom_column_header=geometry,
                filters=filters,
                limit=limit,
                offset=offset
            )

            if len(data.get('items')) == 0:
                raise EmptyDataSetError(
                    'Empty dataset for export id {} with id_role {}.'.format(
                        id_export, info_role.id_role
                    )
                )

            status = 0

            result = (export_.as_dict(True), columns, data)

        except (
                InsufficientRightsError,
                NoResultFound,
                EmptyDataSetError
        ) as e:
            LOGGER.warn('repository.get_by_id(): %s', str(e))
            exc = e
            raise
        except Exception as e:
            exc = e
            LOGGER.critical('exception: %s', e)
            raise
        finally:
            end_time = datetime.utcnow()
            if exc:
                exp_tb = sys.exc_info()
                if (isinstance(exc, InsufficientRightsError)
                        or isinstance(exc, EmptyDataSetError)):
                    raise
                elif isinstance(exc, NoResultFound):
                    raise NoResultFound(
                        'Unknown export id {}.'.format(id_export))
                else:
                    log = str(exp_tb)
                    status = -1

            ExportLog.record({
                'id_role': info_role.id_role,
                'id_export': export_.id,
                'export_format': export_format,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'log': log})

            if status != 0 or exc:
                LOGGER.critical('export error: %s', exp_tb)
                raise
            else:
                return result

    def getfilter_corexportsroles_clause(self, info_role):
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

    def get_allowed_exports(self, info_role):
        """
            Liste des exports autorisés pour un role
        """
        q = Export.query\
                  .outerjoin(CorExportsRoles)\
                  .filter(self.getfilter_corexportsroles_clause(info_role))\
                  .order_by(Export.id.desc())

        result = q.all()
        if not result:
            raise NoResultFound('No configured export')
        return result

    def get_export_is_allowed(self, id_export, info_role):
        """
            Test si un role à les droits sur un export
        """
        q = Export.query.outerjoin(
            CorExportsRoles
        ).filter(
            Export.id == id_export
        ).filter(
            self.getfilter_corexportsroles_clause(info_role)
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
