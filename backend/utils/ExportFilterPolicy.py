import logging
from enum import Enum
from flask import current_app
from sqlalchemy import or_, and_
from geonature.core.gn_meta.models import TDatasets
# from pypnusershub.db.tools import InsufficientRightsError
# from geonature.core.users.models import TRoles, UserRigth


logger = current_app.logger
logger.setLevel(logging.DEBUG)


class Operator(Enum):
    greater_than = '>'
    less_than = '<'
    equal_to = '=='
    not_equal_to = '!='


class AbstractFilterPolicy():
    @staticmethod
    def apply(context, query, filter):
        raise NotImplementedError


class AbstractCompositeFilter(AbstractFilterPolicy):
    @staticmethod
    def apply(context, query, filters):
        raise NotImplementedError


class OrCompositeFilter(AbstractCompositeFilter):
    @staticmethod
    def apply(context, query, filters):
        return query.filter(or_(*filters))


class AndCompositeFilter(AbstractCompositeFilter):
    @staticmethod
    def apply(context, query, filters):
        return query.filter(and_(*filters))


class DatasetActorFilterPolicy(AbstractFilterPolicy):
    ''' dataset actor can access its own data. '''

    @staticmethod
    def apply(context, query, filter=None):
        user = context.user
        if user.tag_object_code in ('1', '2', 'E'):
            columns = context.view.tableDef.columns
            column_names = [column.name for column in columns.values()]
            auth_filters = []

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

            CompositeFilter = OrCompositeFilter()
            query = CompositeFilter.apply(context, query, auth_filters)
            logger.debug('SQL query: %s', query)
            return query
