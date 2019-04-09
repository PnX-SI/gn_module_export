# gn_module_interoperabilite
Module GeoNature d'interopérabilité

CCTP de définition du projet - http://geonature.fr/documents/cctp/2017-10-CCTP-GeoNature-interoperabilite.pdf

# Installation du module
```
source backend/venv/bin/activate
geonature install_gn_module /PATH_TO_MODULE/gn_module_export exports
```

# Configuration
Pour avoir des exports disponibles il faut les renseigner au niveau de la base de données dans la table `gn_exports.t_exports`.
Pour avoir un exemple se référer aux données du fichier `data/sample.sql`.

