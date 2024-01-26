"""Fix and improve SINP DEE synthese view (see #105)

Revision ID: fe1347f4805f
Revises: 75edd92560d7
Create Date: 2023-05-11 20:21:38.452938

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fe1347f4805f"
down_revision = "75edd92560d7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DROP VIEW gn_exports.v_synthese_sinp_dee ;

        CREATE VIEW gn_exports.v_synthese_sinp_dee AS
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
                a.jcode ->> 'COM'::text AS "codeCommune",
                a.jversion ->> 'COM'::text AS "anneeRefCommune",
                a.jcode ->> 'M10'::text AS "codeMaille",
                s.nom_cite AS "nomCite",
                s.count_min AS "denombrementMin",
                s.count_max AS "denombrementMax",
                s.altitude_min AS "altitudeMin",
                s.altitude_max AS "altitudeMax",
                (s.altitude_min + s.altitude_max) / 2 AS "altitudeMoyenne",
                s.depth_min AS "profondeurMin",
                s.depth_max AS "profondeurMax",
                (s.depth_max - s.depth_min) / 2 AS "profondeurMoyenne",
                s.observers AS observateur,
                s.determiner AS determinateur,
                s.digital_proof AS "uRLPreuveNumerique",
                s.non_digital_proof AS "preuveNonNumerique",
                s.the_geom_4326 AS geometrie,
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

        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."ID_synthese" IS 'Identifiant de la donnée dans la table synthese';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idOrigine" IS 'Identifiant de la donnée dans la table source';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idSINPOccTax" IS 'Identifiant permanent de l''occurrence';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idSINPRegroupement" IS 'Identifiant permanent du regroupement';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idSINPJdd" IS 'Identifiant unique du jeu de données';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dateDebut" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."heureDebut" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dateFin" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."heureFin" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."cdNom" IS 'Identifiant Taxref du nom de l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeHabRef" IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."habitat" IS 'Habitat dans lequel le taxon a été observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeHabitat" IS 'Code métier de l''habitat où le taxon de l''observation a été identifié';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."versionRef" IS 'Version de Habref utilisée';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."organismeGestionnaireDonnee" IS 'Notes : Nom de l’organisme qui détient la Donnée Source (DS) de la DEE et qui en a la responsabilité. Si plusieurs organismes sont nécessaires, les séparer par des virgules.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomDepartement" IS 'Nom du département';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeDepartement" IS 'Code INSEE en vigueur suivant l''année du référentiel INSEE des départements, auquel l''information est rattachée';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."anneeRefDepartement" IS 'Année du référentiel INSEE utilisé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomCommune" IS 'Nom de la commune. Libellé de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeCommune" IS 'Code de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."anneeRefCommune" IS 'Année de production du référentiel INSEE, qui sert à déterminer quel est le référentiel en vigueur pour le code et le nom de la commune';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeMaille" IS 'Code de la cellule de la grille de référence nationale 10kmx10km dans laquelle se situe l’observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomCite" IS 'Nom de l''objet utilisé dans la donnée source';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."denombrementMin" IS 'Nombre minimal d''objet dénombré';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."denombrementMax" IS 'Nombre maximal d''objet dénombré';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."altitudeMin" IS 'Altitude minimale';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."altitudeMax" IS 'Altitude maximale';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."altitudeMoyenne" IS 'Altitude moyenne de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMin" IS 'Profondeur Minimum de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMax" IS 'Profondeur Maximale de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMoyenne" IS 'Profondeur moyenne de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."observateur" IS 'Personne(s) ayant procédé à l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."determinateur" IS 'Personne ayant procédé à la détermination';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."uRLPreuveNumerique" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."preuveNonNumerique" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."geometrie" IS 'Géometrie de la localisation de l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."precisionGeometrie" IS 'Estimation en mètres d’une zone tampon autour de l''objet géographique.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomLieu" IS 'Nom du lieu ou de la station où a été effectué l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."commentaire" IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."obsDescription" IS 'Description libre de l''observation, aussi succincte et précise que possible';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dateDetermination" IS 'Date de création de la donnée';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dEEDateTransformation" IS 'Date de la dernière modification de la données';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dEEDateDerniereModification" IS 'Date de la dernière action sur l''objet observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."referenceBiblio" IS 'Référence de la source de l’observation lorsque celle-ci est de type « Littérature », au format ISO690';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."sensiDateAttribution" IS 'Date à laquelle on a attribué un niveau de sensibilité à la donnée. C''est également la date à laquelle on a consulté le référentiel de sensibilité associé.';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."natureObjetGeo" IS 'Classe associée au concept de localisation géographique';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."methodeRegroupement" IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."obsTechnique" IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occStatutBiologique" IS 'Comportement général de l''individu sur le site d''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occEtatBiologique" IS 'Code de l''état biologique de l''organisme au moment de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occNaturalite" IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."preuveExistante" IS 'Indique si une preuve existe ou non';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."diffusionNiveauPrecision" IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occStadeDeVie" IS 'Stade de développement du sujet de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occSexe" IS 'Sexe du sujet de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."objetDenombrement" IS 'Objet sur lequel porte le dénombrement';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."typeDenombrement" IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."sensiNiveau" IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."statutObservation" IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dEEFloutage" IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."statutSource" IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occMethodeDetermination" IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occComportement" IS 'Comportement de l''individu ou groupe d''individus';
        COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dSPublique" IS 'Indique explicitement si la donnée à l''origine de la DEE est publique ou privée. Cela concerne la donnée initiale et son acquisition naturaliste.';
        """
    )


