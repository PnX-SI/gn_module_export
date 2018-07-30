import logging
from flask import current_app
from sqlalchemy import or_, and_
from geonature.core.gn_meta.models import TDatasets
# from pypnusershub.db.tools import InsufficientRightsError
# from geonature.core.users.models import TRoles, UserRigth


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class AbstractFilterPolicy():
    def __init__(self, container):
        self.container = container

    def apply(self, query):
        raise NotImplementedError


class AbstractCompositeFilter(AbstractFilterPolicy):
    def apply(self, query, *filters):
        raise NotImplementedError


class OrCompositeFilter(AbstractCompositeFilter):
    def apply(self, query, *filters):
        return query.filter(or_(*filters))


class AndCompositeFilter(AbstractCompositeFilter):
    def apply(self, query, *filters):
        return query.filter(and_(*filters))


class DatasetActorFilterPolicy(AbstractFilterPolicy):
    ''' dataset actor should be able to access its own data. '''

    def apply(self, query):
        columns = self.container.view.tableDef.columns
        column_names = [column.name for column in columns.values()]
        user = self.container.user
        auth_filters = []
        if user.tag_object_code in ('1', '2', 'E'):
            if ('id_dataset' in column_names and (user.tag_object_code in ('2', 'E'))):  # noqa E501
                allowed_datasets = TDatasets.get_user_datasets(user)
                if len(allowed_datasets) >= 1:
                    auth_filters.append(columns.id_dataset.in_(tuple(allowed_datasets)))  # noqa E501
                # else:
                #     raise InsufficientRightsError
                logger.debug('Allowed datasets: %s', allowed_datasets)

            if 'observers' in column_names:
                auth_filters.append(
                    columns.observers.any(id_role=user.id_role))

            if 'id_digitiser' in column_names:
                auth_filters.append(columns.id_digitiser == user.id_role)

            CompositeFilter = OrCompositeFilter(self)
            query = CompositeFilter.apply(query, *auth_filters)
            logger.debug('SQL query: %s', query)
            return query
