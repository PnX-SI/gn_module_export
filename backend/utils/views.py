# inspiration: https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Views
# sqlalchemy-views

from sqlalchemy.schema import DDLElement
from sqlalchemy.ext.compiler import compiles
from flask import current_app

from geonature.utils.env import DB

logger = current_app.logger


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


@compiles(CreateView)
def visit_create_view(element, compiler, **kw):
    schema, schema_dot_view = kw.get('schema', None), None
    if hasattr(element.target, 'schema') and element.target.schema:
        schema = element.target.schema
        schema_dot_view = '.'.join([schema, element.name])
    return 'CREATE OR REPLACE VIEW %s AS (%s)' % (
        schema_dot_view if schema else element.name,
        compiler.sql_compiler.process(element.selectable))


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(DropView)
def visit_drop_view(element, compiler, **kw):
    return "DROP VIEW IF EXISTS %s" % (element.name)  # CASCADE


def View(name, metadata, selectable):
    # https://docs.sqlalchemy.org/en/latest/core/selectable.html?highlight=table#sqlalchemy.sql.expression.TableClause  # noqa: E501
    # table(name, *columns) return is an instance of TableClause,
    # which represents the “syntactical” portion of the schema-level
    # Table object.
    t = DB.table(name)
    for c in selectable.c:
        c._make_proxy(t)
    if hasattr(metadata, 'schema') and not t.schema:
        t.schema = metadata.schema  # otherwise the view lands in 'public'.
    # FIXME: cp foreign_key_constraints -> constraints
    t.foreign_key_constraints = [c.copy()
                                 for c in t.columns
                                 if isinstance(c, DB.ForeignKeyConstraint)]
    t._extra_dependencies = None

    # DB.event.listen(
    #             metadata,
    #             "after_create",
    #             DB.DDL(CreateView)
    #         )
    # DB.event.listen(
    #     metadata,
    #     "before_drop",
    #     DB.DDL("DROP VIEW %s" % name)
    # )  # noqa: E133
    # FIXME: deprecated execute_at -> use DB.event
    CreateView(t.name, selectable).execute_at('after-create', metadata)
    DropView(t.name).execute_at('before-drop', metadata)
    return t
