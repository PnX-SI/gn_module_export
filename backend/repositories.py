from datetime import datetime
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

    def _get_data(
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

    def get_by_id(self, id_role, id_export, with_data=False, format=None):
        export = Export.query.get(id_export)
        if export:
            if with_data:
                # TODO: filters
                data = self._get_data(export.view_name, export.schema_name)
                try:
                    ExportLog.log(
                        id_export=export.id, format=format, id_user=id_role)
                except Exception as e:
                    DB.session.rollback()
                    logger.critical('%s', str(e))
                    return {'error': 'Echec de journalisation.'}

                return (export.as_dict(), data.get('items', None))
            else:
                return export.as_dict()
        else:
            raise NoResultFound('Unknown export id {}.'.format(id_export))

    def get_all(self, all=False):
        if not all:
            xs = Export.query.filter(Export.deleted.is_(None)).all()
        else:
            xs = Export.query.all()
        return xs

    def create(self, **kwargs):
        # TODO: (drop and re) create view
        # if not id_export and not view_name => creation
        #    create_and_populate_view(schema_def)
        # if id_export and view_name and schema_def? != export.schema_def
        #    drop_view(view_name)
        #    create_and_populate_view()

        x = Export(**kwargs)
        self.session.add(x)
        try:
            ExportLog.log(
                id_export=x.id, format='crea', id_user=x.id_creator)
        except Exception as e:
            DB.session.rollback()
            logger.warn('%s', str(e))
            raise e('Echec de journalisation.')
            # self.session.flush()  # session is flushed in ExportLog.log()
        return x

    def update(self, **kwargs):
        # TODO: drop/refresh view
        x = self.get_by_id(kwargs['id_export'])
        if x:
            x.__dict__.update((k, v) for k, v in kwargs.items() if k in x.__dict__)  # noqa E501
            try:
                ExportLog.log(
                    id_export=x.id, format='upda', id_user=kwargs['id_role'])
            except Exception as e:
                DB.session.rollback()
                logger.warn('%s', str(e))
                raise e('Echec de journalisation.')
            # self.session.flush()  # session is flushed in ExportLog.log()
            return x
        else:
            raise NoResultFound('Unknown export id {}'.format(kwargs['id_export']))  # noqa E501

    def delete(self, id_role, id_export):
        # TODO: drop view
        x = self.get_by_id(id_export)
        x.deleted = datetime.utcnow()
        try:
            ExportLog.log(
                id_export=x.id, format='dele', id_user=id_role)
        except Exception as e:
            DB.session.rollback()
            logger.critical('%s', str(e))
            raise e('Echec de journalisation.')
        # self.session.flush()  # session is flushed in ExportLog.log()
