"""create export schema

Revision ID: 73d9d757b1e8
Revises: dde31e76ce45
Create Date: 2022-01-13 16:32:22.721296

"""
import importlib

from alembic import op 
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '73d9d757b1e8'
down_revision = None
branch_labels = ('gn_module_exports',)
depends_on =(
    'dde31e76ce45'  # GeoNature 2.9.0
)

def upgrade():
    conn = op.get_bind()
    conn.execute(text(importlib.resources.read_text('gn_module_export.migrations.data', 'exports.sql')))


def downgrade():
    op.execute("DROP SCHEMA gn_exports CASCADE") 
