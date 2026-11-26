from pathlib import Path
from secrets import token_hex
from typing import Optional

import flask_sqlalchemy
from flask import g
from packaging import version
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, or_, false
import flask_sqlalchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

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
    id_export: Mapped[int] = mapped_column(
        Integer(),
        ForeignKey("gn_exports.t_exports.id"),
        primary_key=True,
    )

    id_role: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("utilisateurs.t_roles.id_role"),
        primary_key=True,
    )
    token: Mapped[str] = mapped_column(String(80), default=token_hex(16))

    export = relationship(
        "Export",
        lazy="joined",
        backref=backref("cor_roles_exports", cascade="all, delete-orphan"),
    )
    role = relationship(
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

    id_licence: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_licence: Mapped[str] = mapped_column(Text)
    url_licence: Mapped[str] = mapped_column(Text)

    def __str__(self):
        return "{}".format(self.name_licence)

    __repr__ = __str__


class Export(DB.Model):
    __tablename__ = "t_exports"
    __table_args__ = {"schema": "gn_exports"}
    query_class = ExportsQuery

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # noqa: A003
    label: Mapped[str] = mapped_column(Text, unique=True, index=True)
    schema_name: Mapped[str] = mapped_column(Text)
    view_name: Mapped[str] = mapped_column(Text)
    view_pk_column: Mapped[str] = mapped_column(Text)
    desc: Mapped[Optional[str]] = mapped_column(Text)
    geometry_field: Mapped[Optional[str]] = mapped_column(Text)
    geometry_srid: Mapped[Optional[int]] = mapped_column(Integer)
    public: Mapped[bool] = mapped_column(Boolean, default=False)
    id_licence: Mapped[int] = mapped_column(Integer(), ForeignKey(Licences.id_licence))
    licence = relationship("Licences")
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
        if not user:
            user = g.current_user
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

    def is_export_available(self, destination_format: str) -> bool:
        """
        Indicate if the export is available in a given format.

        An export is not available if the format requested is either a geojson (or a gpkg)
        and the SRID or the geometry field are not set in the export definition.

        Parameters
        ----------
        destination_format : str
            extension string (e.g. *.json*,*.gpkg*)

        Returns
        -------
        bool
            is the export available
        """
        if destination_format in ("geojson", "gpkg"):
            return self.geometry_field and self.geometry_srid
        return True


class ExportSchedules(DB.Model):
    __tablename__ = "t_export_schedules"
    __table_args__ = {"schema": "gn_exports"}
    id_export_schedule: Mapped[int] = mapped_column(Integer, primary_key=True)
    frequency: Mapped[int] = mapped_column(Integer())
    format: Mapped[str] = mapped_column(String(10))
    id_export: Mapped[Optional[int]] = mapped_column(Integer(), ForeignKey(Export.id))

    export = relationship("Export", lazy="subquery", cascade="all,delete")

    in_process: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    @property
    def skip_newer_than(self):
        return self.frequency * 24 * 60

    def is_export_available(self):
        return self.export.is_export_available(self.format)

    @property
    def __export_request_instance(self):
        # To avoid circular import
        from gn_module_export.utils_export import ExportRequest

        return ExportRequest(
            id_export=self.id_export,
            format=self.format,
        )

    def file_url_access(self) -> Path:
        return self.__export_request_instance.get_export_url()

    def filepath(self) -> Path:
        return Path(self.__export_request_instance.get_full_path_file_name())
