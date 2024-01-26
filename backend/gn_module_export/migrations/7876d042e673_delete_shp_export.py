"""Delete shp export

Revision ID: 7876d042e673
Revises: fe1347f4805f
Create Date: 2023-05-26 18:43:43.816196

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7876d042e673"
down_revision = "fe1347f4805f"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    -- Transformation des shp en gpkg
    UPDATE gn_exports.t_export_schedules AS tes SET format = 'gpkg' WHERE format='shp';

    -- Cas où l'export gpkg et shp étaient tous les deux définis
    -- suppression d'un des deux doublons
    WITH d AS (
        SELECT min(id_export_schedule), id_export
        FROM gn_exports.t_export_schedules WHERE format=  'gpkg'
        GROUP BY id_export
        HAVING count(*)>1
    )
    DELETE FROM gn_exports.t_export_schedules e
    USING d
    WHERE format = 'gpkg' AND e.id_export = d.id_export AND NOT e.id_export_schedule = d.min ;
    """
    )


def downgrade():
    # Pas de retour possible sur les données
    pass
