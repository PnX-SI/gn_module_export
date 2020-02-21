# Module export

Module permettant d'ajouter des fonctionnalités d'export à l'application GeoNature.

## Fonctionnalités principales

- Interface administrateur de gestion des exports créés dynamiquement à partir de vues
- Interface utilisateur permettant de réaliser des exports
- API JSON d'interrogation des exports
- Génération automatique planifiée des fichiers des exports
- Export sémantique RDF au format Darwin-SW

# Installation du module

## Configuration

### Email

Le module d'export envoie des emails indiquant que l'export demandé est prêt. Pour cela il est nécessaire de configurer les paramètres email dans la configuration générale de GeoNature (``config/geonature_config.toml``).

La configuration des emails utilise les paramètres définis par Flask_mail. Pour avoir accès à l'ensemble des paramètres se référer à la [documentation complète](https://flask-mail.readthedocs.io/en/latest/).

```
[MAIL_CONFIG]
    MAIL_SERVER = "monserver.mail"
    MAIL_PORT = 465 # Si différent de 465 en SSL
    MAIL_USERNAME = "user@monserver.mail"
    MAIL_PASSWORD = "password"
    MAIL_DEFAULT_SENDER = "user@monserver.mail"
```

### Autres paramètres:
Les autres paramètres concernent les dossiers d'export
* export_schedules_dir : chemin absolu du dossier ou les exports programmés seront déposés lors de la réalisation de la commande gn_exports_run_cron_export

* export_dsw_dir : chemin absolu du dossier ou l'export sémantique au format Darwin-SW sera réalisé
* export_dsw_filename : nom du fichier de l'export sémantique au format turtle (.ttl)

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

- Lancer l'installation du module

```
source backend/venv/bin/activate
geonature install_gn_module /PATH_TO_MODULE/gn_module_export exports
deactivate
```

Pour avoir des exports disponibles, il faut les renseigner dans la table ``gn_exports.t_exports``.

# Administration du module

## Création d'une nouvelle vue en base

Pour créer un nouvel export, il faut au préalable créer une vue dans la base de données correspondante à l'export désiré.

Pour des questions de lisibilité, il est conseillé de créer la vue dans le schéma ``gn_exports``.

## Enregistrer l'export créé dans le module Admin

L'interface d'administration est accessible dans GeoNature via le module ``Admin`` puis ``backoffice GeoNature``.

Dans la rubrique Exports selectionner le menu ``Export`` puis cliquer sur ``Create`` et renseigner les valeurs.

## Associer les roles ayant la permission d'accéder à cet export

Aller sur la page ``Associer roles aux exports``.

Puis créer des associations entre les rôles et l'export en question.

Seul les roles ayant des emails peuvent être associé à un export, exception faite des groupes.

# Documentation swagger d'un export

Par défaut une documentation swagger est générée automatiquement mais il est possible de la surcharger en respectant certaines conventions.

1. Créer un fichier au format OpenAPI décrivant votre export
2. Sauvegarder le fichier ``geonature/external_modules/exports/backend/templates/swagger/api_specification_{id_export}.json``


# Export planifié
Lors de l'installation du module une commande cron est créée. Elle se lance tout les jours à minuit.

```
    0 0 * * * MODULE_EXPORT_HOME/gn_export_cron.sh GN2_HOME # gn_export cron job
```

Cette commande liste des exports planifié dans la table ``gn_exports.t_export_schedules`` et les exécute si besoin.
La fonction considère qu'un export doit être réalisé à partir du moment ou le fichier généré précedemment est plus ancien (en jours) que la fréquence définie.

Il est possible de lancer manuellement cette commande

```
    cd GN2_HOME
    source backend/venv/bin/activate
    geonature gn_exports_run_cron_export
```


# Export RDF au format Darwin-SW

Le module peut génèrer un export RDF au format Darwin-SW des données de la Synthèse de GeoNature.

L'export est accéssible de deux façon : 
 * API
 * commande GeoNature
 
API : 

  `URL_GEONATURE_BACK/exports/semantic_dsw`

    Paramètres : 
        - limit
        - offset
        - champs présent dans la vue  v_exports_synthese_sinp_rdf
        
Commande:
```
    cd GN2_HOME
    source backend/venv/bin/activate
    geonature gn_exports_run_cron_export_dsw --limit 10 --offset=0
```

Les paramètres limit et offset sont optionnels. S'ils ne sont pas spécifiés l'export se fera sur l'ensemble des données

# Autres

CCTP de définition du projet - http://geonature.fr/documents/cctp/2017-10-CCTP-GeoNature-interoperabilite.pdf

A voir aussi : https://www.indigo-datacloud.eu

Ainsi que : https://fr.wikipedia.org/wiki/Syst%C3%A8me_d'information_taxonomique_int%C3%A9gr%C3%A9

Pour le volet Taxonomie, un travail expérimental a été réalisé : https://github.com/PnX-SI/TaxHub/issues/150

# Mise à jour du module

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
cp /home/`whoami`/gn_module_export_old/config/conf_gn_module.toml   /home/`whoami`/gn_module_export/config/conf_gn_module.toml
```

- Relancer la compilation en mettant à jour la configuration

```
cd /home/`whoami`/geonature/backend
source venv/bin/activate
geonature update_module_configuration EXPORTS
```
