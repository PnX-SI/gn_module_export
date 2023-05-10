"""add token in gn_exports.cor_exports_roles

Revision ID: 75edd92560d7
Revises: c2d02e345a06
Create Date: 2023-05-10 10:28:04.138154

"""
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "75edd92560d7"
down_revision = "c2d02e345a06"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cor_exports_roles", sa.Column("token", sa.String()), schema="gn_exports"
    )

    op.execute(
        sa.text(
            """
            UPDATE gn_exports.cor_exports_roles
            SET token = :token
        """,
        ).bindparams(token=uuid.uuid4().hex)
    )
    op.alter_column("cor_exports_roles", "token", nullable=False, schema="gn_exports")


def downgrade():
    op.drop_column("cor_exports_roles", "token", schema="gn_exports")
