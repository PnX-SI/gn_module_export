1.6.0 (unreleased)
------------------

Nécessite la version 2.13.0 de GeoNature

**🚀 Nouveautés**

- Compatibilité avec GeoNature 2.13.0 et la refonte des permissions, en définissant les permissions disponibles du module (#183)
- L'export "Synthese SINP", fourni par défaut lors de l'installation du module, n'est plus défini comme "public" pour les nouvelles installations, suite à l'ouverture sans authentification de l'API des exports publics (#184)

1.5.0 (2023-06-07) - Workshop 2023
----------------------------------

**🚀 Nouveautés**

* Correction des performances de génération de gros fichiers en les construisant par blocs de lignes (#110, #132, #95, par @mvergez, @joelclems, @VicentCauchois, @bouttier)
* Centralisation et factorisation des fonctions de génération de fichiers dans les sous-modules [Utils-Flask-SQLAlchemy](https://github.com/PnX-SI/Utils-Flask-SQLAlchemy) et [Utils-Flask-SQLAlchemy-Geo](https://github.com/PnX-SI/Utils-Flask-SQLAlchemy-Geo) (#143, par @joelclems, @mvergez, @VincentCauchois, @bouttier)
* Suppression du mécanisme interne d'envoi d'emails quand la génération d'un export à la demande est terminé, au profit du mécanisme de notifications intégré à GeoNature (#127, par @amandine-sahl)
* Possibilité de customiser l'email envoyé lorsqu'un fichier d'export est généré, grace au mécanisme de notification dont les messages sont définis dans la BDD et modifiables dans le module "Admin" (#59, par @amandine-sahl)
* Utilisation de Celery pour traiter les taches asynchrones de génération des fichiers exportés
* Ajout d'une tache Celery Beat lancée automatiquement chaque nuit, pour supprimer les fichiers de plus de 15 jours (#126, par @Pierre-Narcisi)
* Ajout d'un token à chaque utilisateur ou groupe pour chaque export auquel il a accès (table `gn_exports.cor_exports_roles.token`), permettant d'accéder à l'API sans devoir utiliser un login et mot de passe (#131, par @TheoLechemia, @andriacap, @ch-cbna)
* Suppression du champ permettant de renseigner un email lors de la demande de téléchargement d'un export (#170, par @amandine-sahl)
* Révision, simplification et correction des permissions du module (#154, par @TheoLechemia, @ch-cna)
* Simplification de l'association de rôles aux exports dans le module "Admin" en associant ceux-ci directement depuis le formulaire d'édition d'un export (#78, par @andriacap)
* Les exports définis comme "Public" ont désormais leur API accessible de manière ouverte sans authentification
* Suppression de la table `gn_exports.t_exports_logs` traçant les exports (#136, par @amandine-sahl)
* Ajout du champ `gn_exports.t_exports.view_pk_column` permettant de spécifier la colonne d'unicité des vues d'exports (#149, par @amandine-sahl)
* Mise en place d'une Github action pour lancer automatiquement les tests (#130 et #134, par @mvergez)
* Ajout de tests automatisés (#141, par @JulienCorny, @Pierre-Narcisi, @TheoLechemia, @amandine-sahl, @joelclems, @andriacap, @mvergez, @bouttier, @ch-cbna, @jpm-cbna)
* Suppression des paramètres `export_schedules_dir`, `usr_generated_dirname` et `export_web_url` (#155, par @amandine-sahl)
* Le format SHP est supprimé des exports au profit du GPKG, plus performant et maintenable (#174, par @amandine-sahl)
* Nettoyage et refactoring global du code (#138, par @amandine-sahl, @Julien-Corny, @bouttier)
* Nettoyage des fichiers git (#146, par @jpm-cbna)
* Remplacement de l'utilisation de `as_dict` au profit de marshmallow (#172, par @amandine-sahl)
* Correction de la vue complémentaire (`gn_exports.v_synthese_sinp_dee`) au format DEE (#159, par @jpm-cbna)

**🐛 Corrections**

* Correction de l'installation (#133, par @ch-cbna)
* Correction de l'URL de l'API listant les exports (#102, par @TheoLechemia)
* La liste des groupes et utilisateurs que l'on peut associer à un export ne contient désormais que les utilisateurs ayant accès à GeoNature (#75, par @andriacap)

**⚠️ Notes de version**

Si vous mettez à jour le module :

* Les exports définis comme "Public" ont désormais leur API accessible de manière ouverte sans authentification. C'est donc le cas votre export SINP, si vous aviez gardé cet export public créé par défaut lors de l'installation du module
* Si vous les aviez surcouché, supprimez les paramètres `export_schedules_dir`, `usr_generated_dirname` et `export_web_url` de la configuration du module
* La table listant les exports réalisés (`gn_exports.t_exports_logs`) sera automatiquement supprimée
* Les exports au format SHP seront convertis automatiquement en export au format GPKG. Attention si vous aviez des exports planifiés au format SHP, leur URL changera avec le même nom mais avec l'extension `.gpkg`.
* Les droits d'accès au module et aux exports ne se basent désormais plus que sur l'action R (read), et non plus E (export).
* Une colomne permettant d'indiquer le champ d'unicité des vues a été ajoutée dans la table des exports (`gn_exports.t_exports.view_pk_column`). Pour les exports existants, cette colonne est automatiquement remplie avec la valeur de la première colonne des vues exports. Vous pouvez vérifier ou modifier ce champs pour les exports existants.
* Si vous installez le module sur une version 2.12 de GeoNature, il est possible que vous deviez lancer les commandes suivantes afin de mettre à jour les sous-modules Python, avant la mise à jour du module :
  ```sh
  source ~/geonature/backend/venv/bin/activate
  pip install utils-flask-sqlalchemy==0.3.4
  pip install utils-flask-sqlalchemy-geo==0.2.8
  pip install pypnusershub==1.6.7
  ```

1.4.0 (2023-03-27)
==================

Nécessite la version 2.12.0 (ou plus) de GeoNature.

**🚀 Nouveautés**

* Compatibilité avec Angular version 15, mis à jour dans la version
    2.12.0 de GeoNature
* Utilisation de la configuration dynamique (ne nécessitant plus de
    rebuilder le frontend à chaque modification de la configuration du
    module)
* Centralisation de la configuration du module dans le dossier de
    configuration de GeoNature
* Répercussion de la réorganisation des dossiers dans GeoNature. Les
    exports sont désormais stockés dans
    `geonature/backend/media/exports`
* Répercussion de la refactorisation des permissions réalisée dans
    GeoNature 2.12.0
* Le cron lançant automatiquement la tache de génération des exports
    planifiés a été remplacée par un tache Celery Beat, installée
    automatiquement avec le module (#125)
* La commande `gn_exports_run_cron_export` est
    remplacée par `generate` (#125)
* La commande `gn_exports_run_cron_export_dsw` est
    remplacée par `generate-dsw` (#125)
* Le script `gn_export_cron.sh` a été supprimé (#125)
* Compatibilité avec SQLAlchemy 1.4 et Flask-SQLAlchemy 1.4

**🐛 Corrections**

* Ajout du paramètre `MODULE_URL` dans le schéma de configuration du
    module
* Suppression de l'usage de `MODULE_URL` dans la configuration du
    module (https://github.com/PnX-SI/GeoNature/issues/2165)
* Suppression du logger fileHandler. Celui-ci utilisait le paramètre
    `ROOT_DIR` et n'était pas compatible avec Docker

**⚠️ Notes de version**

* Le dossier de stockage des exports a été modifié de
    `geonature/backend/static/exports/` à
    `geonature/backend/media/exports/`. La configuration Apache fournie
    avec GeoNature 2.12 sert directement le dossier `media` sans passer
    par gunicorn. Si vous aviez modifié votre configuration
    spécifiquement pour le module d'export, il est recommandé de retirer
    cette partie spécifique au profit de la configuration générique de
    GeoNature.
* Si vous aviez mis en place un cron système pour générer les exports
    planifiés (dans `/etc/cron/geonature` ou autre), vous
    pouvez le supprimer car ils sont désormais générés automatiquement
    avec Celery Beat.

1.3.0 (2022-11-02)
==================

Nécessite la version 2.10.0 (ou plus) de GeoNature.

**🚀 Nouveautés**

* Compatibilité avec Angular version 12, mis à jour dans la version
    2.10.0 de GeoNature (#111)
* Packaging du module
* Gestion de la base de données avec Alembic
* Ajout d'un paramètre d'ordonnancement à la documentation Swagger
    (`orderby=nom_col[ASC|DESC]`). Ce paramètre est utile lors des
    appels à l'API pour récupérer les données, il faut cependant que la
    colonne de tri pointe vers des valeurs uniques (#101).
* Révision de la vue `gn_exports.v_synthese_sinp_dee` pour ne plus
    utiliser la table `gn_sensitivity.cor_sensitivity_synthese`
    (supprimée dans GeoNature 2.10.0)
* Le cron générant les exports planifiés chaque nuit n'est plus mis
    en place automatiquement lors de l'installation du module. Libre à
    chacun de le mettre en place.

**🐛 Corrections Notes de version**

Après la procédure classique de mise à jour du module, il faut :

* Exécuter le script SQL de mise à jour
    `data/migrations/1.2.8to1.3.0.sql`
* Exécuter la commande suivante afin d'indiquer à Alembic l'état de
    votre base de données :

```sh
cd
source geonature/backend/venv/bin/activate
geonature db stamp c2d02e345a06
deactivate
```

1.2.8 (2022-01-13)
==================

Nécessite la version 2.9 de GeoNature. Non compatible avec les versions
2.10 et supérieures de GeoNature.

**🐛 Corrections**

* Compatibilité avec la version 2.9.0 de GeoNature
* Sécurisation de l'administration des exports
* Correction de l'URL générée par défaut pour l'envoi des emails des
    fichiers exportés

1.2.7 (2021-12-21)
==================

Nécessite la version 2.8.0 (ou plus) de GeoNature

**🚀 Nouveautés**

* Suite aux évolutions des commandes de GeoNature, les commandes du
    module sont désormais accessibles via la commande
    `geonature exports` suivie de la commande de l'action :

```sh
gn_exports_run_cron_export      # Lance les exports planifiés
gn_exports_run_cron_export_dsw  # Export des données de la synthese au format Darwin-SW
```

**🐛 Corrections**

* Correction du conflit de permissions entre rôle et organisme (#108)

1.2.6 (2021-10-08)
==================

Nécessite la version 2.8.0 (ou plus) de GeoNature

**🚀 Nouveautés**

* Compatibilité avec Marshmallow 3 / GeoNature 2.8.0
* Ajout des ID dans la liste des exports (#103)

1.2.5 (2021-07-30)
==================

**🐛 Corrections**

* Compatibilité avec GeoNature 2.7.x (#100)
* Suppression des exports avec cascade sur les tables `cor_roles` et
    `schedules` (#93)

**⚠️ Notes de version**

* Si vous mettez à jour le module, exécutez le script SQL de mise à
    jour `data/migrations/1.2.4to1.2.5.sql`

1.2.4 (2021-01-05)
==================

**🐛 Corrections**

* Ajout d'un test de chargement de la configuration du module (#90)

1.2.3 (2020-12-22)
==================

**🐛 Corrections**

* Correction du nom du paramètre `expose_dsw_api` dans le fichier
    `config/conf_schema_toml.py` (#90)

1.2.2 (2020-12-18)
==================

**🚀 Nouveautés**

* Ajout d'un paramètre `expose_dsw_api` qui permet d'activer ou non
    la route publique d'export en Sémantique Darwin Core. (Inactif par
    défaut)

**🐛 Corrections**

* Le formulaire d'export conserve l'email de l'utilisateur connecté

1.2.1 (2020-11-18)
==================

Nécessite la version 2.5.4 de GeoNature.

**🚀 Nouveautés**

* Récupération de l'email de l'utilisateur connecté dans le
    formulaire de téléchargement (#50)

1.2.0 (2020-11-13)
==================

Nécessite la version 2.5.0 minimum de GeoNature, du fait de la mise à
jour du standard Occurrences de taxon du SINP en version 2.0

**🚀 Nouveautés**

* Compatibilité avec GeoNature 2.5 et +
* Révision de la vue d'export fournie par défaut
    (`gn_exports.v_synthese_sinp`) suite à la mise de la Synthèse en
    version 2.0 du standard Occurrences de taxon du SINP et passage des
    noms de champs en minusucule (#82)
* Révision de la vue permettant de faire les exports sémantiques au
    format RDF (`gn_exports.v_exports_synthese_sinp_rdf`) suite à la
    mise de la Synthèse en version 2.0 du standard Occurrences de taxon
    du SINP (#82)
* Création d'une vue complémentaire
    (`gn_exports.v_synthese_sinp_dee`) au format DEE (Données
    Elementaires d'Echange) du SINP (#80 par @alainlaupinmnhn)
* Ajout d'un paramètre `csv_separator` permettant de définir le
    séparateur de colonnes des fichiers CSV (`;` par défaut)

**⚠️ Notes de version**

* Si vous mettez à jour le module, exécutez le script SQL de mise à
    jour `data/migrations/1.1.0to1.2.0.sql`, notamment pour mettre à
    jour la vue par défaut `gn_exports.v_synthese_sinp` avec les champs
    de la version 2.0 du standard Occurrences de taxon du SINP. Ou
    adaptez cette vue comme vous le souhaitez.

1.1.0 (2020-07-02)
==================

Compatible avec GeoNature 2.4 minimum.

**🚀 Nouveautés**

* Ajout des exports au format GeoPackage (#54)
* Modification du répertoire des exports générés à la demande par les
    utilisateurs et utilisation d'un paramètre `export_web_url` pour
    surcoucher l'URL des fichiers exportés (#73)
* Ajout d'une rubrique dans la documentation sur la configuration des
    URL des fichiers exportés

**🐛 Corrections**

* Création du fichier `geonature/var/log/gn_export/cron.log` lors de
    l'installation du module
* Corrections de la prise en compte de la fréquence (en jours) pour
    les exports planifiés
* Correction d'un bug de la commande des exports planifiés
    (`IndexError: tuple index out of range`)

**⚠️ Notes de version**

* Les fichiers générés par les exports utilisateurs ne se situent plus
    dans `geonature/backend/static/exports` mais dans
    `geonature/backend/static/exports/usr_generated`. Vous pouvez donc
    supprimer les éventuels fichiers situés à la racine de
    `geonature/backend/static/exports`.
* Si il n'existe pas déjà, créer le répertoire
    `geonature/var/log/gn_export`.
* Par défaut, les fichiers exportés sont servis par Gunicorn qui a un
    timeout qui coupe le téléchargement des fichiers volumineux après
    quelques minutes. Il est conseillé de modifier la configuration
    Apache de GeoNature pour servir les fichiers exportés par Apache et
    avec des URL simplifiées. Voir la documentation
    (https://github.com/PnX-SI/gn_module_export/blob/master/README.md#url-des-fichiers).

1.0.4 (2020-05-14)
==================

**🚀 Nouveautés**

* Amélioration de la vue SINP par défaut
    (`gn_exports.v_synthese_sinp`) (#70) :
    * Amélioration des performances des jointures comme dans l'export
        Synthèse, revu dans la version 2.3.0 de GeoNature
        (https://github.com/PnX-SI/GeoNature/commit/6633de4825c3a57b868bbe284aefdb99a260ced2)
    * Ajout du champs `nom_valide`, des infos taxonomiques, des cadres
        d'acquisition, des acteurs des jeux de données dans la vue
    * Amélioration des noms de champs plus lisibles
    * Complément des commentaires des champs
* Ajout de la licence ouverte 2.0 d'Etalab par défaut
* Compléments de la documentation (Export public par défaut,
    Suppression automatique des fichiers, Fichiers des exports planifiés
    servis par Apache au lieu de Gunicorn - #73)

**🐛 Corrections**

* Correction de la suppression automatique des fichiers exportés avec
    Python 3.5
* Correction de petites typos (#71)

**⚠️ Notes de version**

* Si vous mettez à jour le module, exécutez le script SQL de mise à
    jour `data/migrations/1.0.3to1.0.4.sql` pour ajouter la licence
    ouverte 2.0 et améliorer la vue SINP par défaut
    (`gn_exports.v_synthese_sinp`)

1.0.3 (2020-04-24)
==================

**🐛 Corrections**

* Exports planifiés non horodatés pour qu'ils aient un nom fixe et
    permanent (#61)
* Affichage des noms des groupes dans la liste des rôles dans le
    formulaire d'association d'un export à un rôle dans l'Admin du
    module (#64)
* Ajout d'un test sur le paramètre `ERROR_MAIL_TO` de GeoNature pour
    vérifier qu'il a bien une valeur
* Correction d'un bug lors de l'installation du module (#65)
* Documentation : Compléments mineurs sur la configuration des envois
    d'email, à paramétrer au niveau de GeoNature avant installation du
    module

1.0.2 (2020-04-22)
==================

**🐛 Corrections**

* Correction d'un bug quand l'utilisateur n'a pas d'email

1.0.1 (2020-04-20)
==================

**🚀 Nouveautés**

* Messages d'erreur envoyés à l'administrateur (`ERROR_MAIL_TO` de
    la configuration globale de GeoNature) en plus de l'utilisateur, en
    cas de dysfonctionnement d'un export (#60)
* Horodatage des exports à la demande (#61, par @DonovanMaillard)
* Compléments de la documentation (README.md)

**🐛 Corrections**

* Correction des données dupliquées dans les exports
* Factorisation et nettoyage du code et généralisation de
    l'utilisation du paramètre `export_format_map` (#53)

1.0.0 (2020-02-21)
==================

Compatible avec GeoNature 2.3.2.

**🚀 Nouveautés**

* Possibilité de générer automatiquement des exports de manière
    planifiée
    * Création d'une table `gn_exports.t_export_schedules` permettant
        de lister les exports à générer automatiquement
    * Création d'une fonction Python `gn_exports_run_cron_export()`
        permettant de générer les fichiers des exports planifiées, dans
        le répertoire `static/exports/schedules`, accessible en http
    * Création d'un cron à l'installation du module qui va éxecuter
        le script `gn_export_cron.sh` chaque nuit à minuit, éxecutant la
        fonction python `gn_exports_run_cron_export()`, qui génère les
        fichiers des exports planifiés dans la table
        `gn_exports.t_export_schedules`
* Export sémantique RDF au format Darwin-SW
    * Création d'une vue spécifique
        `gn_exports.v_exports_synthese_sinp_rdf` pour l'export RDF
    * Mapping des champs de la synthèse avec le format Darwin-SW
    * Création d'une fonction Python
        `gn_exports_run_cron_export_dsw()` permettant de générer les
        fichiers des exports planifiées, dans le répertoire
        `static/exports/dsw`, accessible en http
    * Création d'une API permettant d'interroger la vue
        `gn_exports.v_exports_synthese_sinp_rdf` et de récupérer les
        données au format Darwin-SW (ttl)
* Utilisation généralisée des nouvelles librairies externalisées de
    sérialisation (https://github.com/PnX-SI/Utils-Flask-SQLAlchemy et
    https://github.com/PnX-SI/Utils-Flask-SQLAlchemy-Geo)
* Ajout du format GeoJSON pour les exports

0.2.0 (2019-12-30)
==================

**🚀 Nouveautés**

* Possibilité de saisir l'adresse email où l'export sera envoyé

**🐛 Corrections**

* Compatibilité GeoNature 2.3.0
* Prise en compte de l'URL de GeoNature dans la doc de l'API
    (swagger)
* Corrections mineures de l'administration des exports

0.1.0
=====

Première version fonctionelle du module Export de GeoNature

**Fonctionnalités**

* Liste des exports disponibles à partir de la table
    `gn_exports.t_exports` en fonction des droits de l'utilisateur
    connecté définis dans la table `gn_exports.cor_exports_roles`
* Module d'administration (Flask-admin) des droits sur les exports
    gérés dans `gn_exports.cor_exports_roles`
* Possibilité d'exporter le fichier dans différents formats, avec ou
    sans géométrie selon la définition des exports
* Génération automatique d'une API et de sa documentation à partir
    d'un fichier de configuration json (#34)
* Vue SINP fournie par défaut (`gn_export.v_synthese_sinp`)
