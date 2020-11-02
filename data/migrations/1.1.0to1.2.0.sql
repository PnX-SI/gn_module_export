
-- Révision de la vue d'export SINP par défaut avec la mise à jour du standard Occurrences de taxons en version 2.0
-- Compatibilité avec GeoNature 2.5.0 et +

DROP VIEW IF EXISTS  gn_exports.v_synthese_sinp;
CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp AS
 WITH jdd_acteurs AS (  
 SELECT
    d.id_dataset,
    string_agg(DISTINCT concat(COALESCE(orga.nom_organisme, ((roles.nom_role::text || ' '::text) || roles.prenom_role::text)::character varying), ' : ', nomencl.label_default), ' | '::text) AS acteurs
   FROM gn_meta.t_datasets d
     JOIN gn_meta.cor_dataset_actor act ON act.id_dataset = d.id_dataset
     JOIN ref_nomenclatures.t_nomenclatures nomencl ON nomencl.id_nomenclature = act.id_nomenclature_actor_role
     LEFT JOIN utilisateurs.bib_organismes orga ON orga.id_organisme = act.id_organism
     LEFT JOIN utilisateurs.t_roles roles ON roles.id_role = act.id_role
  GROUP BY d.id_dataset
)
 SELECT s.id_synthese AS "ID_synthese",
    s.entity_source_pk_value AS "ID_source",
    s.unique_id_sinp AS "ID_perm_SINP",
    s.unique_id_sinp_grp AS "ID_perm_GRP_SINP",
    s.date_min AS "Date_debut",
    s.date_max AS "Date_fin",
    t.cd_nom AS "CD_nom",
    t.cd_ref AS "CD_ref",
    s.meta_v_taxref AS "Version_Taxref",
    s.nom_cite AS "Nom_cite",
    t.nom_valide AS "Nom_valide",
    t.regne AS "Regne",
    t.group1_inpn AS "Group1_INPN",
    t.group2_inpn AS "Group2_INPN",
    t.classe AS "Classe",
    t.ordre AS "Ordre",
    t.famille AS "Famille",
    t.id_rang AS "Rang_taxo",
    s.count_min AS "Nombre_min",
    s.count_max AS "Nombre_max",
    s.altitude_min AS "Altitude_min",
    s.altitude_max AS "Altitude_max",
    s.depth_min as "Profondeur_min",
    s.depth_max as "Profondeur_max",
    s.observers AS "Observateurs",
    s.determiner AS "Determinateur",
    s.validator AS "Validateur",
    s.sample_number_proof AS "Numero_preuve",
    s.digital_proof AS "Preuve_numerique",
    s.non_digital_proof AS "Preuve_non_numerique",
    s.the_geom_4326 AS geom,
    s.comment_context AS "Comment_releve",
    s.comment_description AS "Comment_occurrence",
    s.meta_create_date AS "Date_creation",
    s.meta_update_date AS "Date_modification",
    COALESCE(s.meta_update_date, s.meta_create_date) AS "Derniere_action",
    d.unique_dataset_id AS "JDD_UUID",
    d.dataset_name AS "JDD_nom",
    jdd_acteurs.acteurs AS "JDD_acteurs",
    af.unique_acquisition_framework_id AS "CA_UUID",
    af.acquisition_framework_name AS "CA_nom",
    s.reference_biblio AS "Reference_biblio",
    s.cd_hab AS "Code_habitat",
    h.lb_hab_fr AS "Habitat",
    s.place_name AS "Nom_lieu",
    s.precision AS "Precision",
    s.additional_data AS "Donnees_additionnelles",
    public.st_astext(s.the_geom_4326) AS "WKT_4326",
    public.ST_x(s.the_geom_point) AS "X_centroid_4326",
    public.ST_y(s.the_geom_point) AS "Y_centroid_4326",
    n1.label_default AS "Nature_objet_geo",
    n2.label_default AS "Type_regroupement",
    s.grp_method AS "Methode_regroupement",
    n3.label_default as "Comportement",
    n4.label_default AS "Technique_obs",
    n5.label_default AS "Statut_biologique",
    n6.label_default AS "Etat_biologique",
    n7.label_default AS "Naturalite",
    n8.label_default AS "Preuve_existante",
    n9.label_default AS "Precision_diffusion",
    n10.label_default AS "Stade_vie",
    n11.label_default AS "Sexe",
    n12.label_default AS "Objet_denombrement",
    n13.label_default AS "Type_denombrement",
    n14.label_default AS "Niveau_sensibilite",
    n15.label_default AS "Statut_observation",
    n16.label_default AS "Floutage_DEE",
    n17.label_default AS "Statut_source",
    n18.label_default AS "Type_info_geo",
    n19.label_default AS "Methode_determination"
   FROM gn_synthese.synthese s
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
;

COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_synthese" IS 'Identifiant de la donnée dans la table synthese';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_source" IS 'Identifiant de la donnée dans la table source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_perm_SINP" IS 'Identifiant permanent de l''occurrence';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_perm_GRP_SINP" IS 'Identifiant permanent du regroupement attribué par la plateforme régionale ou thématique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_debut" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_fin" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CD_nom" IS 'Identifiant Taxref du nom de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CD_ref" IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Version_Taxref" IS 'Version de Taxref utilisée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nom_cite" IS 'Nom de l''objet utilisé dans la donnée source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nom_valide" IS 'Nom valide de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Regne" IS 'Règne de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Group1_INPN" IS 'Groupe INPN (1) de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Group2_INPN" IS 'Groupe INPN (2) de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Classe" IS 'Classe de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Ordre" IS 'Ordre de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Famille" IS 'Famille de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Rang_taxo" IS 'Rang taxonomique de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nombre_min" IS 'Nombre minimal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nombre_max" IS 'Nombre maximal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Altitude_min" IS 'Altitude minimale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Altitude_max" IS 'Altitude maximale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Profondeur_min" IS 'Profondeur minimale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Profondeur_max" IS 'Profondeur maximale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Observateurs" IS 'Personne(s) ayant procédé à l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Determinateur" IS 'Personne ayant procédé à la détermination';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Validateur" IS 'Personne ayant procédé à la validation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Numero_preuve" IS 'Numéro de l''échantillon de la preuve';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Preuve_numerique" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Preuve_non_numerique" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."geom" IS 'Géometrie de la localisation de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Comment_releve" IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Comment_occurrence" IS 'Description libre de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_creation" IS 'Date de création de la donnée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_modification" IS 'Date de la dernière modification de la données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Derniere_action" IS 'Date de la dernière action sur l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."JDD_UUID" IS 'Identifiant unique du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."JDD_nom" IS 'Nom du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."JDD_acteurs" IS 'Acteurs du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CA_UUID" IS 'Identifiant unique du cadre d''acquisition';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CA_nom" IS 'Nom du cadre d''acquisition';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Reference_biblio" IS 'Référence bibliographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Code_habitat" IS 'Code habitat (Habref)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Habitat" IS 'Libellé français de l''habitat (Habref)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nom_lieu" IS 'Nom du lieu';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Precision" IS 'Précision de la géométrie. Estimation en mètres d''une zone tampon autour de l''objet géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Donnees_additionnelles" IS 'Données des champs additionnels';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."WKT_4326" IS 'Géométrie complète de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."X_centroid_4326" IS 'Latitude du centroïde de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Y_centroid_4326" IS 'Longitude du centroïde de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nature_objet_geo" IS 'Classe associée au concept de localisation géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Type_regroupement" IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Methode_regroupement" IS 'Méthode du regroupement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Technique_obs" IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Statut_biologique" IS 'Comportement général de l''individu sur le site d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Comportement" IS 'Comportement de l''individu ou groupe d''individus';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Etat_biologique" IS 'Code de l''état biologique de l''organisme au moment de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Naturalite" IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Preuve_existante" IS 'Indique si une preuve existe ou non';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Precision_diffusion" IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Stade_vie" IS 'Stade de développement du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Sexe" IS 'Sexe du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Objet_denombrement" IS 'Objet sur lequel porte le dénombrement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Type_denombrement" IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Niveau_sensibilite" IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Statut_observation" IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Floutage_DEE" IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Statut_source" IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Type_info_geo" IS 'Type d''information géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Methode_determination" IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';


