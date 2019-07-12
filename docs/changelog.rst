=========
CHANGELOG
=========

0.1.0 (unreleased)
------------------

Première version fonctionelle du module Export de GeoNature

**Fonctionnalités**

* Liste des exports disponibles à partir de la table ``gn_exports.t_exports`` en fonction des droits de l'utilisateur connecté 
définis dans la table ``gn_exports.cor_exports_roles``
* Module d'administration (Flask-admin) des droits sur les exports gérés dans ``gn_exports.cor_exports_roles``
* Possibilité d'exporter le fichier dans différents formats, avec ou sans géométrie selon la définition des exports
* Génération automatique d'une API et de sa documentation à partir des commentaires des champs dans la BDD
* Vue SINP fournie par défaut (``gn_export.v_synthese_sinp``)
