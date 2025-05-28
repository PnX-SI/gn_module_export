"""ExportSchedules Ajout colonne in_process

Revision ID: 8db5a13cf0d2
Revises: 1db24d9b23bc
Create Date: 2025-05-27 17:19:25.837326

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8db5a13cf0d2"
down_revision = "1db24d9b23bc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "t_export_schedules",
        sa.Column("in_process", sa.Boolean, nullable=False, server_default=sa.false()),
        schema="gn_exports",
    )


def downgrade():
    op.drop_column("t_export_schedules", "in_process", schema="gn_exports")
