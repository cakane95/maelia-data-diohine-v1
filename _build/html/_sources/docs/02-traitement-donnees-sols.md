# Méthodologie de Caractérisation des Sols pour l'Instanciation MAELIA

## Création du fichier `typeDeSolParZH.shp` pour le territoire de Sasseme

---

### 1. Contexte et Objectif

Dans la plateforme MAELIA, le modèle de culture AqYield s'appuie sur les caractéristiques des sols pour simuler, à un pas de temps journalier, le développement des cultures. Ces simulations intègrent les interactions dynamiques entre le sol, les conditions climatiques et les itinéraires techniques (ITK) appliqués.

L'objectif de ce document est de décrire la méthodologie employée pour produire le fichier `typeDeSolParZH.shp`, une couche d'information géographique qui caractérise les différents types de sols du territoire étudié et qui sert d'entrée directe pour le modèle.

---

### 2. Classification des Unités de Sol

Pour représenter l'hétérogénéité agro-écologique du territoire, nous avons défini des unités typologiques basées sur la combinaison de trois critères distincts :

* **Le type de sol** : `Dior` (dr), `Deck` (dk) ou `Deck-Mbel` (dkmb).
* **Le type de champ** : champ de case (cc) ou champ de brousse (cb).
* **La présence d'arbres** : avec (arbr) ou sans (sans_arbr).

En raison des données disponibles pour la version actuelle, nous avons consolidé cette typologie en **8 types d'îlots** fonctionnels :
1.  `dior_cb_avec_arbr`
2.  `dior_cb_sans_arbr`
3.  `dior_cc_avec_arbr`
4.  `dior_cc_sans_arbr`
5.  `dekk_cb_avec_arbr`
6.  `dekk_cb_sans_arbr`
7.  `dekk/mbel_cb_avec_arbr`
8.  `dekk/mbel_cb_sans_arbr`

### 2.1. Origine et Description du Parcellaire Enrichi

Le fichier de base utilisé est `Parcellaire_Arbre_Carbone.shp`. Il s'agit d'une couche d'information géographique enrichie qui intègre l'influence des arbres (*Faidherbia albida*) au sein du parcellaire initial de Sasseme.

Ce traitement géospatial complexe a été réalisé en amont par le géomaticien du projet, **M. Ousmane Faye**. Sa méthodologie a consisté à :
1.  Cartographier les arbres de l'espèce *Faidherbia albida*.
2.  Générer des **zones d'influence (tampons) de 17m de rayon** autour de chaque arbre.
3.  **Fusionner** les zones d'influence qui se chevauchaient.
4.  Intégrer ces nouvelles zones au parcellaire, en les distinguant via une colonne attributaire (`Arbre` = 1).

Le rôle du notebook **`02a-creation-centroides.ipynb`** n'est donc pas de réaliser ce traitement, mais de lire ce fichier enrichi et de s'assurer que la géométrie de chaque entité est correctement interprétée pour l'étape d'échantillonnage. Il applique pour cela un **traitement différencié** :
* Pour les **parcelles classiques** (`Arbre` == 0), il calcule le **centroïde** du polygone.
* Pour les **zones d'influence des arbres** (`Arbre` == 1), il utilise les **coordonnées Long/Lat** de l'arbre d'origine.

Ce processus garantit que chaque point d'échantillonnage final **(voir 3.3)** représente la localisation géographique la plus pertinente.

---

### 3. Étape 1 : Consolidation des Données Pédologiques

La première étape consiste à créer une table de synthèse décrivant les propriétés physico-chimiques de chaque type de sol, conformément aux exigences de MAELIA.

#### 3.1. Sources des Données

Les paramètres ont été compilés à partir d'une revue de plusieurs sources de données :
* Travaux académiques (thèses et publications scientifiques).
* Bases de données géospatiales ouvertes (OpenLandMap, iSDA Africa).
* Données de projets de recherche (Cirad Dataverse).

Chaque valeur dans la table de synthèse finale sera explicitement sourcée.

#### 3.2. Harmonisation Verticale des Horizons

En raison des données disponibles, nous avons modélisé le profil de sol sur une **profondeur de 60 cm**, divisée en **deux horizons** : 0-30 cm et 30-60 cm.

Certaines données sources présentaient des horizons différents (ex: 0-20 cm, 20-50 cm). Pour harmoniser ces informations, une **méthode de calcul pro-rata** a été appliquée pour estimer les valeurs sur nos horizons cibles. Lorsque cette approche n'était pas possible, la valeur la plus représentative a été conservée, et cette approximation est documentée.

