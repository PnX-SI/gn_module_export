import logging
from flask import current_app
from sqlalchemy import or_
from geonature.utils.env import DB

logger = current_app.logger
logger.setLevel(logging.DEBUG)

# map encoding to column operator names
# http://docs.sqlalchemy.org/en/latest/core/sqlelement.html?highlight=column%20operator#sqlalchemy.sql.operators.ColumnOperators
FilterOpMap = {
    'EQUALS': '__eq__',
    'NOT_EQUALS': '__ne__',
    'GREATER_THAN': '__gt__',
    'LESS_THAN': '__lt__',
    # "%" and "_" that are present inside the condition
    # will behave like wildcards as well.
    'CONTAINS': 'contains'
}

FilterBooleanOpMap = {
    'OR': or_
}


def model_by_name(name):
    for m in DB._decl_class_registry.values():
        if hasattr(m, '__name__') and m.__name__ == name:
            return m


class Filter():
    # rule_set = [
    #     ((User.name, 'EQUALS', new_person2.name), 'OR', (User.name, 'EQUALS', new_person1.name)),  # noqa E501
    #     (User.name, 'CONTAINS', 'user%2'),
    #     ('Country.zone', 'EQUALS', 'Oceania'),
    # ]
    # q = session.query(User)
    # # print(Filter.apply(None, q, filter=('Address.user_id', 'EQUALS', 1)), end='\n' * 2)  # noqa E501
    # stmt = CompositeFilter.apply(None, q, filters=rule_set)
    # print(stmt)
    # assert stmt.all()[0] == new_person2
    @staticmethod
    def apply(context, query, filter=None):
        if filter:
            field, relation, condition = filter

            if Filter.is_boolean(filter):
                return Filter.apply_boolean(context, query, filter)

            else:
                field = Filter.process(field)
                return query.filter(
                    getattr(field, FilterOpMap[relation])(condition))

    @staticmethod
    def process(field):
            if isinstance(field, str):
                _item = field.split('.')
                assert len(_item) == 2
                return getattr(model_by_name(_item[0]), _item[1])
            return field

    @staticmethod
    def is_boolean(filter):
        return filter[1] in FilterBooleanOpMap

    @staticmethod
    def apply_boolean(context, query, filter):
        expr1, bool_op, expr2 = filter
        return query.filter(FilterBooleanOpMap[bool_op](
            *list([getattr(Filter.process(expr1_), FilterOpMap[relation])(expr2_)  # noqa E501
                   for expr1_, relation, expr2_ in [expr1, expr2]])))


class CompositeFilter(Filter):
    @staticmethod
    def apply(context, query, filters=None):
        for f in filters:
            query = Filter.apply(context, query, f)
        return query


class DatasetActorFilterPolicy(CompositeFilter):
    ''' dataset actor data. '''

    @staticmethod
    def apply(context, query, filters=None):
        user = context.user
        if user.tag_object_code in ('1', '2', 'E'):
            columns = context.view.tableDef.columns
            column_names = [column.name for column in columns.values()]
            filters = []

            if ('id_dataset' in column_names and (user.tag_object_code in ('2', 'E'))):  # noqa E501
                from geonature.core.gn_meta.models import TDatasets
                allowed_datasets = TDatasets.get_user_datasets(user)
                if len(allowed_datasets) >= 1:
                    filters.append(columns.id_dataset.in_(tuple(allowed_datasets)))  # noqa E501
                # else:
                #     from pypnusershub.db.tools import InsufficientRightsError
                #     raise InsufficientRightsError
                logger.debug('Allowed datasets: %s', allowed_datasets)

            if 'observers' in column_names:
                filters.append(columns.observers.any(id_role=user.id_role))

            if 'id_digitiser' in column_names:
                filters.append(columns.id_digitiser == user.id_role)

            query = query.filter(or_(*filters))

        return query
