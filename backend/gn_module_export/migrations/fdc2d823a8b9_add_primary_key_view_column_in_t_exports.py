"""Add primary key view column in t_exports

Revision ID: fdc2d823a8b9
Revises: c2d02e345a06
Create Date: 2023-05-11 17:33:00.460204

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fdc2d823a8b9"
down_revision = "4cac712a2ce6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "t_exports",
        sa.Column("view_pk_column", sa.Unicode, server_default=None),
        schema="gn_exports",
    )
    op.execute(
        """
        UPDATE gn_exports.t_exports SET view_pk_column='id_synthese'
        WHERE label = 'Synthese SINP';
    """
    )


def downgrade():
    op.drop_column("t_exports", "view_pk_column", schema="gn_exports")
