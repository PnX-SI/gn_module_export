import sys
import logging
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
# from geonature.core.gn_meta.models import TDatasets
from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import GenericQuery
from pypnusershub.db.tools import InsufficientRightsError

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
            self, info_role, view, schema,
            geom_column_header=None, filters=[], limit=10000, paging=0):

        query = GenericQuery(self.session, view, schema, geom_column_header,
                             filters, limit, paging)

        # ored_filters = []
        # columns = [c.name for c in query.view.db_cols]
        # logger.debug('cols: %s', columns)
        #
        # if info_role.tag_object_code in {'1', '2'}:
        #     allowed_datasets = TDatasets.get_user_datasets(info_role)  # noqa: E501
        #
        #     if 'id_digitiser' in columns:
        #         ored_filters.append(
        #             query.view.db_cols['id_digitiser'] == info_role.id_role       # noqa: E501
        #         )
        #
        #     if 'observers' in columns:
        #         if info_role.tag_object_code == '1':
        #             ored_filters.append(
        #                 query.view.db_cols['observers'].any(id_role=info_role.id_role))  # noqa: E501
        #
        #     if info_role.tag_object_code == '2':
        #         ored_filters.append(
        #             query.view.db_cols['id_dataset'].in_(tuple(allowed_datasets)))  # noqa: E501
        #
        #     q = query.build_query_filters(query, filters)
        #     query = q.filter(DB.or_(*ored_filters))
        #     # TEST
        #     logger.debug('filters: %s', ored_filters)
        #
        # elif info_role.tag_object_code != '3':
        #     raise InsufficientRightsError

        data = query.return_query()
        return (query.view.db_cols, data)

    def get_by_id(
            self,
            info_role,
            id_export,
            with_data=False,
            filters=[],
            limit=10000,
            paging=0,
            format=None):
        result, end_time, log, e = None, None, None, None
        status = -2
        start_time = datetime.utcnow()
        try:
            export = Export.query.filter_by(id=id_export).one()
            if with_data and format:
                geometry = (
                    export.geometry_field
                    if (hasattr(export, 'geometry_field')
                        and current_app.config['export_format_map'][format]['geofeature'])  # noqa: E501
                    else None)

                columns, data = self._get_data(
                    info_role,
                    export.view_name,
                    export.schema_name,
                    geom_column_header=geometry,
                    filters=filters,
                    limit=limit,
                    paging=paging)

                if not data.get('items', False) or len(data.get('items')) == 0:
                    raise EmptyDataSetError(
                        'Empty dataset for export id {}.'.format(id_export))
            else:
                return export.as_dict()

        except (
                InsufficientRightsError,
                NoResultFound,
                EmptyDataSetError) as e:
            logger.warn('repository.get_by_id(): %s', str(e))
            raise
        except Exception as e:
            logger.critical('exception: %s', e)
            raise
        else:
            status = 0
            result = (export.as_dict(), columns, data)
        finally:
            end_time = datetime.utcnow()
            if e:
                tb = sys.exc_info()
                if (isinstance(e, InsufficientRightsError)
                        or isinstance(e, EmptyDataSetError)):  # noqa: E129 W503
                    raise
                elif isinstance(e, NoResultFound):
                    raise NoResultFound(
                        'Unknown export id {}.'.format(id_export))
                else:
                    log = str(tb)
                    status = -1

            ExportLog.record({
                'id_role': info_role.id_role,
                'id_export': export.id,
                'format': format,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'log': log})

            if status != 0 or e:
                logger.critical('export error: %s', tb)
                raise
            else:
                return result

    def list(self, info_role):
        from geonature.core.users.models import (TRoles, CorRole)

        q = Export.query\
                  .join(CorExportsRoles)\
                  .filter(
                        DB.or_(
                            CorExportsRoles.id_role == info_role.id_role,
                            CorExportsRoles.id_role == info_role.id_organisme,
                            CorExportsRoles.id_role.in_(
                                TRoles.query.with_entities(TRoles.id_role)
                                            .join(CorRole, CorRole.id_role_groupe == TRoles.id_role)      # noqa: E501
                                            .filter(CorRole.id_role_utilisateur == info_role.id_role)),   # noqa: E501
                            Export.public == True))\
                  .order_by(Export.id.desc())

        result = q.all()
        if not result:
            raise NoResultFound('No configured export')
        return result
