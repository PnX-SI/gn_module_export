import logging
from flask import current_app
# from geojson import FeatureCollection
from geonature.utils.utilssqlalchemy import GenericQuery

# from .exportfilter import CompositeFilter


logger = current_app.logger
logger.setLevel(logging.DEBUG)


# TODO: override original build_query_filters()
class ExportQuery(GenericQuery):
    def __init__(
            self,
            id_role,
            db_session,
            tableName, schemaName, geometry_field,
            filters, limit, offset=0):
        self.user = id_role

        super().__init__(
            db_session,
            tableName, schemaName, geometry_field,
            filters, limit, offset)

        logger.debug('User perm: %s', self.user)

    # def build_query_filters():
