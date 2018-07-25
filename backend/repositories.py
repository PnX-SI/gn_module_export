import logging
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from flask import current_app
from geojson import FeatureCollection
from geonature.utils.env import DB
from geonature.core.gn_meta.models import TDatasets
# from geonature.core.users.models import TRoles, UserRigth
from geonature.utils.utilssqlalchemy import GenericQuery

from .models import (Export, ExportLog)


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class UserMock(object):
    def __init__(self, id_role=1, tag_object_code=1):
        self.id_role = id_role
        self.tag_object_code = tag_object_code
        self.id_organisme = '-1'


class AuthorizedGenericQuery(GenericQuery):
    def __init__(
            self,
            db_session,
            tableName, schemaName, geometry_field,
            filters, limit=100, offset=0):
        self.user = UserMock(id_role=3, tag_object_code='2')
        super().__init__(
            db_session,
            tableName, schemaName, geometry_field,
            filters, limit=100, offset=0)

    def return_query(self):
        query = self.db_session.query(self.view.tableDef)
        nb_result_without_filter = query.count()

        # SINP: detId -> id_digitizer ?

        # if self.user.tag_object_code == '2':
        #     allowed_datasets = TDatasets.get_user_datasets(self.user)
        #     logger.debug('allowed datasets: %s', allowed_datasets)
        #     # logger.debug('dataset columns: %s', self.view.tableDef.columns)
        #     logger.debug('dataset columns contain id_dataset: %s', 'export_occtax.id_dataset' in self.view.tableDef.columns)  # noqa E501
        #     query = query.filter(
        #         or_(
        #             self.view.tableDef.columns.id_dataset.in_(tuple(allowed_datasets)),  # noqa E501
        #             self.view.tableDef.columns.observers.any(id_role=self.user.id_role),  # noqa E501
        #             self.view.tableDef.columns.id_digitiser == self.user.id_role  # noqa E501
        #         )
        #     )
        # elif self.user.tag_object_code == '1':
        #     query = query.filter(
        #         or_(
        #             self.view.tableDef.columns.observers.any(id_role=self.user.id_role),  # noqa E501
        #             self.view.tableDef.columns.id_digitiser == self.user.id_role  # noqa E501
        #         )
        #     )

        if self.filters:
            query = self.build_query_filters(query, self.filters)
            query = self.build_query_order(query, self.filters)

        data = query.limit(self.limit).offset(self.offset * self.limit).all()
        nb_results = query.count()

        if self.geometry_field:
            results = FeatureCollection(
                [
                    self.view.as_geofeature(d)
                    for d in data
                    if getattr(d, self.geometry_field) is not None
                ]
            )
        else:
            results = [self.view.as_dict(d) for d in data]

        return {
            'total': nb_result_without_filter,
            'total_filtered': nb_results,
            'page': self.offset,
            'limit': self.limit,
            'items': results
        }


class ExportRepository(object):
    def __init__(self, session=DB.session):
        self.session = session

    def _get_data(
            self, info_role, view, schema,
            geom_column_header=None, filters={}, limit=100000, paging=0):

        logger.debug('Querying "%s"."%s"', schema, view)

        columns = {}
        data = None

        query = AuthorizedGenericQuery(
            self.session, view, schema, geom_column_header,
            filters, limit, paging)

        columns = [col.name for col in query.view.db_cols]

        # if info_role.tag_object_code == '2':
        #     allowed_datasets = TDatasets.get_user_datasets(info_role)
        #     query = query.filter(
        #         or_(
        #             view.id_dataset.in_(tuple(allowed_datasets)),
        #             view.observers.any(id_role=info_role.id_role),
        #             view.id_digitiser == info_role.id_role
        #         )
        #     )
        # elif info_role.tag_object_code == '1':
        #     query = query.filter(
        #         or_(
        #             view.observers.any(id_role=info_role.id_role),
        #             view.id_digitiser == info_role.id_role
        #         )
        #     )

        data = query.return_query()

        # logger.debug('Query columns: %s', columns)
        # logger.debug('Query results: %s', data)
        return (columns, data)

    def get_by_id(
            self, info_role, id_export,
            with_data=False,
            geom_column_header=None,
            filters={},
            limit=10000,
            paging=0,
            format=None):
        export = Export.query.get(id_export)
        if export:
            if with_data and format:
                # TODO: filters
                # FIXME: find_geometry_columns
                # public.geometry_columns
                # geom_column_header = 'geom_4326'
                # srid = 4326

                columns, data = self._get_data(
                    info_role, export.view_name, export.schema_name,
                    geom_column_header=geom_column_header,
                    filters=filters,
                    limit=limit,
                    paging=paging)
                try:
                    ExportLog.log(
                        id_export=export.id, format=format,
                        id_user=info_role.id_role)
                except Exception as e:
                    logger.critical('%s', str(e))
                    return {'error': 'Echec de journalisation.'}

                return (export.as_dict(), columns, data)
            else:
                return export.as_dict()
        else:
            raise NoResultFound('Unknown export id {}.'.format(id_export))

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
            ExportLog.log(
                id_export=x.id, format='crea', id_user=x.id_creator)
        except IntegrityError as e:
            self.session.rollback()
            logger.warn('%s', str(e))
            raise e
        except Exception as e:
            logger.warn('%s', str(e))
            raise e
        return x

    def update(self, **kwargs):
        # TODO: drop and recreate/refresh view
        x = self.get_by_id(kwargs['id_export'])
        if x:
            try:
                x.__dict__.update(
                    (k, v) for k, v in kwargs.items() if k in x.__dict__)
                self.session.add(x)
                self.session.flush()
            except Exception as e:
                self.session.rollback()
                logger.warn('%s', str(e))
                raise e
            ExportLog.log(
                id_export=x.id, format='upda', id_user=kwargs['id_role'])
            return x
        else:
            raise NoResultFound(
                'Unknown export id {}'.format(kwargs['id_export']))

    def delete(self, id_role, id_export):
        # TODO: drop view
        x = self.get_by_id(id_export)
        x.deleted = datetime.utcnow()
        try:
            ExportLog.log(
                id_export=x.id, format='dele', id_user=id_role)
        except Exception as e:
            logger.critical('%s', str(e))
            raise e('Echec de journalisation.')
        # self.session.flush()  # session is flushed in ExportLog.log()
