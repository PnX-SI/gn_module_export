import sys
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
from geonature.utils.env import DB
from pypnusershub.db.tools import InsufficientRightsError

from .models import (Export, ExportLog)
from .utils.query import ExportQuery


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class ExportRepository(object):
    def __init__(self, session=DB.session):
        self.session = session

    # TODO: get_outputs()

    def _get_data(
            self, id_role, view, schema,
            geom_column_header=None, filters=None, limit=10000, paging=0):

        logger.debug('Querying "%s"."%s"', schema, view)

        query = ExportQuery(
            id_role, self.session, view, schema, geom_column_header,
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
            else:
                return export.as_dict()

        except (InsufficientRightsError, NoResultFound) as e:
            logger.warn('%s', str(e))
            raise
        except Exception as e:
            logger.critical('exception: %s', e)
            raise
        else:
            log = str(columns)
            status = 0
            result = (export.as_dict(), columns, data)
        finally:
            end_time = datetime.utcnow()
            e = sys.exc_info()
            if any(e):
                if isinstance(e, InsufficientRightsError):
                    raise e
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
                logger.critical('unmanaged export error: %s', e)
                raise e
            else:
                return result

    def list(self):
        # TODO: list(self, filters)
        result = Export.query.all()
        if not result:
            raise NoResultFound('No configured export')
        return result

    def create(self, adict):
        # TODO: adict.pop('selectable') and create_view(selectable)
        try:
            x = Export.from_dict(adict)
            self.session.add(x)
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            logger.warn('%s', str(e))
            raise e
        except Exception as e:
            self.session.rollback()
            logger.warn('%s', str(e))
            raise e
        else:
            return x

    def update(self, adict):
        # TODO: drop/recreate/refresh view
        x = self.get_by_id(adict['id_export'])
        if not x:
            raise NoResultFound(
                'Unknown export id: {}'.format(adict['id_export']))
        try:
            x.__dict__.update(
                (k, v)
                for k, v in adict.items()
                if k in x.__dict__ and not callable(v))
            self.session.add(x)
            self.session.flush()
        except Exception as e:
            self.session.rollback()
            logger.warn('%s', str(e))
            raise e
        else:
            return x

    def delete(self, id_role, id_export):
        try:
            self.get_by_id(id_export).delete()
            # TODO: drop view if view.schema == DEFAULT_SCHEMA
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.critical('%s', str(e))
            raise

    def getCollections(self):
        # all tables and views
        from sqlalchemy.engine import reflection

        inspection = reflection.Inspector.from_engine(DB.engine)
        schemas = {}
        schema_names = inspection.get_schema_names()
        # TODO: filter out spatial_ref_sys & co
        for schema in schema_names:
            tables = {}
            mapped_tables = inspection.get_table_names(schema=schema)
            for table in mapped_tables:
                columns = {}
                mapped_columns = inspection.get_columns(table, schema=schema)
                for c in mapped_columns:
                    c['type'] = str(c['type'])
                    columns.update({c['name']: c})
                tables.update({table: columns})
            schemas.update({schema: tables})
        return schemas
