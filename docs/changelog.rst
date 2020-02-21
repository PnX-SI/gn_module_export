=========
CHANGELOG
=========

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
  - Création d'une fonction Python ``gn_exports_run_cron_export_dsw()`` permettant de générer les fichiers des exports planifiées, dans le répertoire ``static/exports/schedules``, accessible en http

* Utilisation généralisée des nouvelles librairies externalisées de sérialisation (https://github.com/PnX-SI/Utils-Flask-SQLAlchemy et https://github.com/PnX-SI/Utils-Flask-SQLAlchemy-Geo)
* Ajout du format GeoJSON pour les exports

0.2.0 (2019-12-30)
------------------

**🚀 Nouveautés**

* Possibilité de saisir l'adresse email ou l'export sera envoyé

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
