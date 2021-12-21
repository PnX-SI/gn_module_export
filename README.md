# Module Export

Module permettant d'ajouter des fonctionnalités d'export à l'application GeoNature.

## Fonctionnalités principales

- Interface administrateur de gestion des exports créés dynamiquement à partir de vues dans la base de données de GeoNature
- Interface utilisateur permettant de réaliser des exports sous forme de fichiers (CSV, JSON, GeoJSON, SHP)
- API JSON d'interrogation dynamique et filtrable des exports
- Génération automatique planifiée des fichiers des exports
- Export sémantique RDF au format Darwin-SW

# Installation du module

## Configuration

### Email

Le module d'export envoie des emails indiquant que l'export demandé est prêt. Pour cela il est nécessaire de configurer au préalable les paramètres d'envoi d'emails dans la configuration générale de GeoNature (section ``[MAIL_CONFIG]`` de ``geonature/config/geonature_config.toml``).

La configuration des emails utilise les paramètres définis par Flask_mail. Pour avoir accès à l'ensemble des paramètres se référer à la [documentation complète](https://flask-mail.readthedocs.io/en/latest/).

```
[MAIL_CONFIG]
    MAIL_SERVER = "monserver.mail"
    MAIL_PORT = 465 # Si différent de 465 en SSL
    MAIL_USERNAME = "user@monserver.mail"
    MAIL_PASSWORD = "password"
    MAIL_DEFAULT_SENDER = "user@monserver.mail"
```

### Autres paramètres

Les paramètres du module surcouchables concernent les dossiers d'export et se configurent dans le fichier ``gn_module_export/config/conf_gn_module.toml`` du module Export :

* ``export_schedules_dir`` : chemin absolu du dossier où les exports programmés seront déposés lors de la réalisation de la commande ``gn_exports_run_cron_export``
* ``export_dsw_dir`` : chemin absolu du dossier où l'export sémantique au format Darwin-SW sera réalisé
* ``export_dsw_filename`` : nom du fichier de l'export sémantique au format turtle (``.ttl``)
* ``export_web_url`` : URL des fichiers exportés à la demande par les utilisateurs
* ``expose_dsw_api`` : Indique si la route d'appel à l'API du Darwin SW est active ou non. Par défaut la route n'est pas activée.

Voir le fichier ``gn_module_export/config/conf_gn_module.toml.example`` d'exemple des paramètres.

Si vous modifiez les valeurs par défaut de ces paramètres en les renseignant dans le fichier ``gn_module_export/config/conf_gn_module.toml``, vous devez lancer une commande pour appliquer les modifications des paramètres : 

```
cd /home/`whoami`/geonature/backend
source venv/bin/activate
geonature update_module_configuration EXPORTS
```

## Commande d'installation

- Téléchargez le module dans ``/home/<myuser>/``, en remplacant ``X.Y.Z`` par la version souhaitée

```
wget https://github.com/PnX-SI/gn_module_export/archive/X.Y.Z.zip
unzip X.Y.Z.zip
rm X.Y.Z.zip
```

- Renommez le répertoire du module

```
mv /home/`whoami`/gn_module_export-X.Y.Z /home/`whoami`/gn_module_export
```

- Lancez l'installation du module

```
source geonature/backend/venv/bin/activate
geonature install_gn_module /PATH_TO_MODULE/gn_module_export exports
deactivate
```

## Mise à jour du module

- Suivez les éventuelles notes de la version que vous souhaitez installer

- Téléchargez la nouvelle version du module

```
wget https://github.com/PnX-SI/gn_module_export/archive/X.Y.Z.zip
unzip X.Y.Z.zip
rm X.Y.Z.zip
```

- Renommez l'ancien et le nouveau répertoire

```
mv /home/`whoami`/gn_module_export /home/`whoami`/gn_module_export_old
mv /home/`whoami`/gn_module_export-X.Y.Z /home/`whoami`/gn_module_export
```

- Rapatriez le fichier de configuration

```
cp /home/`whoami`/gn_module_export_old/config/conf_gn_module.toml  /home/`whoami`/gn_module_export/config/conf_gn_module.toml
```

- Rapatriez aussi vos éventuelles surcouches des documentations Swagger des exports depuis le dossier ``/home/`whoami`/gn_module_export_old/backend/templates/swagger/``.

- Relancez la compilation en mettant à jour la configuration

```
cd /home/`whoami`/geonature/backend
source venv/bin/activate
geonature update_module_configuration EXPORTS
```

# Administration du module

## Création d'une nouvelle vue dans la BDD

Pour créer un nouvel export, il faut au préalable créer une vue dans la base de données correspondante à l'export souhaité.

Pour des questions de lisibilité, il est conseillé de créer la vue dans le schéma ``gn_exports``.

