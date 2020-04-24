------------------------------------------------------------------------
-- Mise à jour du schéma gn_exports entre les versions 1.0.3 et 1.0.4 --
------------------------------------------------------------------------

-- Ajout de la Licence ouverte v2 d'Etalab dans les licences par défaut
INSERT INTO gn_exports.t_licences (name_licence, url_licence) VALUES
    ('Licence Ouverte/Open Licence Version 2.0', 'https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf');

-- Amélioration des performances de la vue SINP par défaut
-- Ajout du champs "nom_valide" dans cette vue

DROP VIEW gn_exports.v_synthese_sinp;
CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp AS 
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
    s.id_digitiser AS id_digitiser,
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
    t.nom_valide AS "nomValide",
    s.nom_cite AS "nomCite",
    public.ST_x(public.ST_transform(s.the_geom_point, 2154)) AS x_centroid,
    public.ST_y(public.ST_transform(s.the_geom_point, 2154)) AS y_centroid,
    COALESCE(s.meta_update_date, s.meta_create_date) AS lastact,
    n1.label_default AS "ObjGeoTyp",
    n2.label_default AS "methGrp",
    n3.label_default AS "obsMeth",
    n4.label_default AS "obsTech",
    n5.label_default AS "ocStatutBio",
    n6.label_default AS "ocEtatBio",
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
   FROM gn_synthese.synthese s
     JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
     JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
     JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
     LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON s.id_nomenclature_geo_object_nature = n1.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON s.id_nomenclature_grp_typ = n2.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON s.id_nomenclature_obs_meth = n3.id_nomenclature
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

COMMENT ON COLUMN gn_exports.v_synthese_sinp."idSynthese" IS 'Identifiant de la donnée dans la table synthese';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."permId" IS 'Identifiant permanent de l''occurrence';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."permIdGrp" IS 'Identifiant permanent du regroupement attribué par la plateforme régionale ou thématique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."denbrMin" IS 'Nb minimal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."denbrMax" IS 'Nb maximal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."vTAXREF" IS 'Version du taxref utilisé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."sampleNumb" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."preuvNum" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."preuvNoNum" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."altMin" IS 'Altitude min';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."altMax" IS 'Altitude max';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."geom" IS 'Géometrie';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."dateDebut" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."dateFin" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."validateur" IS 'Personne ayant procédé à la validation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."observer" IS 'Personne ayant procédé à l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."id_digitiser" IS 'Identifiant du numérisateur';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."detminer" IS 'Personne ayant procédé à la détermination';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."obsCtx" IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."obsDescr" IS 'Description libre de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."jddId" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."jddCode" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."id_acquisition_framework" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."cdNom" IS 'Identifiant taxref du nom de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."cdRef" IS 'Identifiant taxref du taxon correspondant à l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nomValide" IS 'Nom valide de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."nomCite" IS 'Nom de l''objet utilisé dans la donnée source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."x_centroid" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."y_centroid" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."lastact" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ObjGeoTyp" IS 'Classe associée au concept de localisation géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."methGrp" IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."obsMeth" IS '';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."obsTech" IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ocEtatBio" IS 'Code de l''état biologique de l''organisme au moment de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ocNat" IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."preuveOui" IS 'Indique si une preuve existe ou non';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."difNivPrec" IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ocStade" IS 'Stade de développement du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ocSex" IS 'Sexe du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."objDenbr" IS 'Objet sur lequel porte le dénombrement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."denbrTyp" IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."sensiNiv" IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."statObs" IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."dEEFlou" IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."statSource" IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."typInfGeo" IS 'Code HABREF de l''habitat où le taxon de l''observation a été identifié';
