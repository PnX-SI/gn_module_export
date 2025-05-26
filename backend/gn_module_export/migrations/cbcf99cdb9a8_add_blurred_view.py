"""Add blurred view

Revision ID: cbcf99cdb9a8
Revises: 1db24d9b23bc
Create Date: 2025-04-23 17:22:36.362008

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cbcf99cdb9a8"
down_revision = "1db24d9b23bc"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE MATERIALIZED VIEW gn_exports.vm_synthese_blurred
        TABLESPACE pg_default
        AS
            SELECT DISTINCT ON (s.id_synthese, areas.id_type) s.id_synthese,
                areas.geom_4326 AS geom
            FROM gn_synthese.synthese s
                JOIN ref_nomenclatures.t_nomenclatures sensi ON sensi.id_nomenclature = s.id_nomenclature_sensitivity
                JOIN gn_synthese.cor_area_synthese cor ON cor.id_synthese = s.id_synthese
                JOIN ref_geo.l_areas areas ON cor.id_area = areas.id_area
                JOIN gn_sensitivity.cor_sensitivity_area_type csat ON csat.id_nomenclature_sensitivity = sensi.id_nomenclature AND csat.id_area_type = areas.id_type
        WITH DATA;
    """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp_blurred
        AS WITH jdd_acteurs AS (
            SELECT d_1.id_dataset,
                string_agg(DISTINCT concat(COALESCE(orga.nom_organisme, ((roles.nom_role::text || ' '::text) || roles.prenom_role::text)::character varying), ' (', nomencl.label_default, ')'), ', '::text) AS acteurs
            FROM gn_meta.t_datasets d_1
                JOIN gn_meta.cor_dataset_actor act ON act.id_dataset = d_1.id_dataset
                JOIN ref_nomenclatures.t_nomenclatures nomencl ON nomencl.id_nomenclature = act.id_nomenclature_actor_role
                LEFT JOIN utilisateurs.bib_organismes orga ON orga.id_organisme = act.id_organism
                LEFT JOIN utilisateurs.t_roles roles ON roles.id_role = act.id_role
            GROUP BY d_1.id_dataset
        )
        SELECT s.id_synthese,
            s.entity_source_pk_value AS id_source,
            s.unique_id_sinp AS id_perm_sinp,
            s.unique_id_sinp_grp AS id_perm_grp_sinp,
            s.date_min AS date_debut,
            s.date_max AS date_fin,
            t.cd_nom,
            t.cd_ref,
            s.meta_v_taxref AS version_taxref,
            s.nom_cite,
            t.nom_vern,
            t.nom_valide,
            t.regne,
            t.group1_inpn,
            t.group2_inpn,
            t.classe,
            t.ordre,
            t.famille,
            t.id_rang AS rang_taxo,
            s.count_min AS nombre_min,
            s.count_max AS nombre_max,
            s.altitude_min,
            s.altitude_max,
            s.depth_min AS profondeur_min,
            s.depth_max AS profondeur_max,
            s.observers AS observateurs,
            s.determiner AS determinateur,
            s.validator AS validateur,
            s.sample_number_proof AS numero_preuve,
            s.digital_proof AS preuve_numerique,
            s.non_digital_proof AS preuve_non_numerique,
            CASE
                WHEN blur.geom IS NOT NULL THEN blur.geom
                ELSE s.the_geom_4326
            END
            AS geom_4326,
            s.comment_context AS comment_releve,
            s.comment_description AS comment_occurrence,
            s.meta_create_date AS date_creation,
            s.meta_update_date AS date_modification,
            COALESCE(s.meta_update_date, s.meta_create_date) AS derniere_action,
            d.unique_dataset_id AS jdd_uuid,
            d.dataset_name AS jdd_nom,
            jdd_acteurs.acteurs AS jdd_acteurs,
            af.unique_acquisition_framework_id AS ca_uuid,
            af.acquisition_framework_name AS ca_nom,
            s.reference_biblio,
            s.cd_hab AS code_habitat,
            h.lb_hab_fr AS habitat,
            s.place_name AS nom_lieu,
            s."precision",
            s.additional_data::text AS donnees_additionnelles,
            n1.label_default AS nature_objet_geo,
            n2.label_default AS type_regroupement,
            s.grp_method AS methode_regroupement,
            n3.label_default AS comportement,
            n4.label_default AS technique_obs,
            n5.label_default AS statut_biologique,
            n6.label_default AS etat_biologique,
            n7.label_default AS naturalite,
            n8.label_default AS preuve_existante,
            n9.label_default AS precision_diffusion,
            n10.label_default AS stade_vie,
            n11.label_default AS sexe,
            n12.label_default AS objet_denombrement,
            n13.label_default AS type_denombrement,
            n14.label_default AS niveau_sensibilite,
            n15.label_default AS statut_observation,
            n16.label_default AS floutage_dee,
            n17.label_default AS statut_source,
            n18.label_default AS type_info_geo,
            n19.label_default AS methode_determination
        FROM gn_synthese.synthese s
            LEFT JOIN gn_exports.vm_synthese_blurred blur ON blur.id_synthese = s.id_synthese
            JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
            JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
            JOIN jdd_acteurs ON jdd_acteurs.id_dataset = s.id_dataset
            JOIN gn_meta.t_acquisition_frameworks af ON d.id_acquisition_framework = af.id_acquisition_framework
            JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
            LEFT JOIN ref_habitats.habref h ON h.cd_hab = s.cd_hab
            LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON s.id_nomenclature_geo_object_nature = n1.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON s.id_nomenclature_grp_typ = n2.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON s.id_nomenclature_behaviour = n3.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON s.id_nomenclature_obs_technique = n4.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON s.id_nomenclature_bio_status = n5.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON s.id_nomenclature_bio_condition = n6.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n7 ON s.id_nomenclature_naturalness = n7.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n8 ON s.id_nomenclature_exist_proof = n8.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n9 ON s.id_nomenclature_diffusion_level = n9.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n10 ON s.id_nomenclature_life_stage = n10.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n11 ON s.id_nomenclature_sex = n11.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n12 ON s.id_nomenclature_obj_count = n12.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n13 ON s.id_nomenclature_type_count = n13.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n14 ON s.id_nomenclature_sensitivity = n14.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n15 ON s.id_nomenclature_observation_status = n15.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n16 ON s.id_nomenclature_blurring = n16.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n17 ON s.id_nomenclature_source_status = n17.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n18 ON s.id_nomenclature_info_geo_type = n18.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n19 ON s.id_nomenclature_determination_method = n19.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures dl ON s.id_nomenclature_diffusion_level = dl.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures st ON s.id_nomenclature_observation_status = st.id_nomenclature
        WHERE st.cd_nomenclature::text = 'Pr'::text AND (EXISTS ( SELECT cda.id_dataset
                FROM gn_meta.cor_dataset_actor cda
            WHERE cda.id_dataset = s.id_dataset AND cda.id_organism = 2));

    """
    )
    op.execute(
        """
            CREATE FUNCTION gn_profiles.refresh_blurred_geoms() RETURNS void
                LANGUAGE plpgsql
                AS $$
                -- Rafraichissement des vues matérialisées des geométrie floutée
                -- USAGE : SELECT gn_profiles.refresh_blurred_geoms()
                BEGIN
                    REFRESH MATERIALIZED VIEW CONCURRENTLY gn_exports.vm_synthese_blurred;
                END
            $$;

        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp_blurred_test AS 
        WITH actors AS (
            SELECT td.id_dataset,
                td.id_acquisition_framework,
                td.unique_dataset_id,
                td.dataset_name,
                td.id_nomenclature_data_origin,
                string_agg(DISTINCT bo.nom_organisme::text, ' | '::text) AS organisms_list
            FROM gn_meta.t_datasets AS td
                LEFT JOIN gn_meta.cor_dataset_actor AS cda
                    ON (
                        cda.id_dataset = td.id_dataset
                        AND cda.id_nomenclature_actor_role = ref_nomenclatures.get_id_nomenclature('ROLE_ACTEUR', '1')
                    )
                LEFT JOIN utilisateurs.bib_organismes AS bo
                    ON bo.id_organisme = cda.id_organism
            GROUP BY td.id_dataset
        ),
        areas AS (
            SELECT bat.id_type,
                bat.type_code,
                bat.ref_version,
                la.id_area,
                la.area_code,
                la.area_name
            FROM ref_geo.bib_areas_types AS bat
                JOIN ref_geo.l_areas AS la ON bat.id_type = la.id_type
            WHERE bat.type_code::text = ANY (ARRAY['DEP'::character varying, 'COM'::character varying, 'M10'::character varying]::text[])
        )
        SELECT s.id_synthese AS "ID_synthese",
            s.entity_source_pk_value AS id_source,
            s.unique_id_sinp AS id_perm_sinp,
            s.unique_id_sinp_grp AS id_perm_grp_sinp,
            s.date_min AS date_debut,
            s.date_max AS date_fin,
            t.cd_nom,
            t.cd_ref,
            s.meta_v_taxref AS version_taxref,
            s.nom_cite,
            t.nom_vern,
            t.nom_valide,
            t.regne,
            t.group1_inpn,
            t.group2_inpn,
            t.classe,
            t.ordre,
            t.famille,
            t.id_rang AS rang_taxo,
            s.count_min AS nombre_min,
            s.count_max AS nombre_max,
            s.altitude_min,
            s.altitude_max,
            s.depth_min AS profondeur_min,
            s.depth_max AS profondeur_max,
            s.observers AS observateurs,
            s.determiner AS determinateur,
            s.validator AS validateur,
            s.sample_number_proof AS numero_preuve,
            s.digital_proof AS preuve_numerique,
            s.non_digital_proof AS preuve_non_numerique,
            CASE
                WHEN blur.geom IS NOT NULL THEN blur.geom
                ELSE s.the_geom_4326
            END
            AS geom_4326,
            s.comment_context AS comment_releve,
            s.comment_description AS comment_occurrence,
            s.meta_create_date AS date_creation,
            s.meta_update_date AS date_modification,
            COALESCE(s.meta_update_date, s.meta_create_date) AS derniere_action,
            d.unique_dataset_id AS jdd_uuid,
            d.dataset_name AS jdd_nom,
            jdd_acteurs.acteurs AS jdd_acteurs,
            af.unique_acquisition_framework_id AS ca_uuid,
            af.acquisition_framework_name AS ca_nom,
            s.reference_biblio,
            s.cd_hab AS code_habitat,
            h.lb_hab_fr AS habitat,
            s.place_name AS nom_lieu,
            s."precision",
            s.additional_data::text AS donnees_additionnelles,
            n1.label_default AS nature_objet_geo,
            n2.label_default AS type_regroupement,
            s.grp_method AS methode_regroupement,
            n3.label_default AS comportement,
            n4.label_default AS technique_obs,
            n5.label_default AS statut_biologique,
            n6.label_default AS etat_biologique,
            n7.label_default AS naturalite,
            n8.label_default AS preuve_existante,
            n9.label_default AS precision_diffusion,
            n10.label_default AS stade_vie,
            n11.label_default AS sexe,
            n12.label_default AS objet_denombrement,
            n13.label_default AS type_denombrement,
            n14.label_default AS niveau_sensibilite,
            n15.label_default AS statut_observation,
            n16.label_default AS floutage_dee,
            n17.label_default AS statut_source,
            n18.label_default AS type_info_geo,
            n19.label_default AS methode_determination
        FROM gn_synthese.synthese s
            LEFT JOIN gn_exports.vm_synthese_blurred blur ON blur.id_synthese = s.id_synthese
            JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
            LEFT JOIN LATERAL (
                SELECT
                    d.id_synthese,
                    json_object_agg(d.type_code, d.o_name) AS jname,
                    json_object_agg(d.type_code, d.o_code) AS jcode,
                    json_object_agg(d.type_code, d.ref_version) AS jversion
                FROM (
                    SELECT cas.id_synthese,
                        ta.type_code,
                        string_agg(ta.area_name::text, '|'::text) AS o_name,
                        string_agg(ta.area_code::text, '|'::text) AS o_code,
                        string_agg(ta.ref_version::character varying::text, '|'::text) AS ref_version
                    FROM gn_synthese.cor_area_synthese AS cas
                        JOIN areas AS ta ON ta.id_area = cas.id_area
                    WHERE cas.id_synthese = s.id_synthese
                    GROUP BY cas.id_synthese, ta.type_code
                ) AS d
                GROUP BY d.id_synthese
            ) AS a ON TRUE
            LEFT JOIN actors ON actors.id_dataset = s.id_dataset
            JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
            JOIN jdd_acteurs ON jdd_acteurs.id_dataset = s.id_dataset
            JOIN gn_meta.t_acquisition_frameworks af ON d.id_acquisition_framework = af.id_acquisition_framework
            JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
            LEFT JOIN ref_habitats.habref h ON h.cd_hab = s.cd_hab
            LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON s.id_nomenclature_geo_object_nature = n1.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON s.id_nomenclature_grp_typ = n2.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON s.id_nomenclature_behaviour = n3.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON s.id_nomenclature_obs_technique = n4.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON s.id_nomenclature_bio_status = n5.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON s.id_nomenclature_bio_condition = n6.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n7 ON s.id_nomenclature_naturalness = n7.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n8 ON s.id_nomenclature_exist_proof = n8.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n9 ON s.id_nomenclature_diffusion_level = n9.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n10 ON s.id_nomenclature_life_stage = n10.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n11 ON s.id_nomenclature_sex = n11.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n12 ON s.id_nomenclature_obj_count = n12.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n13 ON s.id_nomenclature_type_count = n13.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n14 ON s.id_nomenclature_sensitivity = n14.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n15 ON s.id_nomenclature_observation_status = n15.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n16 ON s.id_nomenclature_blurring = n16.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n17 ON s.id_nomenclature_source_status = n17.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n18 ON s.id_nomenclature_info_geo_type = n18.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures n19 ON s.id_nomenclature_determination_method = n19.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures dl ON s.id_nomenclature_diffusion_level = dl.id_nomenclature
            LEFT JOIN ref_nomenclatures.t_nomenclatures st ON s.id_nomenclature_observation_status = st.id_nomenclature
        WHERE st.cd_nomenclature::text = 'Pr'::text AND (EXISTS ( SELECT cda.id_dataset
                FROM gn_meta.cor_dataset_actor cda
            WHERE cda.id_dataset = s.id_dataset AND cda.id_organism = 2));

    """
    )


def downgrade():
    op.execute(
        """
            DROP VIEW IF EXISTS gn_exports.v_synthese_sinp_blurred
        """
    )
    op.execute(
        """
            DROP VIEW IF EXISTS gn_exports.v_synthese_sinp_blurred_test
        """
    )
    op.execute(
        """
            DROP MATERIALIZED VIEW IF EXISTS gn_exports.vm_synthese_blurred
        """
    )
