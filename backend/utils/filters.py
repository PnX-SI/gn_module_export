import logging
from flask import current_app
from sqlalchemy import or_
from geonature.utils.env import DB


logger = current_app.logger
logger.setLevel(logging.DEBUG)

# http://docs.sqlalchemy.org/en/latest/core/sqlelement.html?highlight=column%20operator#sqlalchemy.sql.operators.ColumnOperators
# map encoding to column operator names
FilterOpMap = {
    'EQUALS': '__eq__',
    'NOT_EQUALS': '__ne__',
    'GREATER_THAN': '__gt__',
    'LESS_THAN': '__lt__',
    'CONTAINS': 'contains',  # "%" and "_" -> wildcards in the condition.
    # in_: Order.items.any(LineItem.product_name.in_(product_names))
}  # noqa: E133

FilterBooleanOpMap = {
    'OR': or_
}  # noqa: E133


def model_by_ns(ns):
    # 'name' | ['schema', 'name']
    if isinstance(ns, str):
        name = ns
    elif isinstance(ns, list):
        name = ns[-1]
    else:
        raise Exception(
            'model_by_ns(): unexpected param type: {} {}'.format(type(ns), ns))

    # find primary mapper ?
    for m in DB.Model._decl_class_registry.values():
        if hasattr(m, '__name__') and m.__name__ == name:
            return m

    if logger.level == logging.DEBUG:
        raise Exception(
            'model_by_ns(): could not find model {}'.format(ns))


class Filter():
    # QUESTION: check column type so (User.name, 'EQUALS', 5, (basestring,)) doesn't get through  # noqa: E501
    # TODO: PN like dict ... cf @20cents
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
                field = Filter.process(context, field)
                filter = getattr(field, FilterOpMap[relation])(condition)
                logger.debug('filter: %s', filter)
                return query.filter(filter)

    @staticmethod
    def process(context, field):
        # -> DB.Column/InstrumentedAttribute
        if isinstance(field, str):
            crumbs = field.split('.')
            depth = len(crumbs)
            if depth == 0:
                raise Exception('InvalidFilterField: [schema.]entity.attribute')  # noqa: E501
            elif depth == 1:
                view = context.get('view')
                return getattr(view.tableDef.columns, field)
            elif depth > 2:
                return getattr(model_by_ns(crumbs[0:depth - 1]), crumbs[-1])
            else:
                logger.debug('crumbs: %s', crumbs)
                # raise
                return getattr(model_by_ns(crumbs[0]), crumbs[1])
        else:
            if (field.parent.class_ in [
                    m for m in DB.Model._decl_class_registry.values()
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
        # context = {}
        # context['models'] = get_query_models(query)

        for f in filters:
            query = Filter.apply(context, query, f)
        return query
