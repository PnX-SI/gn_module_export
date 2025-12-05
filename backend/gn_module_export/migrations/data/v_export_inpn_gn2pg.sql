CREATE VIEW gn_exports.v_export_inpn
            (id_synthese, id_perm_sinp, "idSinpSujetObs", "idSinpEvenement", "idSinpDescriptif", "idOrigineSujetObs",
             "idSinpRegroupement", "dateDebut", "dateFin", "heureDebut", "heureFin", "cdNom", "nomCite",
             "denombrementMin", "denombrementMax", "altitudeMin", "altitudeMax", "profondeurMin", "profondeurMax",
             observateur, determinateur, "echelleValidation", "validateurValRegOuNat", "validateurValProd",
             "niveauValidationValReg", "niveauValidationValProd", "niveauValidationValProd_label",
             "commentaireValidation", "urlPreuveNumerique", "preuveNonNumerique", geometrie, cd_geo, "typeLocalisation",
             "commentaireEvenement", "commentaireDescriptif", "idSinpJdd", "referenceSource", "cdHab", habitat_label,
             "nomLocalisation", "precisionGeometrie", "natureObjetGeo", natureobjetgeo_label, "typeRegroupement",
             typeregroupement_label, "nomRegroupement", comportement, comportement_label, "indicePresence",
             technique_obs_label, statut_biologique, statut_biologique_label, "etatBiologique", etat_biologique_label,
             spontaneite, naturalite_label, "stadeBiologique", stade_vie_label, sexe, sexe_label, "objetDenombrement",
             objet_denombrement_label, "methodeDenombrement", type_denombrement_label, niveau_sensibilite,
             niveau_sensibilite_label, "statutObservation", statut_observation_label, "statutSource",
             statut_source_label, methode_determination, methode_determination_label, "AttributAdditionnel", jdd_data,
             ca_data, derniere_action)
