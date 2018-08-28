import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
from geonature.utils.env import DB
from pypnusershub.db.tools import InsufficientRightsError

from .models import (Export, ExportLog)
from .utils.exportquery import ExportQuery


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class ExportRepository(object):
    def __init__(self, session=DB.session):
        self.session = session

    # TODO: get_formats()
    # suggested output format list for current selection to export to.

    def _get_data(
            self, info_role, view, schema,
            geom_column_header=None, filters=None, limit=10000, paging=0):

        logger.debug('Querying "%s"."%s"', schema, view)

        query = ExportQuery(
            info_role, self.session, view, schema, geom_column_header,
            filters, limit, paging)

        columns = [col.name for col in query.view.db_cols]

        # data = query.return_query(policy=None)
        data = query.return_query()
        return (columns, data)

    def get_by_id(
            self,
            info_role,
            id_export,
            with_data=False,
            geom_column_header=None,
            filters=None,
            limit=10000,
            paging=0,
            format=None):
        export = Export.query.get(id_export)
        if not export:
            raise NoResultFound('Unknown export id {}.'.format(id_export))
        if with_data and format:
            try:
                columns, data = self._get_data(
                    info_role, export.view_name, export.schema_name,
                    geom_column_header=geom_column_header,
                    filters=filters,
                    limit=limit,
                    paging=paging)
            except InsufficientRightsError as e:
                logger.warn('InsufficientRightsError')
                raise e
            except Exception as e:
                logger.critical('%s', str(e))
                raise e
            else:
                ExportLog.log(
                    id_export=export.id, format=format,
                    id_user=info_role.id_role)

                return (export.as_dict(), columns, data)
        else:
            return export.as_dict()

    def get_list(self, all=False):
        if not all:
            xs = Export.query.filter(Export.deleted.is_(None)).all()
        else:
            xs = Export.query.all()
        return xs

    def create(self, **kwargs):
        # TODO: create view
        try:
            x = Export(**kwargs)
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
            ExportLog.log(
                id_export=x.id, format='crea', id_user=x.id_creator)
            return x

    def update(self, **kwargs):
        # TODO: drop/recreate/refresh view
        x = self.get_by_id(kwargs['id_export'])
        if not x:
            raise NoResultFound(
                'Unknown export id: {}'.format(kwargs['id_export']))
        try:
            x.__dict__.update(
                (k, v) for k, v in kwargs.items() if k in x.__dict__)
            self.session.add(x)
            self.session.flush()
        except Exception as e:
            self.session.rollback()
            logger.warn('%s', str(e))
            raise e
        else:
            ExportLog.log(
                id_export=x.id, format='upda', id_user=kwargs['id_role'])
            return x

    def delete(self, id_role, id_export):
        # TODO: drop view
        x = self.get_by_id(id_export)
        x.deleted = datetime.utcnow()
        try:
            self.session.add(x)
            self.session.flush()
        except Exception as e:
            logger.critical('%s', str(e))
            raise e('Echec de journalisation.')
        else:
            ExportLog.log(
                id_export=x.id, format='dele', id_user=id_role)

    def getCollections(self):
        # all tables and views
        # and filter out unwanted (spatial_ref_sys & co)
        # or walk bib_tables_location ?
        from sqlalchemy.engine import reflection

        inspection = reflection.Inspector.from_engine(DB.engine)
        schemas = {}
        schema_names = inspection.get_schema_names()
        # schema_names = ['gn_synthese']
        for schema in schema_names:
            tables = {}
            mapped_tables = inspection.get_table_names(schema=schema)
            logger.debug('schema: %s %s', schema, mapped_tables)
            for table in mapped_tables:
                columns = {}
                mapped_columns = inspection.get_columns(table, schema=schema)
                for c in mapped_columns:
                    c['type'] = str(c['type'])
                    columns.update({c['name']: c})
                tables.update({table: columns})
            schemas.update({schema: tables})
        return schemas
