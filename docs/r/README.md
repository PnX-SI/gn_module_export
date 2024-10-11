# Utilisation des données d'export dans les analyses R


## Récupérer les données du module d'export via R

Le fichier `gn2_get_export_api_data.R` offre des fonctions qui permettent de récupérer les données d'une api du modèle d'export.

Il repose sur la librairie `httr2`.



### Utilisation

Au préalable il faut installer le paquet `httr2` : `install.packages("httr2")`

```R
source("gn2_get_export_api_data.R")  

#  Paramètres
gn2_token <- "34c9eeb80a54336c60e3fd68cbf715e7"
gn2_export_id <- 165
gn2_url <- "https://URL_GN2/api/exports/api"


#  Récupération des données 
all_data <- get_gn_export_data(gn2_url, gn2_export_id, gn2_token)
```