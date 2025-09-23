# Création du Fichier des Îlots (`ilots.shp`)

## 1. Objectif

Ce document décrit la méthodologie pour générer le fichier `ilots.shp`. Ce fichier représente l'**îlot cultural**, l'unité de base de la gestion agricole dans MAELIA, et le relie aux exploitants et aux types de sol.

## 2. Fichiers Source et Cible

### 2.1. Fichiers en Entrée
* `data/sols/shapefiles/processed/parcellaire_enrichi.shp`
* `includes_sassemeV1/modeleAgricole/agriculteurs/exploitations.csv`
* `data/sols/csv/processed/donnees_typesDeSol_enrichies.csv`

### 2.2. Fichier en Sortie
* `includes_sassemeV1/modeleAgricole/ilots/dansZone/ilots.shp`

## 3. Description des Variables et Choix Méthodologiques

Le fichier `ilots.shp` final doit contenir 12 attributs pour chaque polygone. La table ci-dessous détaille l'origine et le traitement pour chaque variable.

| Variable | Description | Origine / Traitement |
| :--- | :--- | :--- |
| `ID_ILOT` | Identifiant unique de l'îlot. | Créé en assignant un numéro séquentiel à chaque **polygone du parcellaire d'entrée**. |
| `ID_EXPL` | Identifiant de l'exploitant. | Obtenu par jointure avec `exploitations.csv` via le nom de l'exploitant. |
| `ID_SOL` | Identifiant de l'unité de sol. | Obtenu par jointure avec la table de synthèse via la `ZONE_PEDO`. |
| `ID_ZH` | Identifiant de la Zone Hydrographique. | Obtenu par jointure avec la table de synthèse via la `ZONE_PEDO`. |
| `CARACT_IRR`| Caractère irrigué (Oui/Non). | Valeur fixe **'N'** (Non) pour l'ensemble des îlots. |
| `MATERIEL` | ID du matériel d'irrigation. | **Null**, car pas d'irrigation. |
| `LISTE_EQUIS`| ID des équipements de prélèvement. | **Null**, car pas d'irrigation. |
| `PENTE_MOY` | Pente moyenne (%). | **0**, en considérant le relief plat de la zone d'étude. |
| `PENTE_SWAT`| Pente pour le modèle SWAT (%). | **0**, en considérant le relief plat de la zone d'étude. |
| `EQU_0` | Équipement d'irrigation prioritaire. | **Null**, car pas d'irrigation. |
| `EQU_1` | Équipement d'irrigation secondaire. | **Null**, car pas d'irrigation. |
| `EQU_2` | Équipement d'irrigation tertiaire. | **Null**, car pas d'irrigation. |