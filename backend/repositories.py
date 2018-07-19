import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
from geonature.utils.env import DB
from .models import (Export, ExportLog)
from geonature.utils.utilssqlalchemy import (GenericQuery, GenericTable)


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class ExportRepository(object):
    def __init__(self, session=DB.session):
        self.session = session

    def get_data(
            self, view, schema,
            geom_column_header=None, filters={},
            limit=10000, paging=0):

        logger.debug('Querying "%s"."%s"', schema, view)

        # public.geometry_columns
        data = GenericQuery(
            DB.session, view, schema, geom_column_header,
            filters, limit, paging).return_query()

        logger.debug('Query results: %s', data)
        return data

    def get_one(self, id_export, info_role):
        export = Export.query.get(id_export)
        if export:
            # TODO: filters
            data = self.get_data(export.view_name, export.schema_name)
            try:
                ExportLog.log(
                    id_export=export.id, format='json', id_user=info_role)
            except Exception as e:
                DB.session.rollback()
                logger.critical('%s', str(e))
                return {'error': 'Echec de journalisation.'}

            return (export.as_dict(), data.get('items', None))
        else:
            raise NoResultFound('Unknown export id {}.'.format(id_export))

    def create(self, **kwargs):
        x = Export(**kwargs)
        self.session.add(x)
        self.session.flush()
        return x
