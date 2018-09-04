# inspiration: https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Views
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
    # DOING: fix pg schema name in generated sql
    schema = None
    if hasattr(element.target, 'schema') and len(element.name.split('.')) == 0:
        schema = element.target.schema
    return "CREATE OR REPLACE VIEW %s AS (%s)" % (
        '.'.join([schema, element.name]) if schema else element.name,
        compiler.sql_compiler.process(element.selectable))


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(DropView)
def visit_drop_view(element, compiler, **kw):
    schema = None
    if hasattr(element.target, 'schema') and len(element.name.split('.')) == 0:
        schema = element.target.schema
    return "DROP VIEW IF EXISTS %s" % (
        '.'.join([schema, element.name]) if schema else element.name)


def View(name, metadata, selectable):
    t = DB.table(name)
    # https://docs.sqlalchemy.org/en/latest/core/selectable.html?highlight=table#sqlalchemy.sql.expression.TableClause  # noqa: E501
    # table(name, *columns) return is an instance of TableClause,
    # which represents the “syntactical” portion of the schema-level
    # Table object.
    for c in selectable.c:
        # https://bitbucket.org/zzzeek/sqlalchemy/src/081d4275cf5c3e6842c8e0198542ff89617eaa96/lib/sqlalchemy/sql/elements.py?at=master&fileviewer=file-view-default#elements.py-744  # noqa: E501
        c._make_proxy(t)
    if hasattr(metadata, 'schema') and len(name.split('.')) == 0:
        t.schema = metadata.schema
    CreateView(name, selectable).execute_at('after-create', metadata)
    DropView(name).execute_at('before-drop', metadata)
    # raise
    return t
