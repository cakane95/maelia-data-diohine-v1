# Création des Fichiers de Règles de Décision

## 1. Objectif

Ce document décrit la méthodologie pour générer les fichiers `reglesDeDecision.csv` et `reglesDeDecisionFertilisation.csv`. Ces fichiers sont des matrices complexes qui définissent les itinéraires techniques (ITK) en spécifiant les conditions et paramètres pour chaque opération technique (préparation du sol, semis, récolte, etc.).

## 2. Méthodologie

Pour garantir une base de travail cohérente, nous ne partons pas de zéro. La méthode consiste à **modifier les fichiers de règles de décision d'un territoire déjà instancié** pour les adapter aux spécificités de Sasseme.

Le processus se déroule en plusieurs étapes clés, qui seront implémentées dans un notebook Python dédié :
1.  **Chargement** : Le fichier source `reglesDeDecisionsextended.csv` est chargé.
2.  **Simplification de la Structure** : Le nombre de colonnes (ITK) est réduit pour ne conserver que les 6 ITK de base définis pour notre territoire (combinaisons de culture et de précédent cultural).
3.  **Mise à Jour de l'En-tête** : Les 12 premières lignes sont remplies de manière programmatique pour définir les caractéristiques de nos 6 ITK (ID_ESPECE, ID_PREC, etc.).
4.  **Désactivation des Opérations** : Toutes les opérations culturales sont désactivées par défaut.
5.  **Activation et Paramétrage** : Seules les opérations pertinentes pour Sasseme (`PREPA`, `SEMIS`, `RECOLTE`) sont activées et leurs paramètres clés sont renseignés sur la base de dire d'experts.

## 3. Paramétrage des Opérations Techniques

Les valeurs des paramètres pour les opérations `PREPA`, `SEMIS` et `RECOLTE` ont été définies sur la base de dire d'experts et de la littérature.

#### Préparation du Sol (PREPA)

* **Période d'intervention :** L'opération de préparation du sol peut être réalisée entre le **1er mai** (`PREPA_DEBUT` = 121) et le **31 mai** (`PREPA_FIN` = 151).
* **Temps de travail (`PREPA_TEMPS`) :** Le temps de travail a été estimé à **3 jours par hectare**. En considérant une journée de travail de 8 heures, cela a été converti en une vitesse de travail de **0.0417 ha/h**.

#### Semis (SEMIS)

* **Période d'intervention :** La fenêtre de semis est définie entre le **1er juin** (`SEMIS_DEBUT` = 152) et le **30 juin** (`SEMIS_FIN` = 181).
* **Condition de déclenchement (pour l'arachide) :** Le semis pour la culture de l'arachide est déclenché par une condition pluviométrique. Il doit y avoir un cumul de pluie d'au moins **20 mm** sur **1 jour**.
    * `SEMIS_CUMUL_PLUIE` = 20
    * `SEMIS_N_J_CUMUL_PLUIE` = 1

#### Récolte (RECOLTE)

* **Période d'intervention :** La récolte peut être réalisée entre le **15 septembre** (`RECOLTE_DEBUT` = 258) et le **15 octobre** (`RECOLTE_FIN` = 288).
* **Temps de travail (`RECOLTE_TEMPS`) :** Le temps de travail a été estimé à **7 jours par hectare**, soit une vitesse de travail de **0.0179 ha/h**.

## 4. Fichiers Source et Cible

### 4.1. Fichier en Entrée
* **Règles de Décision (Source)** : `data/ITK/csv/raw/reglesDeDecisionsextended.csv`

### 4.2. Fichiers en Sortie
* **Règles de Décision (Sasseme)** : `includes_sassemeV1/modeleAgricole/culture/reglesDeDecision.csv`
* **Règles de Fertilisation (Sasseme)** : `includes_sassemeV1/modeleAgricole/culture/reglesDeDecisionFertilisation.csv`