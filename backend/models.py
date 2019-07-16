from flask import current_app
from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import serializable
from pypnusershub.db.models import User
from sqlalchemy.orm import backref

@serializable
class Licences(DB.Model):
    __tablename__ = 't_licences'
    __table_args__ = {'schema': 'gn_exports'}

    id_licence = DB.Column(DB.Integer, primary_key=True, nullable=False)
    name_licence = DB.Column(DB.Text, nullable=False)
    url_licence = DB.Column(DB.Text, nullable=False)

    def __str__(self):
        return "{}".format(self.name_licence)

    __repr__ = __str__

@serializable
class Export(DB.Model):
    __tablename__ = 't_exports'
    __table_args__ = {'schema': 'gn_exports'}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)  # noqa: A003
    label = DB.Column(DB.Text, nullable=False, unique=True, index=True)
    schema_name = DB.Column(DB.Text, nullable=False)
    view_name = DB.Column(DB.Text, nullable=False)
    desc = DB.Column(DB.Text)
    geometry_field = DB.Column(DB.Text)
    geometry_srid = DB.Column(DB.Integer)
    public = DB.Column(DB.Boolean, nullable=False, default=False)
    id_licence = DB.Column(DB.Integer(), DB.ForeignKey(Licences.id_licence),
                        primary_key=True, nullable=False)

    licence = DB.relationship('Licences',  lazy='joined')

    def __str__(self):
        return "{}".format(self.label)

    __repr__ = __str__

    @classmethod
    def from_dict(cls, adict):
        export = Export(
            label=adict['label'],
            schema_name=adict['schema_name'],
            view_name=adict['view_name'],
            desc=adict['desc'],
            geometry_field=adict['geometry_field'],
            geometry_srid=adict['geometry_srid'],
            public=adict['public'])
        return export


@serializable
class ExportLog(DB.Model):
    __tablename__ = 't_exports_logs'
    __table_args__ = {'schema': 'gn_exports'}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)  # noqa: A003
    id_role = DB.Column(DB.Integer, DB.ForeignKey(User.id_role))
    role = DB.relationship('User', foreign_keys=[id_role], lazy='joined')
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id))
    export = DB.relationship('Export', lazy='joined')
    format = DB.Column(DB.String(4), nullable=False)  # noqa: A003
    start_time = DB.Column(DB.DateTime, nullable=False)
    end_time = DB.Column(DB.DateTime)
    status = DB.Column(DB.Integer, default=-2)
    log = DB.Column(DB.Text)

    def __init__(self, id_role, id_export, export_format, start_time, end_time,
                 status, log):
        self.id_role = id_role
        self.id_export = id_export
        self.format = export_format
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.log = log

    @classmethod
    def from_dict(cls, adict):
        export_log = ExportLog(
            id_role=adict['id_role'],
            id_export=adict['id_export'],
            export_format=adict['export_format'],
            start_time=adict['start_time'],
            end_time=adict['end_time'],
            status=adict['status'],
            log=adict['log'])
        return export_log

    @classmethod
    def record(cls, adict):
        try:
            x = ExportLog.from_dict(adict)
            DB.session.add(x)
            DB.session.commit()
        except Exception as e:
            DB.session.rollback()
            raise e('Echec de journalisation.')


class CorExportsRoles(DB.Model):
    __tablename__ = 'cor_exports_roles'
    __table_args__ = {'schema': 'gn_exports'}
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id),
                          primary_key=True, nullable=False)
    export = DB.relationship('Export', foreign_keys=[id_export], lazy='joined')
    id_role = DB.Column(DB.Integer, DB.ForeignKey(User.id_role),
                        primary_key=True, nullable=False)
    role = DB.relationship('User', foreign_keys=[id_role], lazy='joined')