def downgrade():
    op.execute(
        """
        DROP VIEW gn_exports.v_synthese_sinp_dee ;

        CREATE VIEW gn_exports.v_synthese_sinp_dee AS
            WITH cda AS (
                SELECT
                    d.id_dataset,
                    string_agg(DISTINCT orga.nom_organisme, ' | ') AS acteurs
                FROM gn_meta.t_datasets d
                    JOIN gn_meta.cor_dataset_actor act ON act.id_dataset = d.id_dataset
                    JOIN ref_nomenclatures.t_nomenclatures nomencl ON nomencl.id_nomenclature = act.id_nomenclature_actor_role
                    LEFT JOIN utilisateurs.bib_organismes orga ON orga.id_organisme = act.id_organism
                    LEFT JOIN utilisateurs.t_roles roles ON roles.id_role = act.id_role
                WHERE  nomencl.cd_nomenclature = '1' AND act.id_organism IS NOT NULL
                GROUP BY d.id_dataset
            ),
            areas AS (
                SELECT ta.id_type, type_code, ta.ref_version, id_area, a_1.area_code, a_1.area_name
                FROM ref_geo.bib_areas_types ta
                JOIN ref_geo.l_areas a_1 ON ta.id_type = a_1.id_type
                WHERE  ta.type_code in ('DEP', 'COM', 'M1')
            )
            SELECT s.id_synthese AS "ID_synthese",
                s.entity_source_pk_value AS "idOrigine",
                s.unique_id_sinp AS "idSINPOccTax",
                s.unique_id_sinp_grp AS "idSINPRegroupement",
                d.unique_dataset_id AS "idSINPJdd",
                s.date_min::date AS "dateDebut",
                s.date_min::time as "heureDebut",
                s.date_max::date AS "dateFin",
                s.date_max::time as "heureFin",
                t.cd_nom AS "cdNom",
                t.cd_ref AS "codeHabRef",
                h.cd_hab AS "habitat",
                h.lb_code AS "codeHabitat",
                'Habref 5.0 2019' AS "versionRef",
                cda.acteurs AS "organismeGestionnaireDonnee",
                a.jname ->> 'DEP' AS "nomDepartement",
                a.jcode ->> 'DEP' AS "codeDepartement",
                a.jversion->> 'DEP' AS "anneeRefDepartement",
                a.jname ->> 'COM' AS "nomCommune",
                a.jcode ->> 'COM' AS "codeCommune",
                a.jversion->> 'COM' AS "anneeRefCommune",
                a.jcode ->> 'M10' AS "codeMaille",
                s.nom_cite AS "nomCite",
                s.count_min AS "denombrementMin",
                s.count_max AS "denombrementMax",
                s.altitude_min AS "altitudeMin",
                s.altitude_max AS "altitudeMax",
                (s.altitude_min + s.altitude_max) / 2 AS "altitudeMoyenne",
                s.depth_min AS "profondeurMin",
                s.depth_max as "profondeurMax",
                (s.depth_max - s.depth_min) / 2 as "profondeurMoyenne",
                s.observers AS "observateur",
                s.determiner AS "determinateur",
                s.digital_proof AS "uRLPreuveNumerique",
                s.non_digital_proof AS "preuveNonNumerique",
                s.the_geom_4326 AS "geometrie",
                s."precision" AS "precisionGeometrie",
                s.place_name AS "nomLieu",
                s.comment_context AS "commentaire",
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
            FROM gn_synthese.synthese s
                JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
                JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
                JOIN gn_meta.t_acquisition_frameworks af ON d.id_acquisition_framework = af.id_acquisition_framework
                JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
                LEFT JOIN cda ON d.id_dataset = cda.id_dataset
                LEFT JOIN LATERAL (
                    SELECT
                        d_1.id_synthese,
                        json_object_agg(d_1.type_code, d_1.o_name) AS jname,
                        json_object_agg(d_1.type_code, d_1.o_code) AS jcode,
                        json_object_agg(d_1.type_code, d_1.ref_version) AS jversion
                    FROM (
                        SELECT
                            sa.id_synthese,
                            ta.type_code,
                            string_agg(ta.area_name, '|') AS o_name,
                            string_agg(ta.area_code, '|') AS o_code,
                            string_agg(ta.ref_version::varchar, '|') AS ref_version
                        FROM gn_synthese.cor_area_synthese sa
                        JOIN areas ta ON ta.id_area = sa.id_area
                        WHERE sa.id_synthese = s.id_synthese
                        GROUP BY sa.id_synthese, ta.type_code
                    ) d_1
                    GROUP BY d_1.id_synthese
                ) a ON TRUE
                LEFT JOIN ref_habitats.habref h ON h.cd_hab = s.cd_hab
                LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON s.id_nomenclature_geo_object_nature = n1.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON s.id_nomenclature_grp_typ = n2.id_nomenclature
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
                LEFT JOIN ref_nomenclatures.t_nomenclatures n20 ON s.id_nomenclature_behaviour = n20.id_nomenclature
                LEFT JOIN ref_nomenclatures.t_nomenclatures n21 ON d.id_nomenclature_data_origin = n21.id_nomenclature
            ;

            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."ID_synthese" IS 'Identifiant de la donnée dans la table synthese';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idOrigine" IS 'Identifiant de la donnée dans la table source';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idSINPOccTax" IS 'Identifiant permanent de l''occurrence';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idSINPRegroupement" IS 'Identifiant permanent du regroupement';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."idSINPJdd" IS 'Identifiant unique du jeu de données';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dateDebut" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."heureDebut" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dateFin" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."heureFin" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."cdNom" IS 'Identifiant Taxref du nom de l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeHabRef" IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."habitat" IS 'Habitat dans lequel le taxon a été observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeHabitat" IS 'Code métier de l''habitat où le taxon de l''observation a été identifié';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."versionRef" IS 'Version de Habref utilisée';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."organismeGestionnaireDonnee" IS 'Notes : Nom de l’organisme qui détient la Donnée Source (DS) de la DEE et qui en a la responsabilité. Si plusieurs organismes sont nécessaires, les séparer par des virgules.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomDepartement" IS 'Nom du département';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeDepartement" IS 'Code INSEE en vigueur suivant l''année du référentiel INSEE des départements, auquel l''information est rattachée';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."anneeRefDepartement" IS 'Année du référentiel INSEE utilisé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomCommune" IS 'Nom de la commune. Libellé de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeCommune" IS 'Code de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."anneeRefCommune" IS 'Année de production du référentiel INSEE, qui sert à déterminer quel est le référentiel en vigueur pour le code et le nom de la commune';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."codeMaille" IS 'Code de la cellule de la grille de référence nationale 10kmx10km dans laquelle se situe l’observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomCite" IS 'Nom de l''objet utilisé dans la donnée source';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."denombrementMin" IS 'Nombre minimal d''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."denombrementMax" IS 'Nombre maximal d''objet dénombré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."altitudeMin" IS 'Altitude minimale';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."altitudeMax" IS 'Altitude maximale';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."altitudeMoyenne" IS 'Altitude moyenne de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMin" IS 'Profondeur Minimum de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMax" IS 'Profondeur Maximale de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMoyenne" IS 'Profondeur moyenne de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."observateur" IS 'Personne(s) ayant procédé à l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."determinateur" IS 'Personne ayant procédé à la détermination';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."uRLPreuveNumerique" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."preuveNonNumerique" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."geometrie" IS 'Géometrie de la localisation de l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."precisionGeometrie" IS 'Estimation en mètres d’une zone tampon autour de l''objet géographique.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."nomLieu" IS 'Nom du lieu ou de la station où a été effectué l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."commentaire" IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."obsDescription" IS 'Description libre de l''observation, aussi succincte et précise que possible';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dateDetermination" IS 'Date de création de la donnée';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dEEDateTransformation" IS 'Date de la dernière modification de la données';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dEEDateDerniereModification" IS 'Date de la dernière action sur l''objet observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."referenceBiblio" IS 'Référence de la source de l’observation lorsque celle-ci est de type « Littérature », au format ISO690';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."sensiDateAttribution" IS 'Date à laquelle on a attribué un niveau de sensibilité à la donnée. C''est également la date à laquelle on a consulté le référentiel de sensibilité associé.';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."natureObjetGeo" IS 'Classe associée au concept de localisation géographique';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."methodeRegroupement" IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."obsTechnique" IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occStatutBiologique" IS 'Comportement général de l''individu sur le site d''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occEtatBiologique" IS 'Code de l''état biologique de l''organisme au moment de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occNaturalite" IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."preuveExistante" IS 'Indique si une preuve existe ou non';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."diffusionNiveauPrecision" IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occStadeDeVie" IS 'Stade de développement du sujet de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occSexe" IS 'Sexe du sujet de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."objetDenombrement" IS 'Objet sur lequel porte le dénombrement';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."typeDenombrement" IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."sensiNiveau" IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."statutObservation" IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dEEFloutage" IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."statutSource" IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occMethodeDetermination" IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."occComportement" IS 'Comportement de l''individu ou groupe d''individus';
            COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."dSPublique" IS 'Indique explicitement si la donnée à l''origine de la DEE est publique ou privée. Cela concerne la donnée initiale et son acquisition naturaliste.';
        """
    )
