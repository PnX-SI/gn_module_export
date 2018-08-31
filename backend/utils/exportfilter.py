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
}  # noqa: E133

FilterBooleanOpMap = {
    'OR': or_
}  # noqa: E133


def model_by_name(name):
    for m in DB._decl_class_registry.values():
        if hasattr(m, '__name__') and m.__name__ == name:
            return m


class Filter():
    # QUESTION: check_type: column type ?
    #  so (User.name, 'EQUALS', 5, (basestring,)) doesn't get through
    # TODO: PN like dict
    # rule_set = [
    #     ((User.name, 'EQUALS', new_person2.name), 'OR', (User.name, 'EQUALS', new_person1.name)),  # noqa: E501
    #     (User.name, 'CONTAINS', 'user%2'),
    #     ('Country.zone', 'EQUALS', 'Oceania'),
    # ]
    # q = session.query(User)
    # # print(Filter.apply(None, q, filter=('Address.user_id', 'EQUALS', 1)), end='\n' * 2)  # noqa: E501
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
        else:
            if (field.parent.class_ in [
                    m for m in DB._decl_class_registry.values()
                    if hasattr(m, '__name__')]):
                return field
            else:
                raise Exception('UnregisteredModel')

    @staticmethod
    def is_boolean(filter):
        return filter[1] in FilterBooleanOpMap

    @staticmethod
    def apply_boolean(context, query, filter):
        expr1, bool_op, expr2 = filter
        return query.filter(FilterBooleanOpMap[bool_op](
            *list([getattr(Filter.process(expr1_), FilterOpMap[relation])(expr2_)  # noqa: E501
                   for expr1_, relation, expr2_ in [expr1, expr2]])))


class CompositeFilter(Filter):
    @staticmethod
    def apply(context, query, filters=None):
        for f in filters:
            query = Filter.apply(context, query, f)
        return query
