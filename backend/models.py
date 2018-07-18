# from datetime import datetime

from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import serializable
from geonature.core.users.models import TRoles


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