AS
WITH params(echelle_validation) AS (VALUES ('region'::text)),
     base_production(base) AS (VALUES (NULL::text)),
     af_objectifs AS (SELECT c.id_acquisition_framework,
                             STRING_AGG(tn.label_default::text, ','::text) AS objectifs
                      FROM gn_meta.cor_acquisition_framework_objectif c
                               JOIN ref_nomenclatures.t_nomenclatures tn
                                    ON tn.id_nomenclature = c.id_nomenclature_objectif
                      GROUP BY c.id_acquisition_framework),
     af_voletsinp AS (SELECT c.id_acquisition_framework,
                             STRING_AGG(tn.label_default::text, ','::text) AS voletsinp
                      FROM gn_meta.cor_acquisition_framework_objectif c
                               JOIN ref_nomenclatures.t_nomenclatures tn
                                    ON tn.id_nomenclature = c.id_nomenclature_objectif
                      GROUP BY c.id_acquisition_framework),
     af_principal AS (SELECT taf_1.unique_acquisition_framework_id                                              AS "IdentifiantCadreAcquisition",
                             taf_1.acquisition_framework_name                                                   AS "LibelleCadreAcquisition",
                             taf_1.acquisition_framework_desc                                                   AS "DescriptionCadreAcquisition",
                             o.objectifs                                                                        AS "Objectifs",
                             taf_1.keywords                                                                     AS "MotsCles",
                             taf_1.territory_desc                                                               AS "PrecisionGeographique",
                             meta.unique_acquisition_framework_id                                               AS "ReferenceMetacadre",
                             taf_1.territory_desc                                                               AS " Territoires",
                             tnf.label_default                                                                  AS "TypeFinancement",
                             v.voletsinp                                                                        AS "VoletSINP",
                             tnt.label_default                                                                  AS "NiveauTerritorial",
                             NULL::text                                                                         AS "NomFichierTaxonomique",
                             NULL::text                                                                         AS "StatutAvancement",
                             taf_1.acquisition_framework_end_date                                               AS "DateCloture",
                             taf_1.acquisition_framework_start_date                                             AS "DateLancement",
                             CONCAT_WS(', '::text, taf_1.target_description,
                                       taf_1.ecologic_or_geologic_target)                                       AS "DescriptionCibleTaxo",
                             'Non'::text                                                                        AS "FichierJointOuiNon",
                             NULL::text                                                                         AS "IdentifiantProcedureDepot",
                             taf_1.is_parent                                                                    AS "estMetaCadre"
                      FROM gn_meta.t_acquisition_frameworks taf_1
                               LEFT JOIN gn_meta.t_acquisition_frameworks meta
                                         ON meta.id_acquisition_framework = taf_1.acquisition_framework_parent_id
                               LEFT JOIN ref_nomenclatures.t_nomenclatures tnt
                                         ON tnt.id_nomenclature = taf_1.id_nomenclature_territorial_level
                               LEFT JOIN ref_nomenclatures.t_nomenclatures tnf
                                         ON tnf.id_nomenclature = taf_1.id_nomenclature_financing_type
                               LEFT JOIN af_objectifs o ON taf_1.id_acquisition_framework = o.id_acquisition_framework
                               LEFT JOIN af_voletsinp v ON taf_1.id_acquisition_framework = v.id_acquisition_framework),
     json_af_principal AS (SELECT p."IdentifiantCadreAcquisition",
                                  TO_JSON(p.*) AS "Principal"
                           FROM af_principal p),
     af_contact_principal AS (SELECT taf_1.unique_acquisition_framework_id    AS "IdentifiantCadreAcquisition",
                                     CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteContactPrincipal",
                                     bo.nom_organisme                         AS "OrganismeContactPrincipal",
                                     COALESCE(tr.email, bo.email_organisme)   AS "MailContactPrincipal",
                                     bo.uuid_organisme
                              FROM gn_meta.t_acquisition_frameworks taf_1
                                       JOIN gn_meta.cor_acquisition_framework_actor cda
                                            ON taf_1.id_acquisition_framework = cda.id_acquisition_framework
                                       LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                       LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                              WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                       FROM ref_nomenclatures.t_nomenclatures tn
                                                                       WHERE tn.mnemonique::text = 'Contact principal'::text))),
     json_af_contact_principal AS (SELECT cp."IdentifiantCadreAcquisition",
                                          TO_JSON(cp.*) AS "ContactPrincipal"
                                   FROM af_contact_principal cp),
     af_financeurs AS (SELECT taf_1.unique_acquisition_framework_id    AS "IdentifiantCadreAcquisition",
                              CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteFinanceur",
                              bo.nom_organisme                         AS "OrganismeFinanceur",
                              COALESCE(tr.email, bo.email_organisme)   AS "MailFinanceur",
                              bo.uuid_organisme
                       FROM gn_meta.t_acquisition_frameworks taf_1
                                JOIN gn_meta.cor_acquisition_framework_actor cda
                                     ON taf_1.id_acquisition_framework = cda.id_acquisition_framework
                                LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                       WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                FROM ref_nomenclatures.t_nomenclatures tn
                                                                WHERE tn.mnemonique::text = 'Financeur'::text))),
     json_af_financeur AS (SELECT cb."IdentifiantCadreAcquisition",
                                  JSON_AGG(TO_JSON(cb.*)) AS "Financeurs"
                           FROM af_financeurs cb
                           GROUP BY cb."IdentifiantCadreAcquisition"),
     af_maitriseoeuvre AS (SELECT taf_1.unique_acquisition_framework_id    AS "IdentifiantCadreAcquisition",
                                  CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteMaitreOeuvre",
                                  bo.nom_organisme                         AS "OrganismeMaitreOeuvre",
                                  COALESCE(tr.email, bo.email_organisme)   AS "MailMaitreOeuvre",
                                  bo.uuid_organisme
                           FROM gn_meta.t_acquisition_frameworks taf_1
                                    JOIN gn_meta.cor_acquisition_framework_actor cda
                                         ON taf_1.id_acquisition_framework = cda.id_acquisition_framework
                                    LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                    LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                           WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                    FROM ref_nomenclatures.t_nomenclatures tn
                                                                    WHERE tn.mnemonique::text = 'Maître d''oeuvre'::text))),
     json_af_matriseoeuvre AS (SELECT f."IdentifiantCadreAcquisition",
                                      JSON_AGG(TO_JSON(f.*)) AS "MaitriseOeuvre"
                               FROM af_maitriseoeuvre f
                               GROUP BY f."IdentifiantCadreAcquisition"),
     af_maitriseouvrage AS (SELECT taf_1.unique_acquisition_framework_id    AS "IdentifiantCadreAcquisition",
                                   CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteMaitreOuvrage",
                                   bo.nom_organisme                         AS "OrganismeMaitreOuvrage",
                                   COALESCE(tr.email, bo.email_organisme)   AS "MailMaitreOuvrage",
                                   bo.uuid_organisme
                            FROM gn_meta.t_acquisition_frameworks taf_1
                                     JOIN gn_meta.cor_acquisition_framework_actor cda
                                          ON taf_1.id_acquisition_framework = cda.id_acquisition_framework
                                     LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                     LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                            WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                     FROM ref_nomenclatures.t_nomenclatures tn
                                                                     WHERE tn.mnemonique::text = 'Maître d''ouvrage'::text))),
     json_af_maitriseouvrage AS (SELECT pr."IdentifiantCadreAcquisition",
                                        JSON_AGG(TO_JSON(pr.*)) AS "MaitriseOuvrage"
                                 FROM af_maitriseouvrage pr
                                 GROUP BY pr."IdentifiantCadreAcquisition"),
     af AS (SELECT jp."IdentifiantCadreAcquisition",
                   JSONB_BUILD_OBJECT('IdentifiantCadreAcquisition', jp."IdentifiantCadreAcquisition", 'uuid',
                                      jp."IdentifiantCadreAcquisition", 'Principal', jp."Principal", 'ContactPrincipal',
                                      jcp."ContactPrincipal", 'Financeurs', jf."Financeurs", 'MaitriseOeuvre',
                                      jmo1."MaitriseOeuvre", 'MaitriseOuvrage', jmo2."MaitriseOuvrage") AS af_data
            FROM json_af_principal jp
                     LEFT JOIN json_af_contact_principal jcp
                               ON jcp."IdentifiantCadreAcquisition" = jp."IdentifiantCadreAcquisition"
                     LEFT JOIN json_af_financeur jf
                               ON jf."IdentifiantCadreAcquisition" = jp."IdentifiantCadreAcquisition"
                     LEFT JOIN json_af_matriseoeuvre jmo1
                               ON jmo1."IdentifiantCadreAcquisition" = jp."IdentifiantCadreAcquisition"
                     LEFT JOIN json_af_maitriseouvrage jmo2
                               ON jmo2."IdentifiantCadreAcquisition" = jp."IdentifiantCadreAcquisition"),
     ds_principal AS (SELECT td.unique_dataset_id                  AS "IdentifiantJeuDonnees",
                             (SELECT base_production.base
                              FROM base_production)                AS "BaseProduction",
                             td.dataset_name                       AS "Libelle",
                             td.dataset_shortname                  AS "LibelleCourt",
                             td.keywords                           AS "MotsCles",
                             tno.label_default                     AS "Objectifs",
                             taf_1.unique_acquisition_framework_id AS "RattachementCadreAcquisition",
                             tnt.label_default                     AS "Territoires",
                             tntd.label_default                    AS "TypeDonnees",
                             td.terrestrial_domain                 AS "estContinental",
                             td.marine_domain                      AS "estMarin"
                      FROM gn_meta.t_datasets td
                               JOIN gn_meta.t_acquisition_frameworks taf_1
                                    ON taf_1.id_acquisition_framework = td.id_acquisition_framework
                               LEFT JOIN ref_nomenclatures.t_nomenclatures tno
                                         ON tno.id_nomenclature = td.id_nomenclature_dataset_objectif
                               LEFT JOIN ref_nomenclatures.t_nomenclatures tnt
                                         ON tnt.id_nomenclature = taf_1.id_nomenclature_territorial_level
                               LEFT JOIN ref_nomenclatures.t_nomenclatures tntd
                                         ON tntd.id_nomenclature = td.id_nomenclature_data_type),
     json_ds_principal AS (SELECT p."IdentifiantJeuDonnees",
                                  TO_JSON(p.*) AS "Principal"
                           FROM ds_principal p),
     ds_contact_principal AS (SELECT td.unique_dataset_id                     AS "IdentifiantJeuDonnees",
                                     CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteContactPrincipal",
                                     bo.nom_organisme                         AS "OrganismeContactPrincipal",
                                     COALESCE(tr.email, bo.email_organisme)   AS "MailContactPrincipal",
                                     bo.uuid_organisme
                              FROM gn_meta.t_datasets td
                                       JOIN gn_meta.cor_dataset_actor cda ON td.id_dataset = cda.id_dataset
                                       LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                       LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                              WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                       FROM ref_nomenclatures.t_nomenclatures tn
                                                                       WHERE tn.mnemonique::text = 'Contact principal'::text))),
     json_ds_contact_principal AS (SELECT cp."IdentifiantJeuDonnees",
                                          TO_JSON(cp.*) AS "ContactPrincipal"
                                   FROM ds_contact_principal cp),
     ds_contact_baseprod AS (SELECT td.unique_dataset_id                     AS "IdentifiantJeuDonnees",
                                    CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteContactFournisseur",
                                    bo.nom_organisme                         AS "OrganismeContactFournisseur",
                                    COALESCE(tr.email, bo.email_organisme)   AS "MailContactFournisseur",
                                    bo.uuid_organisme
                             FROM gn_meta.t_datasets td
                                      JOIN gn_meta.cor_dataset_actor cda ON td.id_dataset = cda.id_dataset
                                      LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                      LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                             WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                      FROM ref_nomenclatures.t_nomenclatures tn
                                                                      WHERE tn.mnemonique::text =
                                                                            'Point de contact base de données de production'::text))),
     json_ds_contact_baseprod AS (SELECT cb."IdentifiantJeuDonnees",
                                         JSON_AGG(TO_JSON(cb.*)) AS "ContactBaseProd"
                                  FROM ds_contact_baseprod cb
                                  GROUP BY cb."IdentifiantJeuDonnees"),
     ds_fournisseurs AS (SELECT td.unique_dataset_id                     AS "IdentifiantJeuDonnees",
                                CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteContactFournisseur",
                                bo.nom_organisme                         AS "OrganismeContactFournisseur",
                                COALESCE(tr.email, bo.email_organisme)   AS "MailContactFournisseur",
                                bo.uuid_organisme
                         FROM gn_meta.t_datasets td
                                  JOIN gn_meta.cor_dataset_actor cda ON td.id_dataset = cda.id_dataset
                                  LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                  LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                         WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                  FROM ref_nomenclatures.t_nomenclatures tn
                                                                  WHERE tn.mnemonique::text = 'Fournisseur du jeu de données'::text))),
     json_ds_fournisseur AS (SELECT f_1."IdentifiantJeuDonnees",
                                    JSON_AGG(TO_JSON(f_1.*)) AS "Fournisseurs"
                             FROM ds_fournisseurs f_1
                             GROUP BY f_1."IdentifiantJeuDonnees"),
     ds_producteur AS (SELECT td.unique_dataset_id                     AS "IdentifiantJeuDonnees",
                              CONCAT(tr.nom_role, ' ', tr.prenom_role) AS "IdentiteContactProducteur",
                              bo.nom_organisme                         AS organismecontactproducteur,
                              COALESCE(tr.email, bo.email_organisme)   AS "MailContactProducteur",
                              bo.uuid_organisme
                       FROM gn_meta.t_datasets td
                                JOIN gn_meta.cor_dataset_actor cda ON td.id_dataset = cda.id_dataset
                                LEFT JOIN utilisateurs.bib_organismes bo ON bo.id_organisme = cda.id_organism
                                LEFT JOIN utilisateurs.t_roles tr ON tr.id_role = cda.id_role
                       WHERE cda.id_nomenclature_actor_role = ((SELECT tn.id_nomenclature
                                                                FROM ref_nomenclatures.t_nomenclatures tn
                                                                WHERE tn.mnemonique::text = 'Producteur du jeu de données'::text))),
     json_ds_producteur AS (SELECT pr_1."IdentifiantJeuDonnees",
                                   JSON_AGG(TO_JSON(pr_1.*)) AS "Producteurs"
                            FROM ds_producteur pr_1
                            GROUP BY pr_1."IdentifiantJeuDonnees"),
     ds AS (SELECT jp."IdentifiantJeuDonnees",
                   JSONB_BUILD_OBJECT('IdentifiantJeuDonnees', jp."IdentifiantJeuDonnees", 'uuid',
                                      jp."IdentifiantJeuDonnees", 'Principal', jp."Principal", 'ContactPrincipal',
                                      jcp."ContactPrincipal", 'Fournisseurs', f."Fournisseurs", 'Producteurs',
                                      pr."Producteurs") AS dataset_data
            FROM json_ds_principal jp
                     LEFT JOIN json_ds_contact_principal jcp ON jcp."IdentifiantJeuDonnees" = jp."IdentifiantJeuDonnees"
                     LEFT JOIN json_ds_contact_baseprod jcb ON jcb."IdentifiantJeuDonnees" = jp."IdentifiantJeuDonnees"
                     LEFT JOIN json_ds_fournisseur f ON f."IdentifiantJeuDonnees" = jp."IdentifiantJeuDonnees"
                     LEFT JOIN json_ds_producteur pr ON pr."IdentifiantJeuDonnees" = jp."IdentifiantJeuDonnees")
