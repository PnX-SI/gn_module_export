import sys
import logging
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
from geonature.utils.env import DB
from geonature.core.gn_meta.models import TDatasets
from pypnusershub.db.tools import InsufficientRightsError

from .models import (Export, ExportLog, CorExportsRoles)
from geonature.utils.utilssqlalchemy import GenericQuery


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

        logger.debug(
            'Querying "%s"."%s" with cruved "%s"', schema, view, info_role.__dict__)  # noqa: E501

        query = GenericQuery(
            self.session, view, schema, geom_column_header,
            filters, limit, paging)

        if info_role.tag_object_code in {'1', '2'}:
            allowed_datasets = TDatasets.get_user_datasets(info_role.id_role)  # noqa: E501
            if 'id_digitiser' in query.view.db_cols:
                ored_filters = [
                    query.view.db_cols.id_digitiser == info_role.id_role,         # noqa: E501
                    query.view.db_cols.observers.any(id_role=info_role.id_role),  # noqa: E501
                    query.view.db_cols.id_dataset.in_(tuple(allowed_datasets))    # noqa: E501
                ]
                filters.append(DB.or_(*ored_filters))

            elif 'id_digitiser' in query.view.db_cols:
                if info_role.tag_object_code == '1':
                    filters.append(
                        query.view.db_cols.id_digitiser == info_role.id_role)
                else:
                    ored_filters = [
                        query.view.db_cols.id_digitiser == info_role.id_role,
                        query.view.db_cols.id_dataset.in_(tuple(allowed_datasets))    # noqa: E501
                    ]
                    filters.append(DB.or_(*ored_filters))

            elif 'observers' in query.view.db_cols:
                if info_role.tag_object_code == '1':
                    filters.append(
                        query.view.db_cols.observers.any(id_role=info_role.id_role))  # noqa: E501
                else:
                    ored_filters = [
                        query.view.db_cols.id_digitiser == info_role.id_role,
                        query.view.db_cols.observers.any(id_role=info_role.id_role),  # noqa: E501
                        query.view.db_cols.id_dataset.in_(tuple(allowed_datasets))    # noqa: E501
                    ]
                    filters.append(DB.or_(*ored_filters))

        elif info_role.tag_object_code != '3':
            raise InsufficientRightsError

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
                    if (hasattr(export, 'geometry_field') and format != 'csv')
                    else None)

                columns, data = self._get_data(
                    info_role,
                    export.view_name,
                    export.schema_name,
                    geom_column_header=geometry,  # noqa: E501
                    filters=filters,
                    limit=limit,
                    paging=paging)

                if (not data.get('items', None) or len(data.get('items')) == 0):  # noqa: E501
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
            # log = str(columns)
            status = 0
            result = (export.as_dict(), columns, data)
        finally:
            end_time = datetime.utcnow()
            e = sys.exc_info()
            if any(e):
                if (isinstance(e, InsufficientRightsError)
                        or isinstance(e, EmptyDataSetError)):  # noqa: E129 W503
                    raise
                elif isinstance(e, NoResultFound):
                    raise NoResultFound(
                        'Unknown export id {}.'.format(id_export))
                else:
                    log = str(e)
                    status = -1

            ExportLog.record({
                'id_role': info_role.id_role,
                'id_export': export.id,
                'format': format,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'log': log})

            if status != 0 or any(e):
                logger.critical('export error: %s', e)
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
                                            .filter(CorRole.id_role_utilisateur == info_role.id_role))))  # noqa: E501

        logger.debug('query: %s', str(q))
        result = q.all()
        if not result:
            raise NoResultFound('No configured export')
        return result

    # def create(self, adict):
    #     from sqlalchemy.exc import IntegrityError
    #     try:
    #         x = Export.from_dict(adict)
    #         self.session.add(x)
    #         self.session.flush()
    #     except IntegrityError as e:
    #         self.session.rollback()
    #         logger.warn('%s', str(e))
    #         raise e
    #     except Exception as e:
    #         self.session.rollback()
    #         logger.warn('%s', str(e))
    #         raise e
    #     else:
    #         return x
    #
    # def update(self, adict):
    #     x = self.get_by_id(adict['id_export'])
    #     if not x:
    #         raise NoResultFound(
    #             'Unknown export id: {}'.format(adict['id_export']))
    #     try:
    #         x.__dict__.update(
    #             (k, v)
    #             for k, v in adict.items()
    #             if k in x.__dict__ and not callable(v))
    #         self.session.add(x)
    #         self.session.flush()
    #     except Exception as e:
    #         self.session.rollback()
    #         logger.warn('%s', str(e))
    #         raise e
    #     else:
    #         return x
    #
    # def delete(self, id_role, id_export):
    #     try:
    #         self.get_by_id(id_export).delete()
    #         self.session.commit()
    #     except Exception as e:
    #         self.session.rollback()
    #         logger.critical('%s', str(e))
    #         raise