#### 3.3. Détermination des Valeurs Représentatives et Tableau de Synthèse

Pour chaque paramètre pédologique (teneur en argile, sable, etc.) issu des bases de données spatialisées, une valeur représentative pour chaque type d'îlot a été calculée en suivant une méthode d'échantillonnage par centroïdes :

1.  **Génération des centroïdes** : Le centroïde (le centre géométrique) de chaque parcelle a été calculé.
2.  **Extraction des valeurs** : La valeur du paramètre a été extraite à l'emplacement exact de chaque centroïde.
3.  **Calcul de la moyenne** : La moyenne de toutes les valeurs extraites pour un même type d'îlot a été calculée. Cette moyenne est considérée comme la valeur représentative pour ce type.

Le résultat de cette étape est un **tableau de synthèse** où chaque ligne représente l'un des 8 types d'îlots et chaque colonne correspond à un paramètre requis par MAELIA pour chaque horizon.

### 3.4. Liste des Variables Requises par MAELIA

La description des sols dans MAELIA nécessite un ensemble de variables pédologiques. Certaines de ces variables sont globales, tandis que d'autres sont renseignées **par couche de sol**, numérotées de 1 à 2 dans notre cas.

**Remarques importantes :**
* Les variables indexées `[1–2]` sont définies pour chaque couche.
* Il est indispensable de connaître le **nombre de couches** présentes pour chaque type de sol.
* L’**épaisseur de chaque couche** est donnée par la variable `P[n]`.
* La **somme des épaisseurs** (`P[n]`) doit être cohérente avec la profondeur totale `PRO`.
* Les couches doivent être renseignées **dans l’ordre**, de la surface vers la profondeur.

Le tableau ci-dessous présente la liste des variables nécessaires à la description des sols pour les simulations.

| Variable | Description |
| :--- | :--- |
| **Identifiants** | |
| `ID_SOL` | Identifiant unique pour chaque type de sol (ex: 1, 2, 3...). |
| `ID_ZH` | Identifiant de la Zone Hydrographique. Fixé à **1** pour l'ensemble du territoire. |
| `STU_DOM`| *Soil Typological Unit* dominante. Identifiant textuel du type de sol. |
| `ZONE_PEDO`| Nom de la zone pédologique (ex: `dior_cb_sans_arbr`, `dekk_cb_sans_arbr`). |
| **Variables Globales** | |
| `PIRM` | Infiltrabilité du sol (mm/h) — capacité d'infiltration de l'eau en surface. |
| `PRO` | Profondeur totale du sol utile (en cm). |
| `CSTRU` | Note experte (entre 0 et 1) représentant la qualité structurale globale du sol. |
| **Variables par Couche** | |
| `P[1–2]` | Profondeur ou épaisseur (en cm) de la couche *n*. |
| `ARG[1–2]` | Teneur en argile (%) dans la couche *n*. |
| `EG[1–2]` | Teneur en éléments grossiers (%) dans la couche *n*. |
| `DAH[1–2]` | Densité apparente (g/cm³) de la couche *n*. |
| `RUPRH[1–2]` | Réserve utile potentielle en eau (mm) de la couche *n*. |
| `KSAT[1–2]` | Conductivité hydraulique à saturation (mm/h) dans la couche *n*. |
| `PH[1–2]` | Valeur du pH (acidité) dans la couche *n*. |
| `CN[1–2]` | Rapport carbone/azote (C/N) dans la couche *n*. |
| `CAL[1–2]` | Teneur en calcaire (%) dans la couche *n*. |
| `MO[1–2]` | Teneur en matière organique (%) dans la couche *n*. |
| `SAB[1–2]` | Teneur en sable (%) dans la couche *n*. |
| `HCC[1–2]` | Humidité volumique à la capacité au champ (%) dans la couche *n*. |
| `HPFP[1–2]` | Humidité volumique au point de flétrissement (%) dans la croche *n*. |

### 3.5. Provenance des Données

La table ci-dessous détaille l'origine de chaque donnée utilisée pour construire les variables requises par MAELIA, organisées par type.

