from secrets import token_hex
from packaging import version

from flask import g
from sqlalchemy import or_
from sqlalchemy.orm import relationship
import flask_sqlalchemy

if version.parse(flask_sqlalchemy.__version__) >= version.parse("3"):
    from flask_sqlalchemy.query import Query
else:  # retro-compatibility Flask-SQLAlchemy 2 / SQLAlchemy 1.3
    from flask_sqlalchemy import BaseQuery as Query

from geonature.utils.env import DB
from utils_flask_sqla.serializers import serializable

from pypnusershub.db.models import User
from geonature.core.users.models import CorRole


class CorExportsRoles(DB.Model):
    __tablename__ = "cor_exports_roles"
    __table_args__ = {"schema": "gn_exports"}
    id_export = DB.Column(
        DB.Integer(),
        DB.ForeignKey("gn_exports.t_exports.id"),
        primary_key=True,
        nullable=False,
    )

    id_role = DB.Column(
        DB.Integer,
        DB.ForeignKey("utilisateurs.t_roles.id_role"),
        primary_key=True,
        nullable=False,
    )
    token = DB.Column(DB.String(80), nullable=False, default=token_hex(16))

    export = DB.relationship("Export", lazy="joined", cascade="all,delete")
    role = DB.relationship("UserRepr", lazy="joined")


class ExportsQuery(Query):
    def get_allowed_exports(self, user=None):
        """
        Liste des exports autorisés pour un role
        """
        if not user:
            user = g.current_user
        ors = [
            CorExportsRoles.id_role == user.id_role,
            CorExportsRoles.id_role.in_(
                User.query.with_entities(User.id_role)
                .join(CorRole, CorRole.id_role_groupe == User.id_role)
                .filter(CorRole.id_role_utilisateur == user.id_role)
            ),
            Export.public == True,
        ]
        self = self.outerjoin(CorExportsRoles).filter(or_(*ors))
        return self


class UserRepr(User):
    def __str__(self):
        if self.groupe:
            val = "Groupe : {}".format(self.nom_role)
        else:
            val = "{nom} {prenom} - ({email})".format(
                nom=self.nom_role,
                prenom=self.prenom_role or "",
                email=self.email or "no email",
            )
        return val


@serializable
class Licences(DB.Model):
    __tablename__ = "t_licences"
    __table_args__ = {"schema": "gn_exports"}

    id_licence = DB.Column(DB.Integer, primary_key=True, nullable=False)
    name_licence = DB.Column(DB.Text, nullable=False)
    url_licence = DB.Column(DB.Text, nullable=False)

    def __str__(self):
        return "{}".format(self.name_licence)

    __repr__ = __str__


@serializable
class Export(DB.Model):
    __tablename__ = "t_exports"
    __table_args__ = {"schema": "gn_exports"}
    query_class = ExportsQuery

    id = DB.Column(DB.Integer, primary_key=True, nullable=False)  # noqa: A003
    label = DB.Column(DB.Text, nullable=False, unique=True, index=True)
    schema_name = DB.Column(DB.Text, nullable=False)
    view_name = DB.Column(DB.Text, nullable=False)
    desc = DB.Column(DB.Text)
    geometry_field = DB.Column(DB.Text)
    geometry_srid = DB.Column(DB.Integer)
    public = DB.Column(DB.Boolean, nullable=False, default=False)
    id_licence = DB.Column(
        DB.Integer(), DB.ForeignKey(Licences.id_licence), nullable=False
    )
    allowed_roles = DB.relationship(UserRepr, secondary=CorExportsRoles.__table__)
    licence = DB.relationship("Licences")

    def __str__(self):
        return "{}".format(self.label)

    __repr__ = __str__


@serializable
class ExportLog(DB.Model):
    __tablename__ = "t_exports_logs"
    __table_args__ = {"schema": "gn_exports"}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)  # noqa: A003
    id_role = DB.Column(DB.Integer, DB.ForeignKey(User.id_role))
    role = DB.relationship("User", foreign_keys=[id_role], lazy="joined")
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id))
    export = DB.relationship("Export", lazy="joined")
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


class ExportSchedules(DB.Model):
    __tablename__ = "t_export_schedules"
    __table_args__ = {"schema": "gn_exports"}
    id_export_schedule = DB.Column(DB.Integer, primary_key=True, nullable=False)
    frequency = DB.Column(DB.Integer(), nullable=False)
    format = DB.Column(DB.String(10), nullable=False)
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id))

    export = DB.relationship("Export", lazy="subquery", cascade="all,delete")
