Notice d'utilisation de la vue export_inpn
============================================

## Contexte d'utilisation

Cette vue est proposée et conçue pour répondre au besoin d'avoir qu'un seul format de référence pour la transmission des
données depuis une instance **GeoNature** vers les plateformes SINP. Elle réorganise les informations de la synthèse pour les
réassigner aux champs attendus du standard SOTv3, mais elle ne retranscrit pas le contenu initial. En conséquence, elle
n'est utilisable qu'avec les nomenclatures et la structure des GeoNature au standard OccTax_v2

La connexion de cette vue à un élément du module d'export pourra être mise en place pour permettre une transmission des
données au format CSV ou via l'API intégrée de GeoNature. Cette vue est également compatible avec l'outil **GN2PG**. Par
conséquent, la
transmission via cet outil est aussi possible.

## Description

La vue export_inpn récupère toutes les informations nécessaires de la synthèse et des métadonnées pour permettre de
transmettre facilement les données de GeoNature vers l'INPN.

### 1. La récupération des identifiants uniques

Il a été décidé, dans la mesure où la synthèse ne comporte qu'un seul identifiant unique pour une donnée (le second
étant lié à un type de regroupement) que les trois niveaux `Evenement`, `SujetObservation` et `Descriptif` récupèrerait
ce même identifiant pour permettre une traçabilité de la donnée sur ces trois niveaux.

⚠️ Cette mesure devra être corrigée une fois que GeoNature sera passé au SOTv3. Auquel cas chaque donnée devra avoir des
identifiants différents
pour chacun de ces niveaux.

Il peut être envisagé de gérer cette multiplicité des identifiants via des champs/tables supplémentaires, mais il faudra
modifier la requête de la vue en conséquence avant utilisation. Les changements imputés à la base devront être
répercutée
dans la vue en conséquences selon la solution adoptée.

### 2. La récupération des nomenclatures

Les valeurs des différents champs régis par des nomenclatures ne font l'objet que d'une correspondance champ à champ.

Il n'y a pas de prise en compte de l'évolution des nomenclatures dans cette vue entre le standard de GeoNature et le standard SOT v3. Il n'y a pas de transformation de valeur, pourtant nécessaire pour retranscrire la bonne

information au SOTv3. Ainsi les codes récupérés ne sont pas utilisables tels quels dans leur nouvel intitulé. Les

modifications de
valeurs sont laissées à l'interprétation du receveur (PatriNat dans le cas d'une transmission au niveau national). Les
correspondances pouvant être complexes pour certains champs, il a été choisi de ne pas fixer ces associations de valeurs

dans cette vue. Les labels d'origine ont été conservés volontairement pour permettre une meilleure lecture.


Les correspondances entre les deux standards seront fixées une fois GeoNature passé au SOTv3. Il faudra prévoir une
réintégration complète des données depuis les GeoNature pour assurer l'homogénéité entre les bases.


### 3. Les champs xxxx_label

Pour plus de transparence et de lisibilité en cas d'export CSV, les champs `xxxx_label` sont les seuls champs qui n'ont
pas été renommés et qui comportent le libellé de la valeur d'origine présent dans la synthèse. Il est possible de

s'appuyer sur ces champs pour réaliser la retranscription des valeurs des nomenclatures.


### 4. Renseigner la base de production

En amont de la transmission des données, il est possible de renseigner la base de production :
Il suffit de remplacer le `NULL` dans la ligne ```base_production(base) AS (VALUES (NULL::text))```.
Cette valeur est personnalisable, mais il est conseillé qu'il soit fixe et stable au cours des transmissions si possible
conforme à l'appellation dans référentiel organisme.

### 5. La récupération des métadonnées

Les métadonnées sont récupérées depuis les tables du module métadonnées et compilées dans un json compatible avec le
formalisme nécessaire à **gn2pg**.

### 6. Casse des noms de champs

Les noms de champs en sortie sont directement issus du standard SOTv3 pour les champs qui sont récupérés. La

casse doit donc être respectée : il est donc nécessaire d'apposer les doubles quotes quand cela est nécessaire.

### 7. Le niveau de sensibilité

La sensibilité est incluse dans cette vue pour répondre à des besoins autres que l'intégration des données au niveau

national. Dans le cadre d'une intégration au niveau de l'INPN, ces champs ne seront pas utilisés. La sensibilité sera
recalculée en fonction des listes de sensibilité en vigueur.

