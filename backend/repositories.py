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
        from sqlalchemy.engine import reflection

        IGNORE = {
            'information_schema': '*',
            'public': ['spatial_ref_sys']
        }
        inspection = reflection.Inspector.from_engine(DB.engine)
        schemas = {}
        schema_names = [
            schema
            for schema in inspection.get_schema_names()
            if IGNORE.get(schema, None) != '*'
        ]
        for schema in schema_names:
            tables = {}
            mapped_tables = inspection.get_table_names(schema=schema)
            mapped_tables = [
                t for t in mapped_tables
                if not(IGNORE.get(schema, False) and t in IGNORE.get(schema))]
            for table in mapped_tables:
                columns = {}
                mapped_columns = inspection.get_columns(table, schema=schema)
                pk_constraints = inspection.get_primary_keys(
                    table, schema=schema)
                fks = inspection.get_foreign_keys(table, schema)
                fk_constraints = {
                    k: fk
                    for fk in fks for k in fk['constrained_columns']}

                for c in mapped_columns:

                    c['type'] = str(c['type'])

                    if c['name'] in fk_constraints.keys():
                        c['fk_constraints'] = {
                            key: fk_constraints[c['name']][key]
                            for key in {
                                'referred_schema',
                                'referred_table',
                                'referred_columns'}
                        }

                    if c['name'] in pk_constraints:
                        c['is_primary_key'] = True

                    columns.update({c['name']: c})
                tables.update({table: columns})
            schemas.update({schema: tables})

        models = [m for m in DB.Model._decl_class_registry.values()
                  if hasattr(m, '__name__')]

        def modelname_from_tablename(schema, tablename):
            for m in models:
                if (hasattr(m, '__name__')
                    and hasattr(m, '__tablename__')
                    and m.__tablename__ == tablename
                    and m.__table__.schema == schema):  # noqa: E129
                    return m.__name__
            return ''

        return [{
                'name': s,
                'tables': [
                    {
                        'name': t,
                        'fields': [f for f in schemas[s][t]],
                        'model': modelname_from_tablename(s, t)
                    } for t in schemas[s]]
                } for s in schemas]
