=========
CHANGELOG
=========

1.0.4 (unreleased)
------------------

* Amélioration de la vue SINP par défaut (``gn_exports.v_synthese_sinp``) (#70) :

  * Amélioration des performances des jointures comme dans l'export Synthèse, revu dans la version 2.3.0 de GeoNature (https://github.com/PnX-SI/GeoNature/commit/6633de4825c3a57b868bbe284aefdb99a260ced2)
  * Ajout du champs ``nom_valide``, des infos taxonomiques, des cadres d'acquisition, des acteurs des jeux de données dans la vue
  * Amélioration des noms de champs plus lisibles
  * Complément des commentaires des champs
* Ajout de la licence ouverte 2.0 d'Etalab par défaut
* Compléments de la documentation

**🐛 Corrections**

* Correction de petites typos (#71)

1.0.3 (2020-04-24)
------------------

**🐛 Corrections**

* Exports planifiés non horodatés pour qu'ils aient un nom fixe et permanent (#61)
* Affichage des noms des groupes dans la liste des rôles dans le formulaire d'association d'un export à un rôle dans l'Admin du module (#64)
* Ajout d'un test sur le paramètre ``ERROR_MAIL_TO`` de GeoNature pour vérifier qu'il a bien une valeur
* Correction d'un bug lors de l'installation du module (#65)
* Documentation : Compléments mineurs sur la configuration des envois d'email, à paramétrer au niveau de GeoNature avant installation du module

1.0.2 (2020-04-22)
------------------

**🐛 Corrections**

* Correction d'un bug quand l'utilisateur n'a pas d'email

1.0.1 (2020-04-20)
------------------

**🚀 Nouveautés**

* Messages d'erreur envoyés à l'administrateur (``ERROR_MAIL_TO`` de la configuration globale de GeoNature) en plus de l'utilisateur, en cas de dysfonctionnement d'un export (#60)
* Horodatage des exports à la demande (#61, par @DonovanMaillard)
* Compléments de la documentation (README.md)

**🐛 Corrections**

* Correction des données dupliquées dans les exports
* Factorisation et nettoyage du code et généralisation de l'utilisation du paramètre ``export_format_map`` (#53)

1.0.0 (2020-02-21)
------------------

Compatible avec GeoNature 2.3.2.

**🚀 Nouveautés**

* Possibilité de générer automatiquement des exports de manière planifiée

  - Création d'une table ``gn_exports.t_export_schedules`` permettant de lister les exports à générer automatiquement
  - Création d'une fonction Python ``gn_exports_run_cron_export()`` permettant de générer les fichiers des exports planifiées, dans le répertoire ``static/exports/schedules``, accessible en http
  - Création d'un cron à l'installation du module qui va éxecuter le script ``gn_export_cron.sh`` chaque nuit à minuit, éxecutant la fonction python ``gn_exports_run_cron_export()``, qui génère les fichiers des exports planifiés dans la table ``gn_exports.t_export_schedules``

* Export sémantique RDF au format Darwin-SW

  - Création d'une vue spécifique ``gn_exports.v_exports_synthese_sinp_rdf`` pour l'export RDF
  - Mapping des champs de la synthèse avec le format Darwin-SW
  - Création d'une fonction Python ``gn_exports_run_cron_export_dsw()`` permettant de générer les fichiers des exports planifiées, dans le répertoire ``static/exports/dsw``, accessible en http
  - Création d'une API permettant d'interroger la vue ``gn_exports.v_exports_synthese_sinp_rdf`` et de récupérer les données au format Darwin-SW (ttl)

* Utilisation généralisée des nouvelles librairies externalisées de sérialisation (https://github.com/PnX-SI/Utils-Flask-SQLAlchemy et https://github.com/PnX-SI/Utils-Flask-SQLAlchemy-Geo)
* Ajout du format GeoJSON pour les exports

0.2.0 (2019-12-30)
------------------

**🚀 Nouveautés**

* Possibilité de saisir l'adresse email où l'export sera envoyé

**🐛 Corrections**

* Compatibilité GeoNature 2.3.0
* Prise en compte de l'URL de GeoNature dans la doc de l'API (swagger)
* Corrections mineures de l'administration des exports

0.1.0
-----

Première version fonctionelle du module Export de GeoNature

**Fonctionnalités**

* Liste des exports disponibles à partir de la table ``gn_exports.t_exports`` en fonction des droits de l'utilisateur connecté définis dans la table ``gn_exports.cor_exports_roles``
* Module d'administration (Flask-admin) des droits sur les exports gérés dans ``gn_exports.cor_exports_roles``
* Possibilité d'exporter le fichier dans différents formats, avec ou sans géométrie selon la définition des exports
* Génération automatique d'une API et de sa documentation à partir d'un fichier de configuration json (#34)
* Vue SINP fournie par défaut (``gn_export.v_synthese_sinp``)
