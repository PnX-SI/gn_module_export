import sys
import logging
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
# from geonature.core.gn_meta.models import TDatasets
from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import GenericQuery
from pypnusershub.db.tools import InsufficientRightsError
from geonature.core.users.models import (TRoles, CorRole)

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
            limit=10000, offset=0):
        query = GenericQuery(
            self.session,
            export_.view_name, export_.schema_name, geom_column_header,
            filters,
            limit, offset)
        data = query.return_query()
        return (query.view.db_cols, data)

    def get_by_id(
            self,
            info_role,
            id_export,
            with_data=False,
            filters=dict(),
            limit=10000,
            offset=0,
            export_format=None):
        result = None
        end_time = None
        log = None
        exc = None
        status = -2
        start_time = datetime.utcnow()
        try:
            export_ = Export.query.filter_by(id=id_export)\
                            .join(CorExportsRoles)\
                            .filter(
                                DB.or_(
                                    CorExportsRoles.id_role == info_role.id_role,                                # noqa: E501
                                    CorExportsRoles.id_role == info_role.id_organisme,                           # noqa: E501
                                    CorExportsRoles.id_role.in_(
                                        TRoles.query.with_entities(TRoles.id_role)                               # noqa: E501
                                                    .join(CorRole, CorRole.id_role_groupe == TRoles.id_role)     # noqa: E501
                                                    .filter(CorRole.id_role_utilisateur == info_role.id_role)),  # noqa: E501
                                    Export.public == True))\
                            .one()
            logger.debug('export: %s', export_.as_dict())
            if with_data and export_format:
                geometry = (
                    export_.geometry_field
                    if (hasattr(export_, 'geometry_field')
                        and current_app.config['export_format_map'][export_format]['geofeature'])             # noqa: E501
                    else None)

                columns, data = self._get_data(
                    info_role,
                    export_,
                    geom_column_header=geometry,
                    filters=filters,
                    limit=limit,
                    offset=offset)

                if len(data.get('items')) == 0:
                    raise EmptyDataSetError(
                        'Empty dataset for export id {} with id_role {}.'.format(                             # noqa: E501
                            id_export, info_role.id_role))
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

    def getAllowedExports(self, info_role):
        q = Export.query\
                  .join(CorExportsRoles)\
                  .filter(
                        DB.or_(
                            CorExportsRoles.id_role == info_role.id_role,
                            CorExportsRoles.id_role == info_role.id_organisme,
                            CorExportsRoles.id_role.in_(
                                TRoles.query.with_entities(TRoles.id_role)
                                            .join(CorRole, CorRole.id_role_groupe == TRoles.id_role)           # noqa: E501
                                            .filter(CorRole.id_role_utilisateur == info_role.id_role)),        # noqa: E501
                            Export.public == True))\
                  .order_by(Export.id.desc())

        result = q.all()
        if not result:
            raise NoResultFound('No configured export')
        return result
