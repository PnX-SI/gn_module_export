import logging
from flask import current_app
from geojson import FeatureCollection
from geonature.utils.utilssqlalchemy import GenericQuery

from .ExportFilterPolicy import DatasetActorFilterPolicy


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class AuthorizedExportQuery(GenericQuery):
    def __init__(
            self,
            info_role,
            db_session,
            tableName, schemaName, geometry_field,
            filters, limit, offset=0):
        self.user = info_role

        super().__init__(
            db_session,
            tableName, schemaName, geometry_field,
            filters, limit, offset)

        logger.debug('User perm: %s', self.user.tag_object_code)

    def return_query(self, policy=DatasetActorFilterPolicy):
        query = self.db_session.query(self.view.tableDef)
        nb_result_without_filter = query.count()

        if self.filters:
            query = self.build_query_filters(query, self.filters)
            query = self.build_query_order(query, self.filters)

        if policy:
            query = policy.apply(self, query)

        logger.debug('SQL query: %s', query)

        data = query.limit(self.limit).offset(self.offset * self.limit).all()
        nb_results = query.count()

        if self.geometry_field:
            results = FeatureCollection([
                self.view.as_geofeature(d)
                for d in data
                if getattr(d, self.geometry_field) is not None])
        else:
            results = [self.view.as_dict(d) for d in data]

        return {
            'total': nb_result_without_filter,
            'total_filtered': nb_results,
            'page': self.offset,
            'limit': self.limit,
            'items': results}
