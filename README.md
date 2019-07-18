# Module export

Module permmant d'ajouter de fonctionnalités d'export à l'application GéoNature

## Fonctionnalités principales
* Interface administrateur de gestion des exports
* Interface utilisateur permettant de réaliser des exports
* API d'intérogation des exports
* Export nocture des exports [TODO]
* Export RDF au format Darwin-SW [TODO]


# Installation du module

## Configuration
### Mail
Le module d'export envoie des mails indiquant que l'export demandé est près. Pour cela il est nécessaire de configurer les paramètres mail dans la configuration générale de GéoNature (`config/geonature_config.toml`).

La configuration des mails utilise les paramètres définis pas Flask_mail. Pour avoir accès à l'ensemble des paramètres se référer à la [documentation complète](https://flask-mail.readthedocs.io/en/latest/).

```
[MAIL_CONFIG]
    MAIL_SERVER = "monserver.mail"
    MAIL_PORT = 465 # Si différent de 465 en SSL
    MAIL_USERNAME = "user@monserver.mail"
    MAIL_PASSWORD = "password"
    MAIL_DEFAULT_SENDER = "user@monserver.mail"
```

## Commande d'installation
```
source backend/venv/bin/activate
geonature install_gn_module /PATH_TO_MODULE/gn_module_export exports
```

Pour avoir des exports disponibles il faut les renseigner au niveau de la base de données dans la table `gn_exports.t_exports`.

# Ajout d'un nouvel export
Pour créer un nouvel export il faut suite les étapes décrites ci dessous

## Créer d'une vue correspondant à l'export désiré.

Pour des questions de lisibilité il est conseillé de créer la vue dans le schéma gn_export

## Enregistrer l'export créé dans l'admin

Aller sur la page : `URL_APLLICATION_BACKEND/nomenclatures/admin/export/`

Cliquer sur create et renseigner les valeurs

## Associer les roles ayant la permission d'accéder à cet export

Aller sur la page : `URL_APLLICATION_BACKEND/nomenclatures/admin/export/corexportsroles/`

Puis créer des association entre les rôles et l'export en question
```
Seul les roles ayant des emails peuvent être associé à un export
```

# Documentation swagger d'un export
Par défaut une documentation swagger est générée automatiquement mais il est possible de la surcharger en respectant certaines conventions.

1. Créer un fichier au format open api dévrivant votre export
2. Sauvegarder le fichier `geonature/external_modules/exports/backend/templates/swagger/api_specification_{id_export}.json`


# Autres
CCTP de définition du projet - http://geonature.fr/documents/cctp/2017-10-CCTP-GeoNature-interoperabilite.pdf