## Limites

### 1. Une utilisation restreinte au standard Occtax_v2

### ⚠️ATTENTION!!!⚠️ La transmission issue de cette requête n'est pas entièrement fidèle au standard **SOTv3. Elle ne réalise que la redistribution des valeurs dans les différents champs.

> Cette vue peut être intégrée dans un Géonature dont l'environnement correspond encore au format du **standard
OccTax_v2** du SINP. Elle n'est par contre pas compatible avec un Géonature qui a été modifié pour se rapprocher du
> SOTv3.

> Cette vue a été conçue pour récupérer l'ensemble des valeurs nécessaires à une intégration dans l'INPN. Elle ne fait
> pas transcription des valeurs des nomenclatures entre les deux versions du standard, car cela est complexe et sujet à
> discussion.
>
> La transformation des valeurs doit être faite lors de l'intégration par l'organisme receveur. Les valeurs remontées
> par la requête seront toujours à l'ancien standard. Si les données sont intégrées en l'état, cela générera
> potentiellement des incohérences au niveau des nomenclatures qui ont subi de forts changements.
>
> L'utilisation de cette vue dans un environnement hybride risque de générer également des incohérences ou des errreurs
> lors du traitement des données.
> Il est donc important de restreindre strictement l'utilisation de cette vue dans le context qui lui est dédié

### 2. Une seule échelle de validation possible

Cette vue ne permet que de retransmettre le niveau de validation présent dans la synthèse. Le renseignement de la
variable dans la sous requête `params` permettra d'affecter ces valeurs aux champs correspondant à la bonne échelle de
validation. Si la transmission nécessite une redistribution des niveaux de validation pour différentes échelles, il
faudra modifier la vue pour ajouter les sous requêtes nécessaires.

## Dictionnaire de données

