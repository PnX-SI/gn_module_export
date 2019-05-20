SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

BEGIN;
DROP SCHEMA IF EXISTS gn_exports CASCADE;
CREATE SCHEMA gn_exports;
COMMIT;

SET search_path = gn_exports, pg_catalog;

BEGIN;
CREATE TABLE gn_exports.t_exports
(
    id SERIAL NOT NULL PRIMARY KEY,
    label text COLLATE pg_catalog."default" NOT NULL,
    schema_name text COLLATE pg_catalog."default" NOT NULL,
    view_name text COLLATE pg_catalog."default" NOT NULL,
    "desc" text COLLATE pg_catalog."default",
    geometry_field character varying(255),
    geometry_srid INTEGER,
    public boolean NOT NULL default FALSE,
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
CREATE VIEW gn_exports.v_exports_logs AS
 SELECT r.nom_role ||' '||r.prenom_role AS utilisateur, e.label, l.format, l.start_time, l.end_time, l.status, l.log
 FROM gn_exports.t_exports_logs l
 JOIN utilisateurs.t_roles r ON r.id_role = l.id_role
 JOIN gn_exports.t_exports e ON e.id = l.id_export
 ORDER BY start_time;

COMMIT;

----------------------
-- Prepare Export RDF 
----------------------
--DROP VIEW gn_exports.v_exports_synthese;

CREATE OR REPLACE VIEW gn_exports.v_exports_synthese AS 

SELECT s.id_synthese AS "idSynthese",
       s.unique_id_sinp AS "permId", --ok
    s.unique_id_sinp_grp AS "permIdGrp", --ok
    s.count_min AS "denbrMin", --ok
    s.count_max AS "denbrMax", --ok
    s.meta_v_taxref AS "versionTAXREF", --ok
    --s.sample_number_proof AS "sampleNumb",
    --s.digital_proof AS "preuvNum",
    --s.non_digital_proof AS "preuvNoNum",
    s.altitude_min AS "altMin", --ok dc = minimumElevationInMeters
    s.altitude_max AS "altMax", --ok dc = maximumElevationInMeters 
    st_astext(s.the_geom_4326) AS "WKT", --ok
    s.date_min AS "date_min", --ok
    s.date_max AS "date_max", --ok
    --s.validator AS validateur,
    s.observers AS "obsId",
    -- organisme
    --s.id_digitiser,
    --s.determiner AS detminer,
    s.comment_context AS "obsCtx", --ok
    s.comment_description AS "obsDescr", --ok
    ref_nomenclatures.get_cd_nomenclature(s.id_nomenclature_obs_meth) AS "obsMeth",
    s.meta_create_date,
    s.meta_update_date,
    d.id_dataset AS "jddId",
    d.dataset_name AS "jddCode",
    d.id_acquisition_framework,
    t.cd_nom AS "cdNom", --ok
    t.cd_ref AS "cdRef", --ok
    t.nom_complet AS "scientificName ", -- cd = scientificName 
    s.nom_cite AS "nomCite" --ok
   FROM gn_synthese.synthese s
     JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
     JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
     JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source;