DROP VIEW IF EXISTS gn_exports.v_exports_synthese_sinp_rdf ;
CREATE OR REPLACE VIEW gn_exports.v_exports_synthese_sinp_rdf AS
    WITH deco AS (
         SELECT s_1.id_synthese,
            n1.label_default AS "ObjGeoTyp",
            n2.label_default AS "methGrp",
            n3.label_default AS "occComport",
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
             LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON s_1.id_nomenclature_behaviour = n3.id_nomenclature
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
),
        info_dataset AS (
        SELECT da.id_dataset, r.label_default, org.uuid_organisme, nom_organisme
        FROM gn_meta.cor_dataset_actor da
        JOIN ref_nomenclatures.t_nomenclatures r
        ON da.id_nomenclature_actor_role = r.id_nomenclature
        JOIN utilisateurs.bib_organismes org
        ON da.id_organism = org.id_organisme
        WHERE r.mnemonique = 'Producteur du jeu de données'
)
 SELECT s.id_synthese AS "idSynthese",
    s.unique_id_sinp AS "permId",
    COALESCE(s.unique_id_sinp_grp, s.unique_id_sinp) AS "permIdGrp",
    s.count_min AS "denbrMin",
    s.count_max AS "denbrMax",
    s.meta_v_taxref AS "vTAXREF",
    s.sample_number_proof AS "sampleNumb",
    s.digital_proof AS "preuvNum",
    s.non_digital_proof AS "preuvNoNum",
    s.altitude_min AS "altMin",
    s.altitude_max AS "altMax",
    public.st_astext(s.the_geom_4326) AS "geom",
    s.date_min AS "dateDebut",
    s.date_max AS "dateFin",
    s.validator AS "validateur",
    s.observers AS "observer",
    s.id_digitiser,
    s.determiner AS "determiner",
    s.comment_context AS "obsCtx",
    s.comment_description AS "obsDescr",
    s.meta_create_date,
    s.meta_update_date,
    d.unique_dataset_id AS "jddId",
    d.dataset_name AS "jddCode",
    d.id_acquisition_framework,
    t.cd_nom AS "cdNom",
    t.cd_ref AS "cdRef",
    s.nom_cite AS "nomCite",
    t.nom_complet AS nom_complet,
    public.st_x(public.st_transform(s.the_geom_point, 4326)) AS "x_centroid",
    public.st_y(public.st_transform(s.the_geom_point, 4326)) AS "y_centroid",
    COALESCE(s.meta_update_date, s.meta_create_date) AS lastact,
    deco."ObjGeoTyp",
    deco."methGrp",
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
    deco."typInfGeo",
    info_d.uuid_organisme as "ownerInstitutionID",
    info_d.nom_organisme as "ownerInstitutionCode"
FROM gn_synthese.synthese s
JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
JOIN deco ON deco.id_synthese = s.id_synthese
LEFT OUTER JOIN info_dataset info_d ON info_d.id_dataset = d.id_dataset;


