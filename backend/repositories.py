import sys
import logging
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
from geonature.utils.env import DB
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

    # TODO: get_outputs()

    def _get_data(
            self, id_role, view, schema,
            geom_column_header=None, filters=None, limit=10000, paging=0):

        logger.debug('Querying "%s"."%s"', schema, view)

        # TODO: id_role
        query = GenericQuery(
            self.session, view, schema, geom_column_header,
            filters, limit, paging)

        data = query.return_query()
        return (query.view.db_cols, data)

    def get_by_id(
            self,
            id_role,
            id_export,
            with_data=False,
            filters=None,
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
                    id_role,
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
                'id_role': id_role,
                'id_export': export.id,
                'format': format,
                'start_time': start_time,
                'end_time': end_time,
                'status': status,
                'log': log})

            if status == -1 and any(e):
                logger.critical('export error: %s', e)
                raise
            else:
                return result

    def list(self, **kwargs):
        q = Export.query

        # FIXME: #14 id_role in groups 'Grp_en_poste', 'Grp_admin'
        id_role = kwargs.pop('id_role')
        q = q.join(CorExportsRoles)\
             .filter(CorExportsRoles.id_role == id_role)

        while kwargs:
            k, v = kwargs.popitem()
            q = q.filter(getattr(Export, k) == v)

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
