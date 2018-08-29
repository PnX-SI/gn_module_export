from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import (serializable, geoserializable)
from geonature.core.users.models import TRoles


@geoserializable
@serializable
class Export(DB.Model):
    __tablename__ = 't_exports'
    __table_args__ = {'schema': 'gn_exports'}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    label = DB.Column(DB.Text, nullable=False, unique=True, index=True)
    schema_name = DB.Column(DB.Text, nullable=False)
    view_name = DB.Column(DB.Text, nullable=False)
    desc = DB.Column(DB.Text)
    geometry_field = DB.Column(DB.Text)
    geometry_srid = DB.Column(DB.Integer, default=4326)

    def __init__(self, label, schema_name, view_name, desc=None):
        self.label = label
        self.schema_name = schema_name
        self.view_name = view_name
        self.desc = desc

    def __str__(self):
        return "<Export(id='{}', label='{}')>".format(self.id, self.label)

    __repr__ = __str__


@serializable
class ExportLog(DB.Model):
    __tablename__ = 't_exports_logs'
    __table_args__ = {'schema': 'gn_exports'}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    id_role = DB.Column(DB.Integer, DB.ForeignKey(TRoles.id_role))
    role = DB.relationship('TRoles', foreign_keys=[id_role], lazy='joined')
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id))
    export = DB.relationship('Export', lazy='joined')
    format = DB.Column(DB.String(4), nullable=False)
    start_time = DB.Column(DB.DateTime, nullable=False)
    end_time = DB.Column(DB.DateTime)
    status = DB.Column(DB.Integer, default=-2)
    log = DB.Column(DB.Text)


class CorExportsRoles(DB.Model):
    __tablename__ = 'cor_exports_roles'
    __table_args__ = {'schema': 'gn_exports'}
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id),
                          primary_key=True, nullable=False)
    export = DB.relationship('Export', foreign_keys=[id_export], lazy='joined')
    id_role = DB.Column(DB.Integer, DB.ForeignKey(TRoles.id_role),
                        primary_key=True, nullable=False)
    role = DB.relationship('TRoles', foreign_keys=[id_role], lazy='joined')