-- Vue par défaut d'export des données de la synthèse au format SINP v2
DROP VIEW IF EXISTS  gn_exports.v_synthese_sinp_v2;
CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp_v2 AS
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
	SELECT ta.id_type, type_code, id_area, a_1.area_code, a_1.area_name 
	FROM ref_geo.bib_areas_types ta
	JOIN ref_geo.l_areas a_1 ON ta.id_type = a_1.id_type
	WHERE  ta.type_code in ('DEP', 'COM', 'M1')
), current_year AS (
	SELECT date_part('YEAR', current_timestamp)::int AS current_year
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
    cy.current_year AS "anneeRefDepartement",
    a.jname ->> 'COM' AS "nomCommune",
    a.jcode ->> 'COM' AS "codeCommune",
    cy.current_year AS "anneeRefCommune",
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
    (
    	SELECT meta_create_date
	     FROM gn_sensitivity.cor_sensitivity_synthese css
	     WHERE css.uuid_attached_row = s.unique_id_sinp
	     ORDER BY meta_create_date DESC
	     LIMIT 1
     ) AS "sensiDateAttribution",
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
   JOIN current_year cy ON true
     JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
     JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
     JOIN gn_meta.t_acquisition_frameworks af ON d.id_acquisition_framework = af.id_acquisition_framework
     JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
     LEFT JOIN cda ON d.id_dataset = cda.id_dataset
     LEFT JOIN LATERAL ( 
		SELECT 
			d_1.id_synthese,
	        json_object_agg(d_1.type_code, d_1.o_name) AS jname,
	        json_object_agg(d_1.type_code, d_1.o_code) AS jcode
	   	FROM ( 
	   		SELECT 
	   			sa.id_synthese,
				ta.type_code,
				string_agg(ta.area_name, '|') AS o_name,
				string_agg(ta.area_code, '|') AS o_code
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

COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."ID_synthese" IS 'Identifiant de la donnée dans la table synthese';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."idOrigine" IS 'Identifiant de la donnée dans la table source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."idSINPOccTax" IS 'Identifiant permanent de l''occurrence';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."idSINPRegroupement" IS 'Identifiant permanent du regroupement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."idSINPJdd" IS 'Identifiant unique du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."dateDebut" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."heureDebut" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."dateFin" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."heureFin" IS 'Heure du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."cdNom" IS 'Identifiant Taxref du nom de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."codeHabRef" IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."habitat" IS 'Habitat dans lequel le taxon a été observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."codeHabitat" IS 'Code métier de l''habitat où le taxon de l''observation a été identifié';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."versionRef" IS 'Version de Habref utilisée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."organismeGestionnaireDonnee" IS 'Notes:	Nom de l’organisme qui détient la Donnée Source (DS) de la DEE et qui en a la responsabilité. Si plusieurs organismes sont nécessaires, les séparer par des virgules.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."nomDepartement" IS 'Nom du département.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."codeDepartement" IS 'Code INSEE en vigueur suivant l''année du référentiel INSEE des départements, auquel l''information est rattachée.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."anneeRefDepartement" IS 'Année du référentiel INSEE utilisé.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."nomCommune" IS 'Nom de la commune. Libellé de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."codeCommune" IS 'Code de la/les commune(s) où a été effectuée l’observation suivant le référentiel INSEE en vigueur';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."anneeRefCommune" IS 'Année de production du référentiel INSEE, qui sert à déterminer quel est le référentiel en vigueur pour le code et le nom de la commune.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."codeMaille" IS 'Code de la cellule de la grille de référence nationale 10kmx10km dans laquelle se situe l’observation.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."nomCite" IS 'Nom de l''objet utilisé dans la donnée source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."denombrementMin" IS 'Nombre minimal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."denombrementMax" IS 'Nombre maximal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."altitudeMin" IS 'Altitude minimale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."altitudeMax" IS 'Altitude maximale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."altitudeMoyenne" IS 'Altitude moyenne de l''observation.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."profondeurMin" IS 'Profondeur Minimum de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."profondeurMax" IS 'Profondeur Maximale de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale).';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."profondeurMoyenne" IS 'Profondeur moyenne de l''observation.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."observateur" IS 'Personne(s) ayant procédé à l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."determinateur" IS 'Personne ayant procédé à la détermination';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."uRLPreuveNumerique" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."preuveNonNumerique" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."geometrie" IS 'Géometrie de la localisation de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."precisionGeometrie" IS 'Estimation en mètres d’une zone tampon autour de l''objet géographique.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."nomLieu" IS 'Nom du lieu ou de la station où a été effectué l''observation.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."commentaire" IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."obsDescription" IS 'Description libre de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."dateDetermination" IS 'Date de création de la donnée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."dEEDateTransformation" IS 'Date de la dernière modification de la données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."dEEDateDerniereModification" IS 'Date de la dernière action sur l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."referenceBiblio" IS 'Référence de la source de l’observation lorsque celle-ci est de type « Littérature », au format ISO690';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."sensiDateAttribution" IS 'Date à laquelle on a attribué un niveau de sensibilité à la donnée. C''est également la date à laquelle on a consulté le référentiel de sensibilité associé.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."natureObjetGeo" IS 'Classe associée au concept de localisation géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."methodeRegroupement" IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."obsTechnique" IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."occStatutBiologique" IS 'Comportement général de l''individu sur le site d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."occEtatBiologique" IS 'Code de l''état biologique de l''organisme au moment de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."occNaturalite" IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."preuveExistante" IS 'Indique si une preuve existe ou non';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."diffusionNiveauPrecision" IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."occStadeDeVie" IS 'Stade de développement du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."occSexe" IS 'Sexe du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."objetDenombrement" IS 'Objet sur lequel porte le dénombrement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."typeDenombrement" IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."sensiNiveau" IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."statutObservation" IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."dEEFloutage" IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."statutSource" IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."occMethodeDetermination" IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."occComportement" IS 'Comportement de l''individu ou groupe d''individus.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_v2."dSPublique" IS 'Indique explicitement si la donnée à l''origine de la DEE est publique ou privée. Cela concerne la donnée initiale et son acquisition naturaliste.';
