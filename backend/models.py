
from geonature.utils.env import DB

from utils_flask_sqla.serializers import serializable

from pypnusershub.db.models import User


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
    id_licence = DB.Column(
        DB.Integer(), DB.ForeignKey(Licences.id_licence),
        primary_key=True, nullable=False
    )

    licence = DB.relationship(
        'Licences',
        primaryjoin='Export.id_licence==Licences.id_licence',
        backref='exports'
    )

    def __str__(self):
        return "{}".format(self.label)

    __repr__ = __str__


@serializable
class ExportLog(DB.Model):
    __tablename__ = 't_exports_logs'
    __table_args__ = {'schema': 'gn_exports'}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)  # noqa: A003
    id_role = DB.Column(DB.Integer, DB.ForeignKey(User.id_role))
    role = DB.relationship('User', foreign_keys=[id_role], lazy='joined')
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id))
    export = DB.relationship('Export', lazy='joined')
    format = DB.Column(DB.String(10), nullable=False)  # noqa: A003
    start_time = DB.Column(DB.DateTime, nullable=False)
    end_time = DB.Column(DB.DateTime)
    status = DB.Column(DB.Integer, default=-2)
    log = DB.Column(DB.Text)

    @classmethod
    def record(cls, adict):
        try:
            exportLog = cls()
            exportLog.from_dict(adict)
            DB.session.add(exportLog)
            DB.session.commit()
        except Exception as e:
            DB.session.rollback()
            # raise Exception('Echec de journalisation.')


class CorExportsRoles(DB.Model):
    __tablename__ = 'cor_exports_roles'
    __table_args__ = {'schema': 'gn_exports'}
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id),
                          primary_key=True, nullable=False)
    export = DB.relationship('Export', foreign_keys=[id_export], lazy='joined')
    id_role = DB.Column(DB.Integer, DB.ForeignKey(User.id_role),
                        primary_key=True, nullable=False)
    role = DB.relationship('User', foreign_keys=[id_role], lazy='joined')



class ExportSchedules(DB.Model):
    __tablename__ = 't_export_schedules'
    __table_args__ = {'schema': 'gn_exports'}
    id_export_schedule = DB.Column(DB.Integer, primary_key=True, nullable=False)
    frequency = DB.Column(DB.Integer(), nullable=False)
    format = DB.Column(DB.String(10), nullable=False)
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id))

    export = DB.relationship(
        'Export',
        primaryjoin='Export.id==ExportSchedules.id_export',
        backref='exports'
    )