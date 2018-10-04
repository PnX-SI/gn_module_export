# insp: https://github.com/Overseas-Student-Living/sqlalchemy-filters
import logging
from flask import current_app
from sqlalchemy import or_, types as sa_types
from geonature.utils.env import DB


logger = current_app.logger
logger.setLevel(logging.DEBUG)

# http://docs.sqlalchemy.org/en/latest/core/sqlelement.html?highlight=column%20operator#sqlalchemy.sql.operators.ColumnOperators
# map encoding to orm defin
ed column operator names

FilterOps = {
    'EQUALS': '__eq_ 'NOT_EQUALS': '__ne__',
    'GREATER_THAN': '__gt__',
    'GREATER_OR_EQUALS': '__ge__',
    'LESS_THAN': '__lt__',
    'CONTAINS': 'contains',  # "%" and "_" -> wildcards in the condition.
}  # noqa: E133
# in_(value.split(','))

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
        raise TypeError(
            'model_by_ns(): unexpected param type: "{}" "{}".'.format(
                type(ns), ns))

    for m in DB.Model._decl_class_registry.values():
        if hasattr(m, '__name__') and m.__name__ == name:
            return m

    if logger.level == logging.DEBUG:
        raise ValueError(
            'model_by_ns(): could not find model "{}".'.format(ns))


class Filter():
    # QUESTION: check column type so (User.name, 'EQUALS', 5, (basestring,)) doesn't get through  # noqa: E501
    # rule_set = [
    #     {
    #         'OR':
    #         [{
    #             'EQUALS':
    #             {
    #                 'field': 'User.name',
    #                 'condition': new_person2.name
    #             }
    #         }, {
    #             'EQUALS':
    #             {
    #                 'field': 'User.name',
    #                 'condition': new_person1.name
    #             }
    #         }]
    #     }, {
    #         'CONTAINS':
    #         {
    #             'field': 'User.name',
    #             'condition': 'user%2'
    #         }
    #     }, {
    #         'EQUALS':
    #         {
    #             'field': 'Country.zone',
    #             'condition': 'Oceania'
    #         }
    #     }
    # ]
    # q = session.query(User)
    # print(Filter.apply(None, q, filter={'EQUALS': {
    #     'field': 'Address.user_id', 'condition': 1}})
    # stmt = CompositeFilter.apply(None, q, filters=rule_set)
    # print(stmt)
    # assert stmt.all()[0] == new_person2
    @staticmethod
    def apply(context, query, filter=None):
        if filter:
            field, relation, condition = next(
                (v['field'], k, v['condition']) for k, v in filter.items())

            if Filter.is_boolean(filter):
                return Filter.apply_boolean(context, query, filter)

            else:
                field = Filter.process(context, field)

                filter = getattr(field, FilterOps[relation])(condition)
                return query.filter(filter)

    @staticmethod
    def process(context, field):  # -> DB.Column[field]
        # type_coerce() ?
        def dt_cast(column):
            if (isinstance(column, (
                    sa_types.DATETIME, sa_types.DATE,
                    sa_types.TIME, sa_types.TIMESTAMP))
                or any([
                    f in column.name
                    for f in {'heure', 'date', 'timestamp', 'time'}])):
                logger.debug(
                    'dt_cast: %s, %s', column.name, DB.func.date(column))
                return DB.func.date(column)
            else:
                return column

        if isinstance(field, str):
            crumbs = field.split('.')
            depth = len(crumbs)
            view = context.get('view')
            if depth == 1:
                if view:
                    return dt_cast(getattr(view.tableDef.columns, field))
                else:
                    raise Exception(
                        'InvalidFilterContext: missing "view:name" key-value pair.')  # noqa: E501
            elif depth == 2:
                return dt_cast(getattr(model_by_ns(crumbs[0]), crumbs[1]))
            elif depth > 2:
                return dt_cast(
                    getattr(model_by_ns(crumbs[0:depth - 1]), crumbs[-1]))
            else:
                raise Exception(
                    'InvalidFilterField: [schema.][entity.]attribute')
        else:
            if (field.parent.class_ in {
                    m for m in DB.Model._decl_class_registry.values()
                    if hasattr(m, '__name__')}):
                return dt_cast(field)
            else:
                raise Exception('UnregisteredModel: {}'.format(str(field)))

    @staticmethod
    def is_boolean(filter):
        return next(k for k, v in filter.items()) in FilterBooleanOpMap

    @staticmethod
    def apply_boolean(context, query, filter):
        left, op, right = next(
            (v['field'], k, v['condition']) for k, v in filter.items())
        return query.filter(FilterBooleanOpMap[op](
            *list([
                getattr(
                    Filter.process(subject), FilterOps[relation])(condition)
                for subject, relation, condition in [left, right]])))


class CompositeFilter(Filter):
    @staticmethod
    def apply(context, query, filters=None):
        # context = {}
        # context['models'] = get_query_models(query)

        for f in filters:
            query = Filter.apply(context, query, f)
        return query
