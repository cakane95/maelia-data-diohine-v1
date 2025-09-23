# Création des Règles de Fertilisation (`reglesDeDecisions_fertilisation.csv`)

## 1. Objectif

Ce document détaille la création du fichier `reglesDeDecisions_fertilisation.csv`. La méthode consiste à adapter un fichier d'exemple pour définir une stratégie de fertilisation de base, unique et identique pour nos 6 ITK.

## 2. Méthodologie

La méthode consiste à adapter un fichier d'exemple. Une **stratégie de fertilisation de base, unique et identique** est définie pour nos 6 ITK. Des valeurs fixes sont assignées aux paramètres clés, et tous les autres paramètres non pertinents sont neutralisés avec la valeur `NA`.

Le fichier final aura 8 colonnes : les 2 colonnes de base (`FERTIALT_NOM_ITK` et la colonne vide) et nos 6 colonnes d'ITK.

## 3. Fichiers en Entrée et en Sortie

* **Fichier en Entrée :** `data/ITK/csv/raw/reglesDeDecisions_fertilisation.csv`
* **Fichier en Sortie :** `includes_sassemeV1/modeleAgricole/culture/reglesDeDecisions_fertilisation.csv`

## 4. Paramètres de Fertilisation Définis

Le tableau suivant détaille les valeurs choisies pour chaque paramètre clé.

| Paramètre | Valeur Choisie | Justification / Note |
| :--- | :--- | :--- |
| `FERTIALT_NOM_ALTERNATIVE` | `fertilisation minerale` | Nom de la stratégie. |
| `FERTIALT_ORDRE_ALTERNATIVE`| `1` | Stratégie prioritaire. |
| `FERTIALT_ORDRE_APPORT` | `1` | Premier et unique apport. |
| `FERTIALT_NOM_PRODUIT` | `NPK` | Type de produit. |
| `FERTIALT_DOSE` | `300` | Dose totale (en kg/ha). |
| `FERTIALT_DOSE_P` | `20` | Dose de Phosphore (P). |
| `FERTIALT_DOSE_K` | `10` | Dose de Potassium (K). |
| `FERTIALT_PROF_WSOL` | `0` | Profondeur. |
| `FERTIALT_AGRIW` | `oui` | |
| `FERTIALT_OUTIL` | `0` | Outil par défaut. |
| `FERTIALT_TPS_TRAVAIL` | **`0.0625`** | Vitesse de travail (en ha/h), convertie depuis 2 jours/ha. |
| `FERTIALT_N_PASSAGES` | `1` | Un seul passage. |
| `FERTIALT_OT_SIMULTANEE` | `NA` | Pas d'opération simultanée. |
| `FERTIALT_N_SOUS_PERIODES` | `1` | Une seule période. |
| `FERTIALT_DEBUT` | **`166`** | Date de début (jour julien pour le 15 juin). |
| `FERTIALT_FIN` | **`242`** | Date de fin (jour julien pour le 30 août). |
| *Toutes les autres lignes* | `NA` | Paramètres non utilisés. |