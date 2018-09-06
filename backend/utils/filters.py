import logging
from flask import current_app
from sqlalchemy import or_
from geonature.utils.env import DB


logger = current_app.logger
logger.setLevel(logging.DEBUG)

# http://docs.sqlalchemy.org/en/latest/core/sqlelement.html?highlight=column%20operator#sqlalchemy.sql.operators.ColumnOperators
# map encoding to orm defined column operator names
FilterOpMap = {
    'EQUALS': '__eq__',
    'NOT_EQUALS': '__ne__',
    'GREATER_THAN': '__gt__',
    'LESS_THAN': '__lt__',
    'CONTAINS': 'contains',  # "%" and "_" -> wildcards in the condition.
}  # noqa: E133

FilterBooleanOpMap = {
    'OR': or_
}  # noqa: E133


def model_by_ns(ns):
    # 'name' | ['schema', 'name']
    if isinstance(ns, str):
        name = ns
    elif isinstance(ns, list):
        # TODO: resolve relation
        name = ns[-1]
    else:
        raise Exception(
            'model_by_ns(): unexpected param type: {} {}'.format(type(ns), ns))

    for m in DB.Model._decl_class_registry.values():
        if hasattr(m, '__name__') and m.__name__ == name:
            return m

    if logger.level == logging.DEBUG:
        raise Exception(
            'model_by_ns(): could not find model {}'.format(ns))


class Filter():
    # QUESTION: check column type so (User.name, 'EQUALS', 5, (basestring,)) doesn't get through  # noqa: E501
    # TODO: {rel: (field, cond), ...} cf @20cents
    #
    # rule_set = [
    #     ((User.name, 'EQUALS', new_person2.name), 'OR', (User.name, 'EQUALS', new_person1.name)),  # noqa: E501
    #     (User.name, 'CONTAINS', 'user%2'),
    #     ('Country.zone', 'EQUALS', 'Oceania'),
    # ]
    # q = session.query(User)
    # # print(Filter.apply(None, q, filter=('Address.user_id', 'EQUALS', 1)))
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
                return query.filter(filter)

    @staticmethod
    def process(context, field):
        # -> DB.Column[field]
        if isinstance(field, str):
            crumbs = field.split('.')
            depth = len(crumbs)
            view = context.get('view')
            if depth == 1:
                if view:
                    return getattr(view.tableDef.columns, field)
                else:
                    raise Exception(
                        'InvalidFilterContext: missing "view:name" key-value pair.')  # noqa: E501
            elif depth == 2:
                return getattr(model_by_ns(crumbs[0]), crumbs[1])
            elif depth > 2:
                return getattr(model_by_ns(crumbs[0:depth - 1]), crumbs[-1])
            else:
                raise Exception(
                    'InvalidFilterField: [schema.][entity.]attribute')
        else:
            if (field.parent.class_ in [
                    m for m in DB.Model._decl_class_registry.values()
                    if hasattr(m, '__name__')]):
                return field
            else:
                raise Exception('UnregisteredModel: {}'.format(str(field)))

    @staticmethod
    def is_boolean(filter):
        return filter[1] in FilterBooleanOpMap

    @staticmethod
    def apply_boolean(context, query, filter):
        expr_left, bool_op, expr_right = filter
        return query.filter(FilterBooleanOpMap[bool_op](
            *list([getattr(Filter.process(expr1_), FilterOpMap[relation])(expr2_)  # noqa: E501
                   for expr1_, relation, expr2_ in [expr_left, expr_right]])))


class CompositeFilter(Filter):
    @staticmethod
    def apply(context, query, filters=None):
        # context = {}
        # context['models'] = get_query_models(query)

        for f in filters:
            query = Filter.apply(context, query, f)
        return query
