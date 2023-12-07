from secrets import token_hex

import flask_sqlalchemy
from flask import g
from packaging import version
from sqlalchemy import or_, false
import flask_sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship

if version.parse(flask_sqlalchemy.__version__) >= version.parse("3"):
    from flask_sqlalchemy.query import Query
else:  # retro-compatibility Flask-SQLAlchemy 2 / SQLAlchemy 1.3
    from flask_sqlalchemy import BaseQuery as Query

from datetime import timedelta

from geonature.core.users.models import CorRole
from geonature.utils.env import DB
from pypnusershub.db.models import User
from utils_flask_sqla_geo.generic import GenericQueryGeo


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

    export = DB.relationship(
        "Export",
        lazy="joined",
        backref=backref("cor_roles_exports", cascade="all, delete-orphan"),
    )
    role = DB.relationship(
        "User",
        lazy="joined",
    )


class ExportsQuery(Query):
    def filter_by_scope(self, scope, user=None):
        """
        Liste des exports autorisés pour un role
        """
        if not user:
            user = g.current_user
        if scope == 0:
            self = self.filter(false())
        elif scope in (1, 2):
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


class Licences(DB.Model):
    __tablename__ = "t_licences"
    __table_args__ = {"schema": "gn_exports"}

    id_licence = DB.Column(DB.Integer, primary_key=True, nullable=False)
    name_licence = DB.Column(DB.Text, nullable=False)
    url_licence = DB.Column(DB.Text, nullable=False)

    def __str__(self):
        return "{}".format(self.name_licence)

    __repr__ = __str__


class Export(DB.Model):
    __tablename__ = "t_exports"
    __table_args__ = {"schema": "gn_exports"}
    query_class = ExportsQuery

    id = DB.Column(DB.Integer, primary_key=True, nullable=False)  # noqa: A003
    label = DB.Column(DB.Text, nullable=False, unique=True, index=True)
    schema_name = DB.Column(DB.Text, nullable=False)
    view_name = DB.Column(DB.Text, nullable=False)
    view_pk_column = DB.Column(DB.Text, nullable=False)
    desc = DB.Column(DB.Text)
    geometry_field = DB.Column(DB.Text)
    geometry_srid = DB.Column(DB.Integer)
    public = DB.Column(DB.Boolean, nullable=False, default=False)
    id_licence = DB.Column(DB.Integer(), DB.ForeignKey(Licences.id_licence), nullable=False)
    licence = DB.relationship("Licences")
    allowed_roles = association_proxy(
        "cor_roles_exports",
        "role",
        creator=lambda role: CorExportsRoles(role=role),
    )
    # cor_role_token ajouter via une backref

    def __str__(self):
        return "{}".format(self.label)

    __repr__ = __str__

    def has_instance_permission(
        self,
        user=None,
        scope=None,
        token=None,
    ):
        if self.public:
            return True
        if token:
            return token in map(lambda cor: cor.token, self.cor_roles_exports)
        if not user.is_authenticated:  # no user provided and no user connected
            return False
        if scope == 3:
            return True
        if 0 < scope < 3:
            allowed_id_roles = list(map(lambda user: user.id_role, self.allowed_roles))
            ids_group_of_user = list(map(lambda group: group.id_role, user.groups))
            return user.id_role in allowed_id_roles or set(ids_group_of_user) & set(
                allowed_id_roles
            )
        return False

    def get_view_query(self, limit, offset, filters=None):
        return GenericQueryGeo(
            DB,
            self.view_name,
            self.schema_name,
            filters,
            limit,
            offset,
            self.geometry_field,
        )


class ExportSchedules(DB.Model):
    __tablename__ = "t_export_schedules"
    __table_args__ = {"schema": "gn_exports"}
    id_export_schedule = DB.Column(DB.Integer, primary_key=True, nullable=False)
    frequency = DB.Column(DB.Integer(), nullable=False)
    format = DB.Column(DB.String(10), nullable=False)
    id_export = DB.Column(DB.Integer(), DB.ForeignKey(Export.id))

    export = DB.relationship("Export", lazy="subquery", cascade="all,delete")

    @property
    def skip_newer_than(self):
        return self.frequency * 24 * 60