| Variable MAELIA | Sources Principales | Traitement / Auteurs |
| :--- | :--- | :--- |
| **Identifiants** | | |
| `ZONE_PEDO` | 1. `Parcellaire_Arbre_Carbone.shp` <br> 2. `malou_0_30.csv` | Combinaison d'attributs pour créer l'identifiant. <br> *(Sources: O. Faye & Thèse O. Malou)* |
| `ID_ZH` | Dire d'expert | Valeur fixe `'SSM1'` (notebook `02c`). |
| `STU_DOM` | `ZONE_PEDO` | Classification ('sableux'/'argileux') (notebook `02c`). |
| `ID_SOL`| Calculée | Combinaison des identifiants (notebook `02c`). |
| **Variables Globales** | | |
| `PIRM` | Thèse de Waly Faye | Estimations basées sur des hypothèses (notebook `02c`). |
| `PRO` | Hypothèse de modélisation | Valeur fixe `60` cm (notebook `02c`). |
| `CSTRU` | Dire d'expert | Valeur fixe `0.5` (notebook `02c`). |
| **Variables par Couche** | | |
| `P1`, `P2` | Hypothèse de modélisation | Valeurs fixes `30` et `60` cm (notebook `02c`). |
| `ARG1`, `ARG2` | [OpenLandMap](https://zenodo.org/records/15528401) | Extraction par centroïdes (notebook `02b`). |
| `SAB1`, `SAB2` | [OpenLandMap](https://zenodo.org/records/15528413) | Extraction par centroïdes (notebook `02b`). |
| `DAH1`, `DAH2` | [OpenLandMap](https://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/bd.core_iso.11272.2017.g.cm3_m_30m_b0cm..30cm_20200101_20221231_g_epsg.4326_v20250204.tif) | Extraction et correction du facteur d'échelle (**`/100`**). |
| `C1`, `C2` | [OpenLandMap](https://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/oc_iso.10694.1995.wpml_m_30m_b0cm..30cm_20200101_20221231_g_epsg.4326_v20250204.tif) | Extraction, correction d'échelle (**`/10`**), puis conversion en **%**. |
| `MO1`, `MO2` | Calculée | `C % * 1.724` (Facteur de Van Bemmelen). |
| `N1`, `N2` | [iSDA Africa Raster](https://isdasoil.s3.amazonaws.com/soil_data/nitrogen_total/nitrogen_total.tif) | Correction d'échelle (**`/100`**) et harmonisation pro-rata. |
| `CN1`, `CN2` | Calculée | `C (g/kg) / N (g/kg)`. |
| `PH1`, `PH2` | iSDA Africa (API) | Requêtes API et harmonisation pro-rata. |
| `HCC1`, `HCC2` | [Cirad Dataverse](https://doi.org/10.18167/DVN1/SGNSII) | Extraction (fraction), harmonisation pro-rata, puis conversion en **%**. |
| `HPFP1`, `HPFP2`| [Cirad Dataverse](https://doi.org/10.18167/DVN1/SGNSII) | Extraction (fraction), harmonisation pro-rata, puis conversion en **%**. |
| `RUPRH1`, `RUPRH2`| Calculée | `(HCC_fraction - HPFP_fraction) * épaisseur`. |
| `KSAT1`, `KSAT2`| Thèse de Waly Faye | Estimations et répartition par couche (notebook `02c`). |
| `EG1`, `EG2` | Dire d'expert | Valeur fixe `0` (notebook `02c`). |
| `CAL1`, `CAL2` | Dire d'expert | Valeur fixe `0` (notebook `02c`). |
---

### 4. Étape 2 : Spatialisation et Attribution des Propriétés

L'objectif de cette étape est de transcrire les informations de la table de synthèse sur une carte.

1.  **Jointure attributaire** : La table de synthèse est jointe numériquement au parcellaire existant (une couche géographique de polygones représentant les parcelles).
2.  **Attribution des données** : Chaque parcelle se voit ainsi attribuer l'ensemble des caractéristiques pédologiques correspondant à son type.
3.  **Ajout d'un identifiant unique** : Un identifiant unique est assigné à chaque parcelle pour assurer la traçabilité.

---

### 5. Étape 3 : Simplification Géométrique

Afin d'optimiser la visualisation et potentiellement les temps de calcul dans MAELIA, une dernière étape de traitement géométrique est réalisée.

* **Regroupement (Dissolve)** : Les parcelles adjacentes partageant le même type de sol sont fusionnées en un polygone unique plus grand.

---

### 6. Résultat Final

Le produit final de ce traitement est le fichier `typeDeSolParZH.shp`. Il s'agit d'une couche de polygones où chaque entité géographique représente une zone de sol homogène et contient, dans sa table attributaire, l'ensemble des paramètres pédologiques nécessaires à la simulation.