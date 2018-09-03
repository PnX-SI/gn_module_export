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
    # return "CREATE VIEW gn_exports.%s AS (%s)" % (
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
    for c in selectable.c:
        c._make_proxy(t)
    CreateView(name, selectable).execute_at('after-create', metadata)
    DropView(name).execute_at('before-drop', metadata)
    return t
