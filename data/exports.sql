SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

CREATE SCHEMA IF NOT EXISTS gn_exports;

SET search_path = gn_exports, pg_catalog;

DROP TABLE IF EXISTS gn_exports.t_exports;
CREATE TABLE gn_exports.t_exports
(
    id SERIAL NOT NULL PRIMARY KEY,
    label text COLLATE pg_catalog."default" NOT NULL,
    schema_name text COLLATE pg_catalog."default" NOT NULL,
    view_name text COLLATE pg_catalog."default" NOT NULL,
    "desc" text COLLATE pg_catalog."default",
    geometry_field character varying(255),
    geometry_srid INTEGER,
    CONSTRAINT uniq_label UNIQUE (label)
);

COMMENT ON TABLE gn_exports.t_exports IS 'This table is used to declare views intended for export.';
COMMENT ON COLUMN gn_exports.t_exports.id IS 'Internal value for primary keys';
COMMENT ON COLUMN gn_exports.t_exports.schema_name IS 'Schema name where the view is stored';
COMMENT ON COLUMN gn_exports.t_exports.view_name IS 'The view name';
COMMENT ON COLUMN gn_exports.t_exports.label IS 'Export name to display';
COMMENT ON COLUMN gn_exports.t_exports."desc" IS 'Short or long text to explain the export and/or is content';
COMMENT ON COLUMN gn_exports.t_exports.geometry_field IS 'Name of the geometry field if the export is spatial';
COMMENT ON COLUMN gn_exports.t_exports.geometry_srid IS 'SRID of the geometry';


DROP TABLE IF EXISTS gn_exports.cor_exports_roles;
CREATE TABLE gn_exports.cor_exports_roles (
    id_export integer NOT NULL,
    id_role integer NOT NULL
);
ALTER TABLE ONLY gn_exports.cor_exports_roles
    ADD CONSTRAINT cor_exports_roles_pkey PRIMARY KEY (id_export, id_role);

ALTER TABLE ONLY gn_exports.cor_exports_roles
    ADD CONSTRAINT fk_cor_exports_roles_id_export FOREIGN KEY (id_export) REFERENCES gn_exports.t_exports(id);

ALTER TABLE ONLY gn_exports.cor_exports_roles
    ADD CONSTRAINT fk_cor_exports_roles_id_role FOREIGN KEY (id_role) REFERENCES utilisateurs.t_roles(id_role) ON UPDATE CASCADE;


DROP TABLE IF EXISTS gn_exports.t_exports_logs;
CREATE TABLE gn_exports.t_exports_logs
(
    id SERIAL NOT NULL PRIMARY KEY,
    id_role integer NOT NULL,
    id_export integer,
    format character varying(4) COLLATE pg_catalog."default" NOT NULL,
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

-- Create a view to list Exports LOGS with users names and exports labels
CREATE OR REPLACE VIEW gn_exports.v_exports_logs AS
 SELECT r.nom_role ||' '||r.prenom_role AS utilisateur, e.label, l.format, l.start_time, l.end_time, l.status, l.log
 FROM gn_exports.t_exports_logs l
 JOIN utilisateurs.t_roles r ON r.id_role = l.id_role
 JOIN gn_exports.t_exports e ON e.id = l.id_export
 ORDER BY start_time
