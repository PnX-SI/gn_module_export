"""create export schema

Revision ID: c2d02e345a06
Create Date: 2022-01-13 16:32:22.721296

"""
import importlib

from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = 'c2d02e345a06'
down_revision = None
branch_labels = ('exports',)
depends_on =(
    'dde31e76ce45'  # GeoNature 2.9.0
)

def upgrade():
    conn = op.get_bind()
    conn.execute(text(importlib.resources.read_text('gn_module_export.migrations.data', 'exports.sql')))


def downgrade():
    op.execute("DROP SCHEMA gn_exports CASCADE;")