SELECT s.id_synthese,
       s.unique_id_sinp                                                                AS id_perm_sinp,
       s.unique_id_sinp                                                                AS "idSinpSujetObs",
       s.unique_id_sinp                                                                AS "idSinpEvenement",
       s.unique_id_sinp                                                                AS "idSinpDescriptif",
       COALESCE(NULLIF(s.entity_source_pk_value::text, ''::text), s.id_synthese::text) AS "idOrigineSujetObs",
       s.unique_id_sinp_grp                                                            AS "idSinpRegroupement",
       s.date_min::date                                                                AS "dateDebut",
       s.date_max::date                                                                AS "dateFin",
       s.date_min::time without time zone                                              AS "heureDebut",
       s.date_max::time without time zone                                              AS "heureFin",
       t.cd_nom                                                                        AS "cdNom",
       s.nom_cite                                                                      AS "nomCite",
       s.count_min                                                                     AS "denombrementMin",
       s.count_max                                                                     AS "denombrementMax",
       s.altitude_min                                                                  AS "altitudeMin",
       s.altitude_max                                                                  AS "altitudeMax",
       s.depth_min                                                                     AS "profondeurMin",
       s.depth_max                                                                     AS "profondeurMax",
       s.observers                                                                     AS observateur,
       s.determiner                                                                    AS determinateur,
       CASE
           WHEN ((SELECT params.echelle_validation
                  FROM params)) = 'region'::text THEN 2
           ELSE NULL::integer
           END                                                                         AS "echelleValidation",
       CASE
           WHEN ((SELECT params.echelle_validation
                  FROM params)) = 'region'::text THEN s.validator
           ELSE NULL::character varying
           END                                                                         AS "validateurValRegOuNat",
       CASE
           WHEN ((SELECT params.echelle_validation
                  FROM params)) <> 'region'::text THEN s.validator
           ELSE NULL::character varying
           END                                                                         AS "validateurValProd",
       CASE
           WHEN ((SELECT params.echelle_validation
                  FROM params)) = 'region'::text THEN n20.cd_nomenclature
           ELSE NULL::character varying
           END                                                                         AS "niveauValidationValReg",
       CASE
           WHEN ((SELECT params.echelle_validation
                  FROM params)) <> 'region'::text THEN n20.cd_nomenclature
           ELSE NULL::character varying
           END                                                                         AS "niveauValidationValProd",
       n20.label_default                                                               AS "niveauValidationValProd_label",
       s.validation_comment                                                            AS "commentaireValidation",
       s.digital_proof                                                                 AS "urlPreuveNumerique",
       s.non_digital_proof                                                             AS "preuveNonNumerique",
       CASE
           WHEN s.id_area_attachment IS NULL THEN s.the_geom_4326
           ELSE NULL::geometry
           END                                                                         AS geometrie,
       ta.area_code                                                                    AS cd_geo,
       CASE
           WHEN ta.area_code IS NULL THEN 'géométrie'::text
           ELSE 'administratif'::text
           END                                                                         AS "typeLocalisation",
       s.comment_context                                                               AS "commentaireEvenement",
       s.comment_description                                                           AS "commentaireDescriptif",
       d.unique_dataset_id                                                             AS "idSinpJdd",
       s.reference_biblio                                                              AS "referenceSource",
       s.cd_hab                                                                        AS "cdHab",
       h.lb_hab_fr                                                                     AS habitat_label,
       s.place_name                                                                    AS "nomLocalisation",
       s."precision"                                                                   AS "precisionGeometrie",
       n1.cd_nomenclature                                                              AS "natureObjetGeo",
       n1.label_default                                                                AS natureobjetgeo_label,
       n2.cd_nomenclature                                                              AS "typeRegroupement",
       n2.label_default                                                                AS typeregroupement_label,
       s.grp_method                                                                    AS "nomRegroupement",
       n3.cd_nomenclature                                                              AS comportement,
       n3.label_default                                                                AS comportement_label,
       n4.cd_nomenclature                                                              AS "indicePresence",
       n4.label_default                                                                AS technique_obs_label,
       n5.cd_nomenclature                                                              AS "phaseBiologique",
       n5.label_default                                                                AS statut_biologique_label,
       n6.cd_nomenclature                                                              AS "etatBiologique",
       n6.label_default                                                                AS etat_biologique_label,
       n7.cd_nomenclature                                                              AS spontaneite,
       n7.label_default                                                                AS naturalite_label,
       n10.cd_nomenclature                                                             AS "stadeBiologique",
       n10.label_default                                                               AS stade_vie_label,
       n11.cd_nomenclature                                                             AS sexe,
       n11.label_default                                                               AS sexe_label,
       n12.cd_nomenclature                                                             AS "objetDenombrement",
       n12.label_default                                                               AS objet_denombrement_label,
       n13.cd_nomenclature                                                             AS "methodeDenombrement",
       n13.label_default                                                               AS type_denombrement_label,
       n14.cd_nomenclature                                                             AS niveau_sensibilite,
       n14.label_default                                                               AS niveau_sensibilite_label,
       n15.cd_nomenclature                                                             AS "statutObservation",
       n15.label_default                                                               AS statut_observation_label,
       n17.cd_nomenclature                                                             AS "statutSource",
       n17.label_default                                                               AS statut_source_label,
       n19.cd_nomenclature                                                             AS methode_determination,
       n19.label_default                                                               AS methode_determination_label,
       s.additional_data::text                                                         AS "AttributAdditionnel",
       ds.dataset_data                                                                 AS jdd_data,
       af.af_data                                                                      AS ca_data,
       COALESCE(s.meta_update_date, s.meta_create_date)                                AS derniere_action
FROM gn_synthese.synthese s
         JOIN gn_meta.t_datasets tds ON tds.id_dataset = s.id_dataset
         JOIN gn_meta.t_acquisition_frameworks taf ON tds.id_acquisition_frameworfk = taf.id_acquisition_frameworfk
         JOIN ds ON ds."IdentifiantJeuDonnees" = tds.unique_dataset_id
         JOIN af ON af."IdentifiantCadreAcquisition" = taf.unique_acquisition_framework_id
         JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
         JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
         JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
         LEFT JOIN ref_habitats.habref h ON h.cd_hab = s.cd_hab
         LEFT JOIN ref_geo.l_areas ta ON ta.id_area = s.id_area_attachment
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
         LEFT JOIN ref_nomenclatures.t_nomenclatures n20 ON s.id_nomenclature_valid_status = n20.id_nomenclature;

ALTER TABLE gn_exports.v_export_inpn
    OWNER TO geonatadmin;


