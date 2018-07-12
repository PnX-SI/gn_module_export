# from datetime import datetime
from enum import IntEnum

from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import serializable
from geonature.core.users.models import TRoles


class Format(IntEnum):
    CSV = 1
    JSON = 2
    RDF = 4


format_map_ext = {
    Format.CSV: 'csv',
    Format.JSON: 'json',
    Format.RDF: 'rdf'
}

format_map_mime = {
    Format.CSV: 'text/csv',
    Format.JSON: 'application/json',
    Format.RDF: 'application/rdf+xml'
}


class Standard(IntEnum):
    NONE = 0
    SINP = 1
    DWC = 2
    ABCD = 4
    EML = 8


standard_map_label = {
    Standard.NONE: 'RAW',
    Standard.SINP: 'SINP',
    Standard.DWC: 'DarwinCore',
    Standard.ABCD: 'ABCD Schema',
    Standard.EML: 'EML'
}


@serializable
class Export(DB.Model):
    __tablename__ = 't_exports'
    __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    # uid = DB.Column(DB.TIMESTAMP(timezone=False), nullable=False,
    #                 default=DB.func.now())
    id_role = DB.Column(DB.Integer(), DB.ForeignKey(TRoles.id_role))
    role = DB.relationship('TRoles', foreign_keys=[id_role], lazy='select')
    label = DB.Column(DB.Text, nullable=False, unique=True)
    selection = DB.Column(DB.Text, nullable=False)
    start = DB.Column(DB.DateTime)
    end = DB.Column(DB.DateTime)
    status = DB.Column(DB.Numeric, default=-2)
    log = DB.Column(DB.Text)

    def __init__(self, id_role, label, selection):
        self.id_role = id_role
        self.label = label
        self.selection = selection

    # def __repr__(self):
    #     return "<Export(id='{}', label='{}', selection='{}', start='{}')>".format(  # noqa E501
    #         self.id, self.label, str(self.selection), self.start or '')


@serializable
class ExportLog(DB.Model):
    __tablename__ = 't_exports_logs'
    __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    id_export = DB.Column(DB.Integer(),
                          DB.ForeignKey('gn_exports.t_exports.id'))
    export = DB.relationship('Export', lazy='joined')
    format = DB.Column(DB.Integer, nullable=False)
    id_user = DB.Column(DB.Integer(), DB.ForeignKey(TRoles.id_role))
    user = DB.relationship('TRoles', foreign_keys=[id_user], lazy='joined')
    ip_addr = DB.Column(DB.String(45))  # ipv4 -> ipv6


import sqlalchemy
from sqlalchemy.schema import DDLElement
from sqlalchemy.ext.compiler import compiles


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(CreateView)
def compile(element, compiler, **kw):
    return "CREATE VIEW %s AS %s" % (element.name, compiler.sql_compiler.process(element.selectable))  # noqa E501


@compiles(DropView)  # noqa: W0404
def compile(element, compiler, **kw):
    return "DROP VIEW %s" % (element.name)


def view(name, metadata, selectable):
    t = sqlalchemy.sql.table(name)

    for c in selectable.c:
        c._make_proxy(t)

    CreateView(name, selectable).execute_at('after-create', metadata)
    DropView(name).execute_at('before-drop', metadata)
    return t


# metadata = DB.MetaData(schema='gn_exports', bind=DB.engine)
# stuff = DB.Table(
#     'stuff', metadata,
#     DB.Column('id', DB.Integer, primary_key=True),
#     DB.Column('data', DB.String(50)),
# )
#
# # more_stuff = DB.Table(
# #     'more_stuff', metadata,
# #     DB.Column('id', DB.Integer, primary_key=True),
# #     DB.Column('stuff_id', DB.Integer, DB.ForeignKey('gn_exports.stuff.id')),
# #     DB.Column('data', DB.String(50)),
# # )
#
# stuff_view = view(
#     'stuff_view', metadata,
#     sqlalchemy.sql.expression.select([
#         stuff.c.id,
#         stuff.c.data])  # , more_stuff.c.data.label('moredata')])
#     .select_from(stuff)
#     # .select_from(stuff.join(more_stuff))
#     # .where(stuff.c.data.like(sqlalchemy.text('"%orange%"')))
# )
#
# assert stuff_view.primary_key == [stuff_view.c.id]
# metadata.create_all()
#
# # stuff.insert().execute(
# #     {'data': 'apples'},
# #     {'data': 'pears'},
# #     {'data': 'oranges'},
# #     {'data': 'orange julius'},
# #     {'data': 'apple jacks'},
# # )
#
#
# class MyStuff(DB.Model):
#     __table__ = stuff_view
#     __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
#
#
# print('my stuff:', DB.session.query(MyStuff).all())
# metadata.drop_all()
