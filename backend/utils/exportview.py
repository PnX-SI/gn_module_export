from sqlalchemy.schema import DDLElement
from sqlalchemy.ext.compiler import compiles
from flask import current_app

from geonature.utils.env import DB

logger = current_app.logger


# class CreateView(_CreateDropBase):
class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


@compiles(CreateView)
def visit_create_view(element, compiler, **kw):
    return "CREATE %s AS %s" % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True))


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(DropView)  # noqa
def visit_drop_view(element, compiler, **kw):
    return "DROP VIEW %s" % (element.name)


def View(name, metadata, selectable):
    CreateView(name, selectable).execute_at('after-create', metadata)
    DropView(name).execute_at('before-drop', metadata)
    logger.debug(selectable)
    t = DB.Table(name, metadata)
    return t
