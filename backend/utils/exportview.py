import sqlalchemy
from sqlalchemy.schema import DDLElement  # _CreateDropBase
from sqlalchemy.ext.compiler import compiles

# current_app.config['SQLALCHEMY_ECHO'] = True


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable
        # super(CreateView, self).__init__(name, on=None, bind=None)


@compiles(CreateView)
def visit_create_view(element, compiler, **kw):
    return "CREATE OR REPLACE VIEW %s AS %s" % (
        element.name, compiler.sql_compiler.process(element.selectable))


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name
        # super(DropView, self).__init__(name, on=None, bind=None)


@compiles(DropView)  # noqa
def visit_drop_view(element, compiler, **kw):
    return "DROP VIEW %s" % (element.name)


def View(name, metadata, selectable):
    t = sqlalchemy.sql.table(name)

    for c in selectable.c:
        c._make_proxy(t)

    CreateView(name, selectable).execute_at('after-create', metadata)
    # DropView(name).execute_at('before-drop', metadata)
    return t
