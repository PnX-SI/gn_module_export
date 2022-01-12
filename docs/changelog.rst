=========
CHANGELOG
=========

1.2.8 (unreeased)
------------------

Nécessite la version 2.9.0 (ou plus) de GeoNature

**🐛 Corrections**

* Sécurisation de l'administration des exports
* Correction de l'URL générée par défaut pour l'envoi des emails des fichiers exportés

1.2.7 (2021-12-21)
------------------

Nécessite la version 2.8.0 (ou plus) de GeoNature

**🚀 Nouveautés**

* Suite aux évolutions des commandes de GeoNature, les commandes du module sont désormais accessibles via la commande ``geonature exports`` suivie de la commande de l'action :

::

   gn_exports_run_cron_export      # Lance les exports planifiés
   gn_exports_run_cron_export_dsw  # Export des données de la synthese au format Darwin-SW
   
**🐛 Corrections**

* Correction du conflit de permissions entre rôle et organisme (#108)

1.2.6 (2021-10-08)
------------------

Nécessite la version 2.8.0 (ou plus) de GeoNature

**🚀 Nouveautés**

* Compatibilité avec Marshmallow 3 / GeoNature 2.8.0
* Ajout des ID dans la liste des exports (#103)

1.2.5 (2021-07-30)
------------------

**🐛 Corrections**

* Compatibilité avec GeoNature 2.7.x (#100)
* Suppression des exports avec cascade sur les tables ``cor_roles`` et ``schedules`` (#93)

**⚠️ Notes de version**

* Si vous mettez à jour le module, exécutez le script SQL de mise à jour ``data/migrations/1.2.4to1.2.5.sql``

1.2.4 (2021-01-05)
------------------

**🐛 Corrections**

* Ajout d'un test de chargement de la configuration du module (#90)

1.2.3 (2020-12-22)
------------------

**🐛 Corrections**

* Correction du nom du paramètre ``expose_dsw_api`` dans le fichier ``config/conf_schema_toml.py`` (#90)

1.2.2 (2020-12-18)
------------------

**🚀 Nouveautés**

* Ajout d'un paramètre ``expose_dsw_api`` qui permet d'activer ou non la route publique d'export en Sémantique Darwin Core. (Inactif par défaut)

**🐛 Corrections**

* Le formulaire d'export conserve l'email de l'utilisateur connecté

1.2.1 (2020-11-18)
------------------

Nécessite la version 2.5.4 de GeoNature.

**🚀 Nouveautés**

* Récupération de l'email de l'utilisateur connecté dans le formulaire de téléchargement (#50)

1.2.0 (2020-11-13)
------------------

Nécessite la version 2.5.0 minimum de GeoNature, du fait de la mise à jour du standard Occurrences de taxon du SINP en version 2.0

**🚀 Nouveautés**

* Compatibilité avec GeoNature 2.5 et +
* Révision de la vue d'export fournie par défaut (``gn_exports.v_synthese_sinp``) suite à la mise de la Synthèse en version 2.0 du standard Occurrences de taxon du SINP et passage des noms de champs en minusucule (#82)
* Révision de la vue permettant de faire les exports sémantiques au format RDF (``gn_exports.v_exports_synthese_sinp_rdf``) suite à la mise de la Synthèse en version 2.0 du standard Occurrences de taxon du SINP (#82)
* Création d'une vue complémentaire (``gn_exports.v_synthese_sinp_dee``) au format DEE (Données Elementaires d'Echange) du SINP (#80 par @alainlaupinmnhn)
* Ajout d'un paramètre ``csv_separator`` permettant de définir le séparateur de colonnes des fichiers CSV (``;`` par défaut)

**⚠️ Notes de version**

* Si vous mettez à jour le module, exécutez le script SQL de mise à jour ``data/migrations/1.1.0to1.2.0.sql``, notamment pour mettre à jour la vue par défaut ``gn_exports.v_synthese_sinp`` avec les champs de la version 2.0 du standard Occurrences de taxon du SINP. Ou adaptez cette vue comme vous le souhaitez.

1.1.0 (2020-07-02)
------------------

Compatible avec GeoNature 2.4 minimum.

**🚀 Nouveautés**

* Ajout des exports au format GeoPackage (#54)
* Modification du répertoire des exports générés à la demande par les utilisateurs et utilisation d'un paramètre ``export_web_url`` pour surcoucher l'URL des fichiers exportés (#73)
* Ajout d'une rubrique dans la documentation sur la configuration des URL des fichiers exportés

**🐛 Corrections**

* Création du fichier ``geonature/var/log/gn_export/cron.log`` lors de l'installation du module
* Corrections de la prise en compte de la fréquence (en jours) pour les exports planifiés
* Correction d'un bug de la commande des exports planifiés (``IndexError: tuple index out of range``)

**⚠️ Notes de version**

* Les fichiers générés par les exports utilisateurs ne se situent plus dans ``geonature/backend/static/exports`` mais dans ``geonature/backend/static/exports/usr_generated``. Vous pouvez donc supprimer les éventuels fichiers situés à la racine de ``geonature/backend/static/exports``.
* Si il n'existe pas déjà, créer le répertoire ``geonature/var/log/gn_export``.
* Par défaut, les fichiers exportés sont servis par Gunicorn qui a un timeout qui coupe le téléchargement des fichiers volumineux après quelques minutes. Il est conseillé de modifier la configuration Apache de GeoNature pour servir les fichiers exportés par Apache et avec des URL simplifiées. Voir la documentation (https://github.com/PnX-SI/gn_module_export/blob/master/README.md#url-des-fichiers).

1.0.4 (2020-05-14)
------------------

**🚀 Nouveautés**

* Amélioration de la vue SINP par défaut (``gn_exports.v_synthese_sinp``) (#70) :

  * Amélioration des performances des jointures comme dans l'export Synthèse, revu dans la version 2.3.0 de GeoNature (https://github.com/PnX-SI/GeoNature/commit/6633de4825c3a57b868bbe284aefdb99a260ced2)
  * Ajout du champs ``nom_valide``, des infos taxonomiques, des cadres d'acquisition, des acteurs des jeux de données dans la vue
  * Amélioration des noms de champs plus lisibles
  * Complément des commentaires des champs
* Ajout de la licence ouverte 2.0 d'Etalab par défaut
* Compléments de la documentation (Export public par défaut, Suppression automatique des fichiers, Fichiers des exports planifiés servis par Apache au lieu de Gunicorn - #73)

**🐛 Corrections**

* Correction de la suppression automatique des fichiers exportés avec Python 3.5
* Correction de petites typos (#71)

**⚠️ Notes de version**

* Si vous mettez à jour le module, exécutez le script SQL de mise à jour ``data/migrations/1.0.3to1.0.4.sql`` pour ajouter la licence ouverte 2.0 et améliorer la vue SINP par défaut (``gn_exports.v_synthese_sinp``)

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
