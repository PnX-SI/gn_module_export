from datetime import datetime
from geonature.utils.env import DB
from enum import IntEnum


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


class Role(DB.Model):
    __tablename__ = 'cor_role_export'
    __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
    id_cor_role_export = DB.Column(DB.Integer,
                                   primary_key=True, nullable=False)
    roles = DB.Column(DB.Text, nullable=False)


class ExportType(DB.Model):
    __tablename__ = 't_exports'
    __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    label = DB.Column(DB.Text, nullable=False)
    selection = DB.Column(DB.Text, nullable=False)


class Export(DB.Model):
    __tablename__ = 't_exports_logs'
    __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
    id = DB.Column(DB.TIMESTAMP(timezone=False),
                   primary_key=True, nullable=False)
    start = DB.Column(DB.DateTime)
    end = DB.Column(DB.DateTime)
    format = DB.Column(DB.Integer, nullable=False)
    status = DB.Column(DB.Numeric, default=-2)
    log = DB.Column(DB.UnicodeText)
    id_export = DB.Column(DB.Integer(),
                          DB.ForeignKey('gn_exports.t_exports.id'))
    type = DB.relationship('ExportType',
                           foreign_keys='Export.id_export',
                           backref=DB.backref('ExportType', lazy='dynamic'))
    id_role = DB.Column(
        DB.Integer(),
        DB.ForeignKey('gn_exports.cor_role_export.id_cor_role_export'))
    role = DB.relationship('Role', foreign_keys='Export.id_role',
                           backref=DB.backref('Role', lazy='dynamic'))

    def __init__(self, label, format):
        self.id = datetime.utcnow()
        self.format = int(format)
        self.type = ExportType.query.filter_by(label=label).first()

    def __repr__(self):
        return "<Export(id='{}', label='{}', selection='{}', date='{}', format='{}')>".format(  # noqa E501
            float(self.id), self.type.label, self.type.selection, self.start, self.format)  # noqa E501

    def as_dict(self):  # TODO: define de/serializer
        return {
            'id': float(self.ts()),
            'label': self.type.label,
            'extension': format_map_ext[self.format],
            'selection': self.type.selection,
            'date': self.start,
        }

    def ts(self):
        return (datetime.strptime(str(self.id), '%Y-%m-%d %H:%M:%S.%f')
                - datetime.utcfromtimestamp(0)).total_seconds()
