
-- Révision de la vue d'export SINP par défaut avec la mise à jour du standard Occurrences de taxons en version 2.0
-- Compatibilité avec GeoNature 2.5.0 et +

DROP VIEW if exists gn_exports.v_synthese_sinp;
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
    s.altitude_min AS "altitude_min",
    s.altitude_max AS "altitude_max",
    s.depth_min AS "profondeur_min",
    s.depth_max AS "profondeur_max",
    s.observers AS "observateurs",
    s.determiner AS "determinateur",
    s.validator AS "validateur",
    s.sample_number_proof AS "numero_preuve",
    s.digital_proof AS "preuve_numerique",
    s.non_digital_proof AS "preuve_non_numerique",
    s.the_geom_4326 AS geom,
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
    public.st_astext(s.the_geom_4326) AS "wkt_4326",
    public.st_x(s.the_geom_point) AS "x_centroid_4326",
    public.st_y(s.the_geom_point) AS "y_centroid_4326",
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

COMMENT ON COLUMN gn_exports.v_synthese_sinp."id_synthese"            IS 'Identifiant de la donnée dans la table synthese';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."id_source"              IS 'Identifiant de la donnée dans la table source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."id_perm_sinp"           IS 'Identifiant permanent de l''occurrence';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."id_perm_grp_sinp"       IS 'Identifiant permanent du regroupement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."date_debut"             IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."date_fin"               IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."cd_nom"                 IS 'Identifiant Taxref du nom de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."cd_ref"                 IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."version_taxref"         IS 'Version de Taxref utilisée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nom_cite"               IS 'Nom de l''objet utilisé dans la donnée source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nom_valide"             IS 'Nom valide de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."regne"                  IS 'Règne de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."group1_inpn"            IS 'Groupe INPN (1) de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."group2_inpn"            IS 'Groupe INPN (2) de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."classe"                 IS 'Classe de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ordre"                  IS 'Ordre de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."famille"                IS 'Famille de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."rang_taxo"              IS 'Rang taxonomique de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nombre_min"             IS 'Nombre minimal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nombre_max"             IS 'Nombre maximal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."altitude_min"           IS 'Altitude minimale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."altitude_max"           IS 'Altitude maximale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."profondeur_min"         IS 'Profondeur minimale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."profondeur_max"         IS 'Profondeur maximale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."observateurs"           IS 'Personne(s) ayant procédé à l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."determinateur"          IS 'Personne ayant procédé à la détermination';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."validateur"             IS 'Personne ayant procédé à la validation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."numero_preuve"          IS 'Numéro de l''échantillon de la preuve';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."preuve_numerique"       IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."preuve_non_numerique"   IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."geom"                   IS 'Géometrie de la localisation de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."comment_releve"         IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."comment_occurrence"     IS 'Description libre de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."date_creation"          IS 'Date de création de la donnée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."date_modification"      IS 'Date de la dernière modification de la données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."derniere_action"        IS 'Date de la dernière action sur l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."jdd_uuid"               IS 'Identifiant unique du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."jdd_nom"                IS 'Nom du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."jdd_acteurs"            IS 'Acteurs du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ca_uuid"                IS 'Identifiant unique du cadre d''acquisition';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ca_nom"                 IS 'Nom du cadre d''acquisition';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."reference_biblio"       IS 'Référence bibliographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."code_habitat"           IS 'Code habitat (Habref)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."habitat"                IS 'Libellé français de l''habitat (Habref)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nom_lieu"               IS 'Nom du lieu';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."precision"              IS 'Précision de la géométrie. Estimation en mètres d''une zone tampon autour de l''objet géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."donnees_additionnelles" IS 'Données des champs additionnels';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."wkt_4326"               IS 'Géométrie complète de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."x_centroid_4326"        IS 'Latitude du centroïde de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."y_centroid_4326"        IS 'Longitude du centroïde de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nature_objet_geo"       IS 'Classe associée au concept de localisation géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."type_regroupement"      IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."methode_regroupement"   IS 'Méthode du regroupement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."technique_obs"          IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."statut_biologique"      IS 'Comportement général de l''individu sur le site d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."comportement"           IS 'Comportement de l''individu ou groupe d''individus';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."etat_biologique"        IS 'Code de l''état biologique de l''organisme au moment de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."naturalite"             IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."preuve_existante"       IS 'Indique si une preuve existe ou non';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."precision_diffusion"    IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."stade_vie"              IS 'Stade de développement du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."sexe"                   IS 'Sexe du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."objet_denombrement"     IS 'Objet sur lequel porte le dénombrement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."type_denombrement"      IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."niveau_sensibilite"     IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."statut_observation"     IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."floutage_dee"           IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."statut_source"          IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."type_info_geo"          IS 'Type d''information géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."methode_determination"  IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';

-- Révision de la vue permettant de faire les exports RDF
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


-- Vue d'export des données de la synthèse au format DEE du SINP
DROP VIEW IF EXISTS  gn_exports.v_synthese_sinp_dee;
CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp_dee AS
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
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMin" IS 'Profondeur Minimum de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMax" IS 'Profondeur Maximale de l’observation en mètres selon le référentiel des profondeurs indiqué dans les métadonnées (système de référence spatiale verticale)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."profondeurMoyenne" IS 'Profondeur moyenne de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."observateur" IS 'Personne(s) ayant procédé à l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."determinateur" IS 'Personne ayant procédé à la détermination';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."uRLPreuveNumerique" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."preuveNonNumerique" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."geometrie" IS 'Géometrie de la localisation de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp_dee."precisionGeometrie" IS 'Estimation en mètres d’une zone tampon autour de l''objet géographique';
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
