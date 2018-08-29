import logging
from flask import current_app
# from geojson import FeatureCollection
from geonature.utils.utilssqlalchemy import GenericQuery

from .exportfilter import CompositeFilter


logger = current_app.logger
logger.setLevel(logging.DEBUG)


# TODO: override original build_query_filters()
# TODO: Timing data extraction
class ExportQuery(GenericQuery):
    def __init__(
            self,
            id_role,
            db_session,
            table_name,
            schema_name,
            geometry_field,
            filters,
            limit, offset=0):
        self.user = id_role

        super().__init__(
            db_session,
            table_name, schema_name, geometry_field,
            filters, limit, offset)

        logger.debug('User perm: %s', self.user)

    def build_query_filters(self, query, filters):
        return CompositeFilter.apply(None, query, filters=filters)

    def build_query_filter(self, query, param_name, param_value):
        return query
