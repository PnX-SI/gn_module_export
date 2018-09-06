from geonature.utils.utilssqlalchemy import GenericQuery

from .filters import CompositeFilter


class ExportQuery(GenericQuery):
    def __init__(
            self,
            id_role,
            db_session,
            table_name,
            schema_name,
            geometry_field,
            filters,
            limit=100, offset=0):
        self.user = id_role

        super().__init__(
            db_session,
            table_name, schema_name, geometry_field,
            filters, limit=100, offset=0)

    def build_query_filters(self, query, filters):
        ctx = {'view': self.view}
        return CompositeFilter.apply(ctx, query, filters=filters)

    def build_query_filter(self, query, param_name, param_value):
        return query