| champ                           |      format       |           champ géonature           | nomenclature Occtax_v2 |
|:--------------------------------|:-----------------:|:-----------------------------------:|:----------------------:|
| id_synthese                     |      integer      |             id_synthese             |                        |
| id_perm_sinp                    |       uuid        |           unique_id_sinp            |                        |
| "idSinpSujetObs"                |       uuid        |           unique_id_sinp            |                        |
| "idSinpEvenement"               |       uuid        |           unique_id_sinp            |                        |
| "idSinpDescriptif"              |       uuid        |           unique_id_sinp            |                        |
| "idOrigineSujetObs"             |      varchar      |             id_origine              |                        |
| "idSinpRegroupement"            |       uuid        |         unique_id_sinp_grp          |                        |
| "dateDebut"                     |       date        |              date_min               |                        |
| "dateFin"                       |       date        |              date_max               |                        |
| "heureDebut"                    |       heure       |  date_min::time without time zone   |                        |
| "heureFin"                      |       heure       |  date_max::time without time zone   |                        |
| "cdNom"                         |    code TaxRef    |               cd_nom                |                        |
| "nomCite"                       |      varchar      |              nom_cite               |                        |
| "denombrementMin"               |      entier       |              count_min              |                        |
| "denombrementMax"               |      entier       |              count_max              |                        |
| "altitudeMin"                   |       float       |            altitude_min             |                        |
| "altitudeMax"                   |       float       |            altitude_max             |                        |
| "profondeurMin"                 |       float       |              depth_min              |                        |
| "profondeurMax"                 |       float       |              depth_max              |                        |
| observateur                     |      varchar      |              observers              |                        |
| determinateur                   |      varchar      |             determiner              |                        |
| "echelleValidation"             |   nomenclature    |                  -                  |                        |
| "validateurValRegOuNat"         |      varchar      |              validator              |                        |
| "validateurValProd"             |      varchar      |              validator              |                        |
| "niveauValidationValReg"        |   nomenclature    |           cd_nomenclature           |           ✓            |
| "niveauValidationValProd"       |   nomenclature    |           cd_nomenclature           |           ✓            |
| "niveauValidationValProd_label" |      varchar      |            label_default            |                        |
| "commentaireValidation"         |      varchar      |         validation_comment          |                        |
| "urlPreuveNumerique"            |        url        |            digital_proof            |                        |
| "preuveNonNumerique"            |      varchar      |          non_digital_proof          |                        |
| geometrie                       |        wkt        |            the_geom_4326            |                        |
| cd_geo                          | code_localisation |              area_code              |                        |
| "typeLocalisation"              |   nomenclature    |                  -                  |                        |
| "commentaireEvenement"          |      varchar      |           comment_context           |                        |
| "commentaireDescriptif"         |      varchar      |         comment_description         |                        |
| "idSinpJdd"                     |       uuid        |          unique_dataset_id          |                        |
| "referenceSource"               |      varchar      |          reference_biblio           |                        |
| "cdHab"                         |    code HabRef    |               cd_hab                |                        |
| habitat_label                   |      varchar      |              lb_hab_fr              |                        |
| "nomLocalisation"               |      varchar      |             place_name              |                        |
| "precisionGeometrie"            |       float       |              precision              |                        |
| "natureObjetGeo"                |   nomenclature    |           cd_nomenclature           |           ✓            |
| natureobjetgeo_label            |      varchar      |            label_default            |                        |
| "typeRegroupement"              |   nomenclature    |           cd_nomenclature           |           ✓            |
| typeregroupement_label          |      varchar      |            label_default            |                        |
| "nomRegroupement"               |      varchar      |             grp_method              |                        |
| comportement                    |   nomenclature    |           cd_nomenclature           |           ✓            |
| comportement_label              |      varchar      |            label_default            |                        |
| "indicePresence"                |   nomenclature    |           cd_nomenclature           |           ✓            |
| technique_obs_label             |      varchar      |            label_default            |                        |
| "phaseBiologique"               |   nomenclature    |           cd_nomenclature           |           ✓            |
| statut_biologique_label         |      varchar      |            label_default            |                        |
| "etatBiologique"                |   nomenclature    |           cd_nomenclature           |           ✓            |
| etat_biologique_label           |      varchar      |            label_default            |                        |
| spontaneite                     |   nomenclature    |           cd_nomenclature           |           ✓            |
| naturalite_label                |      varchar      |            label_default            |                        |
| "stadeBiologique"               |   nomenclature    |           cd_nomenclature           |           ✓            |
| stade_vie_label                 |      varchar      |            label_default            |                        |
| sexe                            |   nomenclature    |           cd_nomenclature           |           ✓            |
| sexe_label                      |      varchar      |            label_default            |                        |
| "objetDenombrement"             |   nomenclature    |           cd_nomenclature           |           ✓            |
| objet_denombrement_label        |      varchar      |            label_default            |                        |
| "methodeDenombrement"           |   nomenclature    |           cd_nomenclature           |           ✓            |
| type_denombrement_label         |      varchar      |            label_default            |                        |
| niveau_sensibilite              |   nomenclature    |           cd_nomenclature           |           ✓            |
| niveau_sensibilite_label        |      varchar      |            label_default            |                        |
| "statutObservation"             |   nomenclature    |           cd_nomenclature           |           ✓            |
| statut_observation_label        |      varchar      |            label_default            |                        |
| "statutSource"                  |   nomenclature    |           cd_nomenclature           |           ✓            |
| statut_source_label             |      varchar      |            label_default            |                        |
| methode_determination           |   nomenclature    |           cd_nomenclature           |           ✓            |
| methode_determination_label     |      varchar      |            label_default            |                        |
| "AttributAdditionnel"           |       json        |           additional_data           |                        |
| jdd_data                        |     json_mtd      |                                     |                        |
| ca_data                         |     json_mtd      |                                     |                        |
| derniere_action                 |       date        | meta_update_date / meta_create_date |                        |

---------------------------------------------------------------------------------------------------------------------

## 🚧Perspectives🚧
Certaines évolutions de GeoNature pourront amener à réviser le formalisme de cette vue afin de toujours correspondre au 

standard :
- ### Le passage de GeoNature au standard SOT_v3

    - Une mise à jour de l'environnement GeoNature doit faire l'objet d'une nouvelle vue pour récupérer les informations

      avec la nouvelle structuration de GeoNature quand elle sera disponible.

    - La correspondance des nomenclatures sera directement compatible sans besoin de faire attention à la provenance de
      la donnée.
- ### La gestion de plusieurs échelles de validation
Actuellement un seul niveau de validation est possible sur GeoNature. Il est possible de discriminer l'échelle à 

laquelle il faut l'affecter avec le validateur, mais cela ne constitue pas une manière pérenne et transposable à
toutes les utilisations de Géonature. 