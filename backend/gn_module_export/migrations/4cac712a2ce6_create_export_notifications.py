"""Create export notifications

Revision ID: 4cac712a2ce6
Revises: c2d02e345a06
Create Date: 2023-05-10 17:36:14.073847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4cac712a2ce6"
down_revision = "c2d02e345a06"
branch_labels = None
depends_on = ("09a637f06b96",)  # Geonature Notifications


CATEGORY_CODE = "EXPORT-DONE"
EMAIL_CONTENT = """
Bonjour,
{% if export_failed == true  %}
<p> Votre export  <i>{{ export.label }}</i> n'a pas fonctionné correctement.</p>
<p>Veuillez signaler le problème à l'administrateur du site.</p>
{% else %}
<p>
    Votre export <i>{{ export.label }}</i> est accessible via le lien suivant :
    <a href='{{ url }}'>Téléchargement</a>.
</p>
<p>
    Les données de cet export sont associées à la licence <a href='{{ export.licence.name_licence }}'>{{ export.licence.url_licence }}</a>.
    Merci de les utiliser en respectant cette licence.
</p>
<p>
    <b>Attention</b> : Ce fichier sera supprimé sous {{ nb_keep_day }} jours.
</p>
{% endif %}
"""

DB_CONTENT = """
{% if export_failed == true  %}
    <p> Votre export  <i>{{ export.label }}</i> n'a pas fonctionné correctement.</p>
    <p>Veuillez signaler le problème à l'administrateur du site.</p>
{% else %}
    <p>Votre export <i>{{ export.label }}</i> est accessible via le lien suivant :
    <a href='{{ url }}'>Téléchargement</a>.</p>
    <p><b>Attention</b> : Ce fichier sera supprimé sous {{ nb_keep_day }} jours.</p>
    <p>
        Les données de cet export sont associées à la licence <a href='{{ export.licence.name_licence }}'>{{ export.licence.url_licence }}</a>.
        Merci de les utiliser en respectant cette licence.
    </p>
{% endif %}
"""


def upgrade():
    bind = op.get_bind()
    metadata = sa.MetaData(bind=op.get_bind())
    notification_category = sa.Table(
        "bib_notifications_categories",
        metadata,
        autoload=True,
        schema="gn_notifications",
    )

    iterator = bind.execute(
        notification_category.insert(
            values={
                "code": CATEGORY_CODE,
                "label": "Fichier d'export généré",
                "description": "Se déclenche lorsque la génération d'un fichier d'export est terminée",
            }
        ).returning(notification_category.c.code)
    )
    result = next(iterator)

    notification_template = sa.Table(
        "bib_notifications_templates",
        metadata,
        autoload=True,
        schema="gn_notifications",
    )
    values = [
        {
            "code_category": result.code,
            "code_method": method,
            "content": content,
        }
        for method, content in (("EMAIL", EMAIL_CONTENT), ("DB", DB_CONTENT))
    ]

    bind.execute(notification_template.insert(values=values))
    op.execute(
        f"""
        INSERT INTO
            gn_notifications.t_notifications_rules (code_category, code_method)
        VALUES
            ('{CATEGORY_CODE}', 'DB'),
            ('{CATEGORY_CODE}', 'EMAIL')
        """
    )


def downgrade():
    bind = op.get_bind()
    metadata = sa.MetaData(bind=op.get_bind())
    notification_category = sa.Table(
        "bib_notifications_categories",
        metadata,
        autoload=True,
        schema="gn_notifications",
    )
    notification_template = sa.Table(
        "bib_notifications_templates",
        metadata,
        autoload=True,
        schema="gn_notifications",
    )
    notification_rules = sa.Table(
        "t_notifications_rules",
        metadata,
        autoload=True,
        schema="gn_notifications",
    )

    bind.execute(
        notification_rules.delete().where(notification_rules.c.code_category == CATEGORY_CODE)
    )
    bind.execute(
        notification_template.delete().where(
            notification_template.c.code_category == CATEGORY_CODE
        )
    )
    bind.execute(
        notification_category.delete().where(notification_category.c.code == CATEGORY_CODE)
    )
    op.execute(
        f"""
        DELETE FROM
            gn_notifications.t_notifications_rules
        WHERE
            code_category = '{CATEGORY_CODE}'
        AND
            id_role IS NULL
        """
    )
