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
    __table_args__ = {'schema': 'gn_exports'}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    # uid = DB.Column(DB.TIMESTAMP(timezone=False), nullable=False,
    #                 default=DB.func.now())
    id_role = DB.Column(DB.Integer(), DB.ForeignKey(TRoles.id_role))
    role = DB.relationship('TRoles', foreign_keys=[id_role], lazy='select')
    label = DB.Column(DB.Text, nullable=False, unique=True)
    selection = DB.Column(DB.Text, nullable=False)
    created = DB.Column(DB.DateTime)
    updated = DB.Column(DB.DateTime)

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
    __table_args__ = {'schema': 'gn_exports'}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    id_export = DB.Column(DB.Integer(),
                          DB.ForeignKey('gn_exports.t_exports.id'))
    export = DB.relationship('Export', lazy='joined')
    format = DB.Column(DB.Integer, nullable=False)
    ip_addr = DB.Column(DB.String(45))  # ipv4 -> ipv6
    id_user = DB.Column(DB.Integer(), DB.ForeignKey(TRoles.id_role))
    user = DB.relationship('TRoles', foreign_keys=[id_user], lazy='joined')