Par défaut, un export public (accessible à tous les utilisateurs ayant accès au module Export d'une instance GeoNature) est créé basé sur la vue ``gn_exports.v_synthese_sinp``, contenant toutes les données présentes dans la Synthèse. Il est possible de limiter les données dans cet exeport (en ajoutant des critères dans la clause WHERE de la vue ``gn_exports.v_synthese_sinp``), de supprimer cet export ou de le limiter à certains utilisateurs uniquement.

Les fichiers exportés sont automatiquement supprimés 15 jours après avoir été générés (durée configurable avec le paramètre ``nb_days_keep_file``).

## Enregistrer l'export créé dans le module Admin

L'interface d'administration est accessible dans GeoNature via le module ``Admin`` puis ``Backoffice GeoNature``.

Dans la rubrique Exports selectionner le menu ``Export`` puis cliquer sur ``Create`` et renseigner les valeurs.

## Associer les roles ayant la permission d'accéder à cet export

Si l'export est défini comme "Public" (``gn_exports.t_exports.public = True``), alors tous les utilisateurs pourront y accéder. Sinon il est possible de définir les rôles (utilisateurs ou groupes) qui peuvent accéder à un export.

Aller sur la page ``Associer roles aux exports``.

Puis créer des associations entre les rôles et l'export en question.

Seul les roles ayant des emails peuvent être associé à un export, exception faite des groupes.

Par défaut, lors de l'installation du module, un export public contenant toutes les données de la synthèse est créé (basé sur la vue ``gn_exports.v_synthese_sinp``). Il est donc accessible à tous les utilisateurs pouvant accéder au module Export. Libre à vous de le modifier ou le supprimer.

Chaque fois qu'un export de fichier est réalisé depuis le module, celui-ci est tracé dans la table ``gn_exports.t_exports_logs``.

# API JSON et documentation Swagger d'un export

Pour chaque export créé, une API JSON filtrable est automatiquement créée à l'adresse ``<URL_GeoNature>/api/exports/api/<id_export>``. Comme les exports fichiers, l'API JSON de chaque export est accessible à tous (``Public = True``) ou limitée à certains rôles. 

Par défaut une documentation Swagger est générée automatiquement pour chaque export à l'adresse ``<URL_GeoNature>/api/exports/swagger/<id_export>``, permettant de tester chaque API et d'identifier leurs filtres. 

Il est possible de surcharger la documentation Swagger de chaque API en respectant certaines conventions : 

1. Créer un fichier au format OpenAPI décrivant votre export
2. Sauvegarder le fichier ``geonature/external_modules/exports/backend/templates/swagger/api_specification_{id_export}.json``

# Export planifié

Lors de l'installation du module, une commande cron est créée. Elle se lance tous les jours à minuit.

```
0 0 * * * MODULE_EXPORT_HOME/gn_export_cron.sh GN2_HOME # gn_export cron job
```

Cette commande liste des exports planifiés dans la table ``gn_exports.t_export_schedules`` et les exécute si besoin.

La fonction considère qu'un export doit être réalisé à partir du moment où le fichier généré précedemment est plus ancien (en jours) que la fréquence définie (dans ``gn_exports.t_export_schedules.frequency``).

Il est possible de lancer manuellement cette commande.

```
cd GN2_HOME
source backend/venv/bin/activate
geonature exports gn_exports_run_cron_export
```

Par défaut, le fichier généré par un export planifié est disponible à l'adresse : ``<URL_GEONATURE>/api/static/exports/schedules/Nom_Export.Format``.

# URL des fichiers

Par défaut les fichiers sont servis par le serveur web Gunicorn qui a un timeout limité qui s'applique aussi au téléchargement des fichiers. Si le fichier à télécharger est volumineux, il est possible que le téléchargement soit coupé avant de terminer au bout de quelques minutes. Même si il est possible de le reprendre pour le terminer (éventuellement en plusieurs fois), il est aussi possible (et conseillé) de servir les fichiers des exports par Apache (non concerné par un timeout pour le téléchargement), plutôt que par Gunicorn.

Pour cela, modifier la configuration Apache de GeoNature et ajouter un alias vers le dossier où sont générés les fichiers exportés :

```
sudo nano /etc/apache2/sites-available/geonature.conf
```

Ajoutez ces lignes au milieu de la configuration Apache de GeoNature (en adaptant le chemin absolu et le nom de l'alias comme vous le souhaitez). Exemple pour les exports planifiés : 

```
Alias "/exportschedules" "/home/myuser/geonature/backend/static/exports/schedules"
<Directory "/home/myuser/geonature/backend/static/exports/schedules">
   AllowOverride None
   Require all granted
</Directory>
```

Pour les fichiers générés à la demande par les utilisateurs :

```
Alias "/exportfiles" "/home/myuser/geonature/backend/static/exports/usr_generated"
<Directory "/home/myuser/geonature/backend/static/exports/usr_generated">
   AllowOverride None
   Require all granted
</Directory>
```

Renseignez le paramètre ``export_web_url`` en cohérence dans le fichier ``config/conf_gn_module.toml`` du module (``export_web_url=<URL_GEONATURE>/exportfiles`` dans cet exemple).

Rechargez la configuration Apache pour prendre en compte les modifications :

```
sudo /etc/init.d/apache2 reload
```

Dans cet exemple les fichiers des exports planifiés seront accessibles à l'adresse ``<URL_GEONATURE>/exportschedules/Nom_Export.Format``. Le chemin ``/exportschedules/`` est adaptable bien entendu au niveau de l'alias de la configuration Apache. Les fichiers des exports générés à la demande par les utilisateurs seront disponibles à l'adresse ``<URL_GEONATURE>/exportfiles/Date_Nom_Export.Format``

Une autre solution plus globale serait de compléter la configuration Apache de GeoNature pour que l'ensemble de son répertoire ``backend/static`` soit servi en mode fichier par Apache. Voir http://docs.geonature.fr/conf-apache.html.

# Export RDF au format sémantique Darwin-SW

Le module peut génèrer un export RDF au format Darwin-SW des données de la Synthèse de GeoNature.

Cet export est basé sur la vue ``gn_exports.v_exports_synthese_sinp_rdf`` dont il ne faut pas modifier la structure. Il est cependant possible d'en filtrer le contenu en y ajoutant des conditions dans un ``WHERE`` à la fin de la vue.

L'export est accessible de deux façons :

* API (si ``expose_dsw_api = true``)
* Fichier .ttl généré par une commande GeoNature
 
API : 

  ``<URL_GEONATURE>/api/exports/semantic_dsw``

    Paramètres : 
        - limit
        - offset
        - champs présents dans la vue v_exports_synthese_sinp_rdf
        
Fichier .ttl, généré par la commande :

```
cd GN2_HOME
source backend/venv/bin/activate
geonature exports gn_exports_run_cron_export_dsw --limit 10 --offset=0
```

Le fichier est alors disponible à l'adresse <URL_GEONATURE>/api/static/exports/dsw/export_dsw.ttl.

Les paramètres ``limit`` et ``offset`` sont optionnels. S'ils ne sont pas spécifiés l'export se fera sur l'ensemble des données.

### Standard Darwin-SW

Le format Darwin-SW est un vocabulaire RDF conçu par le TDWG. Il repose sur le langage Web Ontology Language (OWL) qui est un langage de représentation des connaissances.

_"Darwin-SW (DSW) is an RDF vocabulary designed to complement the Biodiversity Information Standards (TDWG) Darwin Core Standard. DSW is based on a model derived from a community consensus about the relationships among the main Darwin Core classes. DSW creates two new classes to accommodate important aspects of its model that are not currently part of Darwin Core: a class of Individual Organisms and a class of Tokens, which are forms of evidence.  DSW uses Web Ontology Language (OWL) to make assertions about the classes in its model and to define object properties that are used to link instances of those classes. A goal in the creation of DSW was to facilitate consistent markup of biodiversity data so that RDF graphs created by different providers could be easily merged.  Accordingly, DSW provides a mechanism for testing whether its terms are being used in a manner consistent with its model. Two transitive object properties enable the creation of simple SPARQL queries that can be used to discover new information about linked resources whose metadata are generated by different providers. The Individual Organism class enables semantic linking of biodiversity resources to vocabularies outside of TDWG that deal with observations and ecological phenomena."_ (Source : http://www.semantic-web-journal.net/system/files/swj635.pdf)

Exemple de graphe représentant l'export d'une seule donnée de la synthèse selon le standard Darwin-SW avec un lien vers TAXREF-LD :

![Exemple de graph pour une donnée](docs/semantic/sample_semantic_dsw.png)

Bibliographie : 

 * Darwin-SW : http://www.semantic-web-journal.net/system/files/swj635.pdf
 * Adding Biodiversity Datasets from Argentinian Patagonia to the Web of Data: http://ceur-ws.org/Vol-1933/paper-6.pdf
 * A Model to Represent Nomenclatural and Taxonomic Information as Linked Data. Application to the French Taxonomic Register, TAXREF : http://ceur-ws.org/Vol-1933/paper-3.pdf

# Autres

* CCTP de définition du projet : http://geonature.fr/documents/cctp/2017-10-CCTP-GeoNature-interoperabilite.pdf
* Biodiversité et opendata (Présentation d'Olivier Rovellotti au Forum TIC 2018) : https://geonature.fr/documents/2018-06-forum-tic-biodiversite-opendata-rovellotti.pdf
* Biodiversité et linked data (Présentation d'Amandine Sahl au Forum TIC 2018) : https://geonature.fr/documents/2018-06-forum-tic-biodiversite-linkeddata-sahl.pdf
* OPENDATA ET BIODIVERSITÉ (Pourquoi et comment publier ses données de biodiversité en opendata ?) : https://geonature.fr/documents/2019-04-biodiversite-opendata.pdf

A voir aussi : 

* https://www.indigo-datacloud.eu
* https://fr.wikipedia.org/wiki/Syst%C3%A8me_d'information_taxonomique_int%C3%A9gr%C3%A9

Pour le volet Taxonomie, un travail expérimental a été réalisé : https://github.com/PnX-SI/TaxHub/issues/150
