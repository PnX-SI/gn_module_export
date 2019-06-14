import sys
import logging
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
# from geonature.core.gn_meta.models import TDatasets
from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import GenericQuery, GenericTable
from pypnusershub.db.tools import InsufficientRightsError
from pypnusershub.db.models import User
from geonature.core.users.models import CorRole

from .models import (Export, ExportLog, CorExportsRoles)


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class Error(Exception):
    pass


class EmptyDataSetError(Error):
    def __init__(self, message=None):
        self.message = message


class ExportRepository(object):

    def __init__(self, session=DB.session):
        self.session = session

    def _get_data(
            self, info_role, export_,
            geom_column_header=None,
            filters=dict(),
            limit=10000, offset=0
    ):
        """
            Fonction qui retourne les données de l'export passé en paramètre
            en applicant des filtres s'il y a lieu
        """
        query = GenericQuery(
            self.session,
            export_.view_name, export_.schema_name, geom_column_header,
            filters,
            limit, offset
        )
        data = query.return_query()
        return (query.view.db_cols, data)

    def get_by_id(
            self,
            info_role,  # information sur le role du compte demandant l'export
            id_export,  # identifiant du role
            with_data=False,  # Indique si oui ou non la fonction retourne les données associées à l'export. Si non retourne la définition de l'export
            filters=dict(),  # Filtres à appliquer sur les données
            limit=1000,  # Nombre maximale de données à retourner
            offset=0,  # Numéro de page à retourner
            export_format=None  # Format de l'export
    ):
        result = None
        end_time = None
        log = None
        exc = None
        status = -2
        start_time = datetime.utcnow()
        try:
            try:
                self.getExportIsAllowed(id_export, info_role)
            except (NoResultFound) as e:
                logger.warn('repository.get_by_id(): %s', str(e))
                exc = e
                raise

            export_ = Export.query.filter_by(id=id_export).one()

            logger.debug('export: %s', export_.as_dict())

            if with_data and export_format:
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
                    info_role,
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
            else:
                return export_.as_dict()

        except (InsufficientRightsError,
                NoResultFound,
                EmptyDataSetError) as e:
            logger.warn('repository.get_by_id(): %s', str(e))
            exc = e
            raise
        except Exception as e:
            exc = e
            logger.critical('exception: %s', e)
            raise
        else:
            status = 0
            result = (export_.as_dict(), columns, data)
        finally:
            end_time = datetime.utcnow()
            if exc:
                tb = sys.exc_info()
                if (isinstance(exc, InsufficientRightsError)
                        or isinstance(exc, EmptyDataSetError)):
                    raise
                elif isinstance(exc, NoResultFound):
                    raise NoResultFound(
                        'Unknown export id {}.'.format(id_export))
                else:
                    log = str(tb)
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
                logger.critical('export error: %s', tb)
                raise
            else:
                return result

    def getfilter_CorExportsRoles_clause(self, info_role):
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

    def getAllowedExports(self, info_role):

        q = Export.query\
                  .outerjoin(CorExportsRoles)\
                  .filter(self.getfilter_CorExportsRoles_clause(info_role))\
                  .order_by(Export.id.desc())

        result = q.all()
        if not result:
            raise NoResultFound('No configured export')
        return result

    def getExportIsAllowed(self, id_export, info_role):
        q = Export.query.outerjoin(
                CorExportsRoles
            ).filter(
                Export.id == id_export
            ).filter(
                self.getfilter_CorExportsRoles_clause(info_role)
            )

        return q.one()

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

    exportTable = GenericTable(
        tableName=export.view_name,
        schemaName=export.schema_name,
        geometry_field=export.geometry_field,
        srid=export.geometry_srid
    )
    for column in exportTable.tableDef.columns:
        swagger_parameters.append({
            "in": "query",
            "name": column.name,
            "schema": {
              "type": column.type.__class__.__name__
            },
            "description": "The numbers of items to return"
        })
        print(column.name, column.type.__class__.__name__)

    return swagger_parameters