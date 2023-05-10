"""drop table gn_exports.t_exports_logs

Revision ID: bcee745e5647
Revises: c2d02e345a06
Create Date: 2023-05-10 10:43:45.661554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bcee745e5647"
down_revision = "c2d02e345a06"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    DROP VIEW gn_exports.v_exports_logs;
    DROP TABLE gn_exports.t_exports_logs;
    """
    )


def downgrade():
    op.execute(
        """
    CREATE TABLE gn_exports.t_exports_logs
    (
        id SERIAL NOT NULL PRIMARY KEY,
        id_role integer NOT NULL,
        id_export integer,
        format character varying(10) NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP,
        status numeric DEFAULT '-2'::integer,
        log text,
        CONSTRAINT fk_export FOREIGN KEY (id_export)
            REFERENCES gn_exports.t_exports (id) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION,
        CONSTRAINT fk_user FOREIGN KEY (id_role)
            REFERENCES utilisateurs.t_roles (id_role) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION
    );

    COMMENT ON TABLE gn_exports.t_exports_logs IS 'This table is used to log all the realised exports.';
    COMMENT ON COLUMN gn_exports.t_exports_logs.id_role IS 'Role who realize export';
    COMMENT ON COLUMN gn_exports.t_exports_logs.id_export IS 'Export type';
    COMMENT ON COLUMN gn_exports.t_exports_logs.format IS 'The exported format (csv, json, shp, geojson)';
    COMMENT ON COLUMN gn_exports.t_exports_logs.start_time IS 'When the export process start';
    COMMENT ON COLUMN gn_exports.t_exports_logs.end_time IS 'When the export process finish';
    COMMENT ON COLUMN gn_exports.t_exports_logs.status IS 'Status of the process : 1 ok: -2 error';
    COMMENT ON COLUMN gn_exports.t_exports_logs.log IS 'Holds export failure message';

    -- View to list Exports LOGS with users names and exports labels
    CREATE VIEW gn_exports.v_exports_logs AS
    SELECT r.nom_role ||' '||r.prenom_role AS utilisateur, e.label, l.format, l.start_time, l.end_time, l.status, l.log
    FROM gn_exports.t_exports_logs l
    JOIN utilisateurs.t_roles r ON r.id_role = l.id_role
    JOIN gn_exports.t_exports e ON e.id = l.id_export
    ORDER BY start_time;
    """
    )
