=========
CHANGELOG
=========


0.2.0 (2019-12-30)
------------------

**🚀 Nouveautés**

* Possibilité de saisir l'adresse email ou l'export sera envoyé

**🐛 Corrections**

* Compatibilité GeoNature 2.3.0



0.1.0
-----

Première version fonctionelle du module Export de GeoNature

**Fonctionnalités**

* Liste des exports disponibles à partir de la table ``gn_exports.t_exports`` en fonction des droits de l'utilisateur connecté définis dans la table ``gn_exports.cor_exports_roles``
* Module d'administration (Flask-admin) des droits sur les exports gérés dans ``gn_exports.cor_exports_roles``
* Possibilité d'exporter le fichier dans différents formats, avec ou sans géométrie selon la définition des exports
* Génération automatique d'une API et de sa documentation à partir d'un fichier de configuration json (#34)
* Vue SINP fournie par défaut (``gn_export.v_synthese_sinp``)
