from flask import current_app, flash, Markup
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import is_form_submitted
from flask_admin.babel import gettext
from psycopg2.errors import ForeignKeyViolation
from sqlalchemy.exc import IntegrityError
from wtforms import validators


from geonature.core.admin.admin import admin as flask_admin, CruvedProtectedMixin
from geonature.utils.env import DB
from utils_flask_sqla_geo.generic import GenericQueryGeo

from gn_module_export.models import Export, ExportSchedules, Licences
from pypnusershub.db.models import User


class LicenceView(CruvedProtectedMixin, ModelView):
    """
    Surcharge de l'administration des licences
    """

    module_code = "EXPORTS"
    object_code = None

    def __init__(self, session, **kwargs):
        super(LicenceView, self).__init__(Licences, session, **kwargs)

    form_excluded_columns = "exports"
    column_labels = dict(
        name_licence="Nom de la licence", url_licence="URL de la licence"
    )
    column_descriptions = dict(
        name_licence="Nom de la licence",
        url_licence="URL de la documentation de la licence",
    )


def _token_formatter(view, context, model, name):
    _html = []
    for user in model.cor_roles_exports:
        _html.append(f"<b>{ user.role} </b> : {user.token}")
    return Markup("<br/>".join(_html))


class ExportView(CruvedProtectedMixin, ModelView):
    """
    Surcharge du formulaire d'administration Export
    """

    can_view_details = True

    module_code = "EXPORTS"
    object_code = None

    # Order column to have licence at the end
    column_list = [
        "id",
        "label",
        "schema_name",
        "view_name",
        "desc",
        "geometry_field",
        "geometry_srid",
        "public",
        "licence",
        "allowed_roles",
    ]

    column_details_list = [
        "id",
        "label",
        "schema_name",
        "view_name",
        "desc",
        "geometry_fields",
        "geometry_srid",
        "public",
        "licence",
        "cor_roles_exports",
    ]
    column_formatters_detail = {"cor_roles_exports": _token_formatter}

    column_labels = dict(
        id="Identifiant",
        label="Nom de l'export",
        schema_name="Nom du schema PostgreSQL",
        view_name="Nom de la vue SQL",
        view_pk_column="Nom de colonne d'unicité de la vue",
        desc="Description",
        geometry_field="Nom de champ géométrique",
        geometry_srid="SRID du champ géométrique",
        allowed_roles="Nom du role",
        cor_roles_exports="Role et token associé à l'export",
    )
    column_descriptions = dict(
        label="Nom libre de l'export",
        schema_name="Nom exact du schéma PostgreSQL contenant la vue SQL.",
        view_name="Nom exact de la vue SQL permettant l'export de vos données.",
        view_pk_column="Nom exact de la colonne d'unicité de la vue. Si non renseigné, la première colonne sera utilisée pour les exports.",
        desc="Décrit la nature de l'export",
        public="L'export est accessible à tous",
        allowed_roles="Role associé à l'export",
    )
    form_columns = (
        "label",
        "schema_name",
        "view_name",
        "view_pk_column",
        "desc",
        "geometry_field",
        "geometry_srid",
        "public",
        "licence",
        "allowed_roles",
    )
    form_args = {
        "allowed_roles": {
            "query_factory": lambda: User.query.order_by(
                User.groupe.desc(), User.nom_role
            ).filter((User.groupe == True) | (User.identifiant.isnot(None)))
        }
    }

    def __init__(self, session, **kwargs):
        # Référence au model utilisé
        super(ExportView, self).__init__(Export, session, **kwargs)

    def validate_form(self, form):
        """
        Validation personnalisée du form
        """
        # try to get the declared view in database
        view_name = getattr(form, "view_name", "")
        schema_name = getattr(form, "schema_name", "")
        geometry_field = getattr(form, "geometry_field", None)
        geometry_srid = getattr(form, "geometry_srid", None)
        view_pk_column = getattr(form, "view_pk_column", None)
        if is_form_submitted() and view_name and schema_name:
            try:
                if geometry_field.data and geometry_srid.data is None:
                    raise KeyError(
                        "Field Geometry SRID is mandatory with Geometry field"
                    )

                query = GenericQueryGeo(
                    DB,
                    view_name.data,
                    schema_name.data,
                    geometry_field=geometry_field.data,
                    filters=[],
                )
                columns = query.view.tableDef.columns.keys()
                # test if columns exists
                test_columns = (geometry_field.data, view_pk_column.data)
                for col in test_columns:
                    if col and col not in columns:
                        raise KeyError(f"Column {col} doesn't exists")

            except Exception as exp:
                flash(exp, category="error")
                return False

        return super(ExportView, self).validate_form(form)

    def handle_view_exception(self, exc):
        """
        Customisation du message d'erreur en cas de suppresion de l'export
        s'il est toujours référencé dans les tables de logs
        """
        if isinstance(exc, IntegrityError):
            if isinstance(exc.orig, ForeignKeyViolation):
                flash(
                    gettext(
                        "L'export ne peut pas être supprimé car il est toujours référencé (table de log)"
                    ),
                    "error",
                )
                return True

        return super(ModelView, self).handle_view_exception(exc)


class ExportSchedulesView(CruvedProtectedMixin, ModelView):
    """
    Surcharge de l'administration de l'export Schedules
    """

    module_code = "EXPORTS"
    object_code = None

    column_descriptions = dict(
        export="Nom de l'export à planifier",
        frequency="Fréquence de la génération de l'export (en jours)",
        format="Format de l'export à générer",
    )

    form_args = {
        "export": {"validators": [validators.DataRequired()]},
        "frequency": {"validators": [validators.NumberRange(1, 365)]},
    }

    if "EXPORTS" in current_app.config:
        format_list = [
            (k, k) for k in current_app.config["EXPORTS"]["export_format_map"].keys()
        ]
        form_choices = {"format": format_list}

    def __init__(self, session, **kwargs):
        super(ExportSchedulesView, self).__init__(ExportSchedules, session, **kwargs)


flask_admin.add_view(ExportView(DB.session, name="Exports", category="Export"))
flask_admin.add_view(LicenceView(DB.session, name="Licences", category="Export"))
flask_admin.add_view(
    ExportSchedulesView(DB.session, name="Planification des exports", category="Export")
)
