"""Add blurred view

Revision ID: cbcf99cdb9a8
Revises: 1db24d9b23bc
Create Date: 2025-04-23 17:22:36.362008

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cbcf99cdb9a8"
down_revision = "8db5a13cf0d2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DROP VIEW IF EXISTS gn_exports.v_synthese_sinp_dee_blurred ;

        CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp_dee_blurred AS
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
                    bat.size_hierarchy,
                    la.id_area,
                    la.area_code,
                    la.area_name
                FROM ref_geo.bib_areas_types AS bat
                    JOIN ref_geo.l_areas AS la ON bat.id_type = la.id_type
                WHERE bat.type_code::text = ANY (ARRAY['DEP'::character varying, 'COM'::character varying, 'M10'::character varying]::text[])
            ),
            geom_blurred as (
            	SELECT DISTINCT ON (s.id_synthese, areas.id_type) s.id_synthese,
				    areas.geom_4326 AS geom
			   FROM gn_synthese.synthese s
			     JOIN ref_nomenclatures.t_nomenclatures sensi on s.id_nomenclature_sensitivity = sensi.id_nomenclature AND sensi.id_type = 16
			     JOIN gn_synthese.cor_area_synthese cor ON cor.id_synthese = s.id_synthese
			     JOIN ref_geo.l_areas areas ON cor.id_area = areas.id_area
			     JOIN gn_sensitivity.cor_sensitivity_area_type csat ON csat.id_nomenclature_sensitivity = sensi.id_nomenclature AND csat.id_area_type = areas.id_type
            )
            SELECT s.id_synthese AS "ID_synthese",
                s.entity_source_pk_value AS "idOrigine",
                s.unique_id_sinp AS "idSINPOccTax",
                s.unique_id_sinp_grp AS "idSINPRegroupement",
                actors.unique_dataset_id AS "idSINPJdd",
                s.date_min::date AS "dateDebut",
                s.date_min::time without time zone AS "heureDebut",
                s.date_max::date AS "dateFin",
                s.date_max::time without time zone AS "heureFin",
                t.cd_nom AS "cdNom",
                t.cd_ref AS "codeHabRef",
                h.cd_hab AS habitat,
                h.lb_code AS "codeHabitat",
                'Habref 5.0 2019'::text AS "versionRef",
                actors.organisms_list AS "organismeGestionnaireDonnee",
                a.jname ->> 'DEP'::text AS "nomDepartement",
                a.jcode ->> 'DEP'::text AS "codeDepartement",
                a.jversion ->> 'DEP'::text AS "anneeRefDepartement",
                a.jname ->> 'COM'::text AS "nomCommune",
                sensi_bat.size_hierarchy as "SizeHierarchy",
                a.jcode ->> 'COM'::text AS "codeCommune",
                a.jversion ->> 'COM'::text AS "anneeRefCommune",
                a.jcode ->> 'M10'::text AS "codeMaille",
                s.nom_cite AS "nomCite",
                s.count_min AS "denombrementMin",
                s.count_max AS "denombrementMax",
            	CASE WHEN geom_blurred IS NULL THEN s.altitude_min ELSE NULL END AS "altitudeMin",
			  	CASE WHEN geom_blurred IS NULL THEN s.altitude_max ELSE NULL END AS "altitudeMax",
			  	CASE WHEN geom_blurred IS NULL THEN (s.altitude_min + s.altitude_max) / 2 ELSE NULL END AS "altitudeMoyenne",
			  	CASE WHEN geom_blurred IS NULL THEN s.depth_min ELSE NULL END AS "profondeurMin",
			  	CASE WHEN geom_blurred IS NULL THEN s.depth_max ELSE NULL END AS "profondeurMax",
			  	CASE WHEN geom_blurred IS NULL THEN (s.depth_max - s.depth_min) / 2 ELSE NULL END AS "profondeurMoyenne",
			  	CASE WHEN geom_blurred IS NULL THEN s.the_geom_4326 ELSE geom_blurred.geom END AS geometrie,
                s.observers AS observateur,
                s.determiner AS determinateur,
                s.digital_proof AS "uRLPreuveNumerique",
                s.non_digital_proof AS "preuveNonNumerique",
                s."precision" AS "precisionGeometrie",
                s.place_name AS "nomLieu",
                s.comment_context AS commentaire,
                s.comment_description AS "obsDescription",
                s.meta_create_date AS "dateDetermination",
                s.meta_update_date AS "dEEDateTransformation",
                COALESCE(s.meta_update_date, s.meta_create_date) AS "dEEDateDerniereModification",
                s.reference_biblio AS "referenceBiblio",
                s.meta_update_date AS "sensiDateAttribution",
                n1.label_default AS "natureObjetGeo",
                n2.label_default AS "methodeRegroupement",
                n4.label_default AS "obsTechnique",
                n5.label_default AS "occStatutBiologique",
                n6.label_default AS "occEtatBiologique",
                n7.label_default AS "occNaturalite",
                n8.label_default AS "preuveExistante",
                n9.label_default AS "diffusionNiveauPrecision",
                n10.label_default AS "occStadeDeVie",
                n11.label_default AS "occSexe",
                n12.label_default AS "objetDenombrement",
                n13.label_default AS "typeDenombrement",
                n14.label_default AS "sensiNiveau",
                n15.label_default AS "statutObservation",
                n16.label_default AS "dEEFloutage",
                n17.label_default AS "statutSource",
                n19.label_default AS "occMethodeDetermination",
                n20.label_default AS "occComportement",
                n21.label_default AS "dSPublique"
            FROM gn_synthese.synthese AS s
                JOIN taxonomie.taxref AS t ON t.cd_nom = s.cd_nom
                left join geom_blurred on s.id_synthese = geom_blurred.id_synthese
                left join gn_sensitivity.cor_sensitivity_area_type csat on csat.id_nomenclature_sensitivity = s.id_nomenclature_sensitivity
                left join ref_geo.bib_areas_types sensi_bat on sensi_bat.id_type = csat.id_area_type
			    left JOIN ref_nomenclatures.t_nomenclatures sensi ON sensi.id_nomenclature = s.id_nomenclature_sensitivity
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
							and (ta.size_hierarchy >= sensi_bat.size_hierarchy or sensi_bat.size_hierarchy is NULL)
                        GROUP BY cas.id_synthese, ta.type_code
                    ) AS d
                    GROUP BY d.id_synthese
                ) AS a ON TRUE
                LEFT JOIN actors ON actors.id_dataset = s.id_dataset
                LEFT JOIN ref_habitats.habref AS h ON h.cd_hab = s.cd_hab
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n1 ON s.id_nomenclature_geo_object_nature = n1.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n2 ON s.id_nomenclature_grp_typ = n2.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n4 ON s.id_nomenclature_obs_technique = n4.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n5 ON s.id_nomenclature_bio_status = n5.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n6 ON s.id_nomenclature_bio_condition = n6.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n7 ON s.id_nomenclature_naturalness = n7.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n8 ON s.id_nomenclature_exist_proof = n8.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n9 ON s.id_nomenclature_diffusion_level = n9.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n10 ON s.id_nomenclature_life_stage = n10.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n11 ON s.id_nomenclature_sex = n11.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n12 ON s.id_nomenclature_obj_count = n12.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n13 ON s.id_nomenclature_type_count = n13.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n14 ON s.id_nomenclature_sensitivity = n14.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n15 ON s.id_nomenclature_observation_status = n15.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n16 ON s.id_nomenclature_blurring = n16.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n17 ON s.id_nomenclature_source_status = n17.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n18 ON s.id_nomenclature_info_geo_type = n18.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n19 ON s.id_nomenclature_determination_method = n19.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n20 ON s.id_nomenclature_behaviour = n20.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures AS n21 ON actors.id_nomenclature_data_origin = n21.id_nomenclature ;

        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."ID_synthese" IS 'Identifiant de la donnée dans la table synthese';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."idOrigine" IS 'Identifiant de la donnée dans la table source';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."idSINPOccTax" IS 'Identifiant permanent de l''occurrence';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."idSINPRegroupement" IS 'Identifiant permanent du regroupement';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."idSINPJdd" IS 'Identifiant unique du jeu de données';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."dateDebut" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."heureDebut" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."dateFin" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."heureFin" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."cdNom" IS 'Identifiant Taxref du nom de l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."codeHabRef" IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."habitat" IS 'Habitat dans lequel le taxon a été observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."codeHabitat" IS 'Code métier de l''habitat où le taxon de l''observation a été identifié';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."versionRef" IS 'Version de Habref utilisée';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."organismeGestionnaireDonnee" IS 'Notes : Nom de l’organisme qui détient la Donnée Source (DS) de la DEE et qui en a la responsabilité. Si plusieurs organismes sont nécessaires, les séparer par des virgules.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."nomDepartement" IS 'Nom du département';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."codeDepartement" IS 'Code INSEE en vigueur suivant l''année du référentiel INSEE des départements, auquel l''information est rattachée';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."anneeRefDepartement" IS 'Année du référentiel INSEE utilisé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."nomCommune" IS 'Nom de la commune. Libellé de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."codeCommune" IS 'Code de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."anneeRefCommune" IS 'Année de production du référentiel INSEE, qui sert à déterminer quel est le référentiel en vigueur pour le code et le nom de la commune';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."codeMaille" IS 'Code de la cellule de la grille de référence nationale 10kmx10km dans laquelle se situe l’observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."nomCite" IS 'Nom de l''objet utilisé dans la donnée source';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."denombrementMin" IS 'Nombre minimal d''objet dénombré';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."denombrementMax" IS 'Nombre maximal d''objet dénombré';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."altitudeMin" IS 'Altitude minimale';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."altitudeMax" IS 'Altitude maximale';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."altitudeMoyenne" IS 'Altitude moyenne de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."profondeurMin" IS 'Profondeur Minimum de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."profondeurMax" IS 'Profondeur Maximale de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."profondeurMoyenne" IS 'Profondeur moyenne de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."observateur" IS 'Personne(s) ayant procédé à l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."determinateur" IS 'Personne ayant procédé à la détermination';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."uRLPreuveNumerique" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."preuveNonNumerique" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."geometrie" IS 'Géometrie de la localisation de l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."precisionGeometrie" IS 'Estimation en mètres d’une zone tampon autour de l''objet géographique.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."nomLieu" IS 'Nom du lieu ou de la station où a été effectué l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."commentaire" IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."obsDescription" IS 'Description libre de l''observation, aussi succincte et précise que possible';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."dateDetermination" IS 'Date de création de la donnée';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."dEEDateTransformation" IS 'Date de la dernière modification de la données';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."dEEDateDerniereModification" IS 'Date de la dernière action sur l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."referenceBiblio" IS 'Référence de la source de l’observation lorsque celle-ci est de type « Littérature », au format ISO690';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."sensiDateAttribution" IS 'Date à laquelle on a attribué un niveau de sensibilité à la donnée. C''est également la date à laquelle on a consulté le référentiel de sensibilité associé.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."natureObjetGeo" IS 'Classe associée au concept de localisation géographique';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."methodeRegroupement" IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."obsTechnique" IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."occStatutBiologique" IS 'Comportement général de l''individu sur le site d''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."occEtatBiologique" IS 'Code de l''état biologique de l''organisme au moment de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."occNaturalite" IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."preuveExistante" IS 'Indique si une preuve existe ou non';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."diffusionNiveauPrecision" IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."occStadeDeVie" IS 'Stade de développement du sujet de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."occSexe" IS 'Sexe du sujet de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."objetDenombrement" IS 'Objet sur lequel porte le dénombrement';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."typeDenombrement" IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."sensiNiveau" IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."statutObservation" IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."dEEFloutage" IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."statutSource" IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."occMethodeDetermination" IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."occComportement" IS 'Comportement de l''individu ou groupe d''individus';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee_blurred."dSPublique" IS 'Indique explicitement si la donnée à l''origine de la DEE est publique ou privée. Cela concerne la donnée initiale et son acquisition naturaliste.';

    """
    )

    op.execute(
        """
            DROP VIEW if exists gn_exports.v_synthese_sinp_blurred;
            CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp_blurred AS
			WITH jdd_acteurs AS (
			SELECT
                d.id_dataset,
                string_agg(DISTINCT concat(COALESCE(orga.nom_organisme, ((roles.nom_role::text || ' '::text) || roles.prenom_role::text)::character varying), ' (', nomencl.label_default,')'), ', '::text) AS acteurs
            FROM gn_meta.t_datasets d
                JOIN gn_meta.cor_dataset_actor act ON act.id_dataset = d.id_dataset
                JOIN ref_nomenclatures.t_nomenclatures nomencl ON nomencl.id_nomenclature = act.id_nomenclature_actor_role
                LEFT JOIN utilisateurs.bib_organismes orga ON orga.id_organisme = act.id_organism
                LEFT JOIN utilisateurs.t_roles roles ON roles.id_role = act.id_role
            GROUP BY d.id_dataset
            ),
            geom_blurred as (
            	SELECT DISTINCT ON (s.id_synthese, areas.id_type) s.id_synthese,
				    areas.geom_4326 AS geom
			   FROM gn_synthese.synthese s
			     JOIN ref_nomenclatures.t_nomenclatures sensi on s.id_nomenclature_sensitivity = sensi.id_nomenclature AND sensi.id_type = 16
			     JOIN gn_synthese.cor_area_synthese cor ON cor.id_synthese = s.id_synthese
			     JOIN ref_geo.l_areas areas ON cor.id_area = areas.id_area
			     JOIN gn_sensitivity.cor_sensitivity_area_type csat ON csat.id_nomenclature_sensitivity = sensi.id_nomenclature AND csat.id_area_type = areas.id_type
            )
            SELECT s.id_synthese AS "id_synthese",
                s.entity_source_pk_value AS "id_source",
                s.unique_id_sinp AS "id_perm_sinp",
                s.unique_id_sinp_grp AS "id_perm_grp_sinp",
                s.date_min AS "date_debut",
                s.date_max AS "date_fin",
                t.cd_nom AS "cd_nom",
                t.cd_ref AS "cd_ref",
                s.meta_v_taxref AS "version_taxref",
                s.nom_cite AS "nom_cite",
                t.nom_valide AS "nom_valide",
                t.regne AS "regne",
                t.group1_inpn AS "group1_inpn",
                t.group2_inpn AS "group2_inpn",
                t.classe AS "classe",
                t.ordre AS "ordre",
                t.famille AS "famille",
                t.id_rang AS "rang_taxo",
                s.count_min AS "nombre_min",
                s.count_max AS "nombre_max",
                CASE WHEN geom_blurred IS NULL THEN s.altitude_min ELSE NULL END AS "altitude_min",
			  	CASE WHEN geom_blurred IS NULL THEN s.altitude_max ELSE NULL END AS "altitude_max",
			  	CASE WHEN geom_blurred IS NULL THEN s.depth_min ELSE NULL END AS "profondeur_min",
			  	CASE WHEN geom_blurred IS NULL THEN s.depth_max ELSE NULL END AS "profondeur_max",
			  	CASE WHEN geom_blurred IS NULL THEN s.the_geom_4326 ELSE geom_blurred.geom END AS geom,
                s.observers AS "observateurs",
                s.determiner AS "determinateur",
                s.validator AS "validateur",
                s.sample_number_proof AS "numero_preuve",
                s.digital_proof AS "preuve_numerique",
                s.non_digital_proof AS "preuve_non_numerique",
                s.comment_context AS "comment_releve",
                s.comment_description AS "comment_occurrence",
                s.meta_create_date AS "date_creation",
                s.meta_update_date AS "date_modification",
                coalesce(s.meta_update_date, s.meta_create_date) AS "derniere_action",
                d.unique_dataset_id AS "jdd_uuid",
                d.dataset_name AS "jdd_nom",
                jdd_acteurs.acteurs AS "jdd_acteurs",
                af.unique_acquisition_framework_id AS "ca_uuid",
                af.acquisition_framework_name AS "ca_nom",
                s.reference_biblio AS "reference_biblio",
                s.cd_hab AS "code_habitat",
                h.lb_hab_fr AS "habitat",
                s.place_name AS "nom_lieu",
                s.precision AS "precision",
                s.additional_data::text AS "donnees_additionnelles",
                CASE WHEN geom_blurred IS NULL THEN public.st_astext(s.the_geom_4326) ELSE public.st_astext(geom_blurred.geom) END as "wkt_4326",
                CASE WHEN geom_blurred IS NULL THEN public.st_x(s.the_geom_point) else null end AS "x_centroid_4326",
                CASE WHEN geom_blurred IS NULL THEN public.st_y(s.the_geom_point) else null end AS "y_centroid_4326",
                n1.label_default AS "nature_objet_geo",
                n2.label_default AS "type_regroupement",
                s.grp_method AS "methode_regroupement",
                n3.label_default AS "comportement",
                n4.label_default AS "technique_obs",
                n5.label_default AS "statut_biologique",
                n6.label_default AS "etat_biologique",
                n7.label_default AS "naturalite",
                n8.label_default AS "preuve_existante",
                n9.label_default AS "precision_diffusion",
                n10.label_default AS "stade_vie",
                n11.label_default AS "sexe",
                n12.label_default AS "objet_denombrement",
                n13.label_default AS "type_denombrement",
                n14.label_default AS "niveau_sensibilite",
                n15.label_default AS "statut_observation",
                n16.label_default AS "floutage_dee",
                n17.label_default AS "statut_source",
                n18.label_default AS "type_info_geo",
                n19.label_default AS "methode_determination"
            FROM gn_synthese.synthese s
            	left join geom_blurred on s.id_synthese = geom_blurred.id_synthese
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
                LEFT JOIN ref_nomenclatures.t_nomenclatures n19 ON s.id_nomenclature_determination_method = n19.id_nomenclature;


            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."id_synthese"            IS 'Identifiant de la donnée dans la table synthese';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."id_source"              IS 'Identifiant de la donnée dans la table source';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."id_perm_sinp"           IS 'Identifiant permanent de l''occurrence';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."id_perm_grp_sinp"       IS 'Identifiant permanent du regroupement';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."date_debut"             IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."date_fin"               IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."cd_nom"                 IS 'Identifiant Taxref du nom de l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."cd_ref"                 IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."version_taxref"         IS 'Version de Taxref utilisée';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."nom_cite"               IS 'Nom de l''objet utilisé dans la donnée source';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."nom_valide"             IS 'Nom valide de l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."regne"                  IS 'Règne de l''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."group1_inpn"            IS 'Groupe INPN (1) de l''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."group2_inpn"            IS 'Groupe INPN (2) de l''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."classe"                 IS 'Classe de l''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."ordre"                  IS 'Ordre de l''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."famille"                IS 'Famille de l''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."rang_taxo"              IS 'Rang taxonomique de l''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."nombre_min"             IS 'Nombre minimal d''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."nombre_max"             IS 'Nombre maximal d''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."altitude_min"           IS 'Altitude minimale';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."altitude_max"           IS 'Altitude maximale';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."profondeur_min"         IS 'Profondeur minimale';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."profondeur_max"         IS 'Profondeur maximale';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."observateurs"           IS 'Personne(s) ayant procédé à l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."determinateur"          IS 'Personne ayant procédé à la détermination';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."validateur"             IS 'Personne ayant procédé à la validation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."numero_preuve"          IS 'Numéro de l''échantillon de la preuve';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."preuve_numerique"       IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."preuve_non_numerique"   IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."geom"                   IS 'Géometrie de la localisation de l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."comment_releve"         IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."comment_occurrence"     IS 'Description libre de l''observation, aussi succincte et précise que possible';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."date_creation"          IS 'Date de création de la donnée';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."date_modification"      IS 'Date de la dernière modification de la données';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."derniere_action"        IS 'Date de la dernière action sur l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."jdd_uuid"               IS 'Identifiant unique du jeu de données';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."jdd_nom"                IS 'Nom du jeu de données';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."jdd_acteurs"            IS 'Acteurs du jeu de données';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."ca_uuid"                IS 'Identifiant unique du cadre d''acquisition';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."ca_nom"                 IS 'Nom du cadre d''acquisition';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."reference_biblio"       IS 'Référence bibliographique';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."code_habitat"           IS 'Code habitat (Habref)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."habitat"                IS 'Libellé français de l''habitat (Habref)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."nom_lieu"               IS 'Nom du lieu';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."precision"              IS 'Précision de la géométrie. Estimation en mètres d''une zone tampon autour de l''objet géographique';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."donnees_additionnelles" IS 'Données des champs additionnels';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."wkt_4326"               IS 'Géométrie complète de la localisation en projection WGS 84 (4326)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."x_centroid_4326"        IS 'Latitude du centroïde de la localisation en projection WGS 84 (4326)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."y_centroid_4326"        IS 'Longitude du centroïde de la localisation en projection WGS 84 (4326)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."nature_objet_geo"       IS 'Classe associée au concept de localisation géographique';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."type_regroupement"      IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."methode_regroupement"   IS 'Méthode du regroupement';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."technique_obs"          IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."statut_biologique"      IS 'Comportement général de l''individu sur le site d''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."comportement"           IS 'Comportement de l''individu ou groupe d''individus';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."etat_biologique"        IS 'Code de l''état biologique de l''organisme au moment de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."naturalite"             IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."preuve_existante"       IS 'Indique si une preuve existe ou non';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."precision_diffusion"    IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."stade_vie"              IS 'Stade de développement du sujet de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."sexe"                   IS 'Sexe du sujet de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."objet_denombrement"     IS 'Objet sur lequel porte le dénombrement';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."type_denombrement"      IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."niveau_sensibilite"     IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."statut_observation"     IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."floutage_dee"           IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."statut_source"          IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."type_info_geo"          IS 'Type d''information géographique';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_blurred."methode_determination"  IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';

        """
    )

    op.execute(
        """
            INSERT INTO gn_exports.t_exports (view_pk_column, label, schema_name, view_name, "desc", geometry_field, geometry_srid, public, id_licence)
            VALUES ('id_synthese', 'Synthese SINP Floutée', 'gn_exports', 'v_synthese_sinp_blurred', 'Export des données de la synthèse au standard SINP et floutée', 'geom', 4326, FALSE, 1);
        """
    )


def downgrade():
    op.execute(
        """
            DELETE FROM gn_exports.t_exports WHERE view_name = 'v_synthese_sinp_blurred';

            DROP VIEW IF EXISTS gn_exports.v_synthese_sinp_dee_blurred;

            DROP VIEW IF EXISTS gn_exports.v_synthese_sinp_blurred;
        """
    )
