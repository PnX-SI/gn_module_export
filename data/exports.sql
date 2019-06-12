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


CREATE OR REPLACE VIEW gn_synthese.v_synthese_sinp AS
 WITH deco AS (
         SELECT s_1.id_synthese,
            n1.label_default AS "ObjGeoTyp",
            n2.label_default AS "methGrp",
            n3.label_default AS "obsMeth",
            n4.label_default AS "obsTech",
            n5.label_default AS "ocEtatBio",
            n6.label_default AS "ocStatBio",
            n7.label_default AS "ocNat",
            n8.label_default AS "preuveOui",
            n9.label_default AS "difNivPrec",
            n10.label_default AS "ocStade",
            n11.label_default AS "ocSex",
            n12.label_default AS "objDenbr",
            n13.label_default AS "denbrTyp",
            n14.label_default AS "sensiNiv",
            n15.label_default AS "statObs",
            n16.label_default AS "dEEFlou",
            n17.label_default AS "statSource",
            n18.label_default AS "typInfGeo",
            n19.label_default AS "ocMethDet"
           FROM gn_synthese.synthese s_1
             LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON s_1.id_nomenclature_geo_object_nature = n1.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON s_1.id_nomenclature_grp_typ = n2.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON s_1.id_nomenclature_obs_meth = n3.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON s_1.id_nomenclature_obs_technique = n4.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON s_1.id_nomenclature_bio_status = n5.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON s_1.id_nomenclature_bio_condition = n6.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n7 ON s_1.id_nomenclature_naturalness = n7.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n8 ON s_1.id_nomenclature_exist_proof = n8.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n9 ON s_1.id_nomenclature_diffusion_level = n9.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n10 ON s_1.id_nomenclature_life_stage = n10.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n11 ON s_1.id_nomenclature_sex = n11.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n12 ON s_1.id_nomenclature_obj_count = n12.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n13 ON s_1.id_nomenclature_type_count = n13.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n14 ON s_1.id_nomenclature_sensitivity = n14.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n15 ON s_1.id_nomenclature_observation_status = n15.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n16 ON s_1.id_nomenclature_blurring = n16.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n17 ON s_1.id_nomenclature_source_status = n17.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n18 ON s_1.id_nomenclature_info_geo_type = n18.id_nomenclature
             LEFT JOIN ref_nomenclatures.t_nomenclatures n19 ON s_1.id_nomenclature_determination_method = n19.id_nomenclature
        )
 SELECT s.id_synthese AS "idSynthese",
    s.unique_id_sinp AS "permId",
    s.unique_id_sinp_grp AS "permIdGrp",
    s.count_min AS "denbrMin",
    s.count_max AS "denbrMax",
    s.meta_v_taxref AS "vTAXREF",
    s.sample_number_proof AS "sampleNumb",
    s.digital_proof AS "preuvNum",
    s.non_digital_proof AS "preuvNoNum",
    s.altitude_min AS "altMin",
    s.altitude_max AS "altMax",
    s.the_geom_4326 AS geom,
    s.date_min AS "dateDebut",
    s.date_max AS "dateFin",
    s.validator AS validateur,
    s.observers AS observer,
    s.id_digitiser,
    s.determiner AS detminer,
    s.comment_context AS "obsCtx",
    s.comment_description AS "obsDescr",
    s.meta_create_date,
    s.meta_update_date,
    d.id_dataset AS "jddId",
    d.dataset_name AS "jddCode",
    d.id_acquisition_framework,
    t.cd_nom AS "cdNom",
    t.cd_ref AS "cdRef",
    s.nom_cite AS "nomCite",
    public.st_x(public.st_transform(s.the_geom_point, 2154)) AS x_centroid,
    public.st_y(public.st_transform(s.the_geom_point, 2154)) AS y_centroid,
    COALESCE(s.meta_update_date, s.meta_create_date) AS lastact,
    deco."ObjGeoTyp",
    deco."methGrp",
    deco."obsMeth",
    deco."obsTech",
    deco."ocEtatBio",
    deco."ocNat",
    deco."preuveOui",
    deco."difNivPrec",
    deco."ocStade",
    deco."ocSex",
    deco."objDenbr",
    deco."denbrTyp",
    deco."sensiNiv",
    deco."statObs",
    deco."dEEFlou",
    deco."statSource",
    deco."typInfGeo"
   FROM gn_synthese.synthese s
     JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
     JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
     JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
     JOIN deco ON deco.id_synthese = s.id_synthese;

INSERT INTO gn_exports.t_exports (label, schema_name, view_name, "desc", geometry_field, geometry_srid, public) VALUES ('Synthese SINP', 'gn_synthese', 'v_synthese_sinp', 'Export des données de la synthèse au standard SINP', 'geom', 4326, TRUE);