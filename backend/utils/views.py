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
    # raise
    return "CREATE OR REPLACE VIEW gn_exports.%s AS (%s)" % (
        element.name,
        compiler.sql_compiler.process(element.selectable))


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(DropView)
def visit_drop_view(element, compiler, **kw):
    return "DROP VIEW IF EXISTS gn_exports.%s" % (element.name)


def View(name, metadata, selectable):
    t = DB.table(name)
    # https://docs.sqlalchemy.org/en/latest/core/selectable.html?highlight=table#sqlalchemy.sql.expression.TableClause  # noqa: E501
    # table(name, *columns) return is an instance of TableClause,
    # which represents the “syntactical” portion of
    # the schema-level Table object.
    for c in selectable.c:
        # https://bitbucket.org/zzzeek/sqlalchemy/src/081d4275cf5c3e6842c8e0198542ff89617eaa96/lib/sqlalchemy/sql/elements.py?at=master&fileviewer=file-view-default#elements.py-744  # noqa: E501
        c._make_proxy(t)
    CreateView(name, selectable).execute_at('after-create', metadata)
    DropView(name).execute_at('before-drop', metadata)
    return t
