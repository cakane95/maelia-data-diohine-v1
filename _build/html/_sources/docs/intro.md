# Introduction : Instanciation du Territoire de Diohine

Ce document interactif détaille, étape par étape, le processus d'instanciation du territoire de Diohine (village de Sasseme) pour la plateforme de simulation MAELIA. Il regroupe les outils, scripts et documents nécessaires pour passer des données brutes aux fichiers finaux requis par le modèle.

L'objectif de ce livre est de fournir des données prêtes à l'emploi et de garantir la transparence et la reproductibilité de la méthodologie.

---
## 🚀 Données Finales

Le résultat de ce travail est une arborescence de fichiers prête à l'emploi pour MAELIA. Vous pouvez télécharger la version la plus récente de ces données via le lien ci-dessous.

```{warning}
Le fichier `especesCultivees.csv` n'est pas inclus dans ce zip.
```

[**Télécharger les données finales (.zip)**](_static/downloads/includes_sassemeV1-latest.zip)

---

## Périmètre de l'Instanciation

Cette première version de l'instanciation se concentre sur un périmètre précis :

* **Acteurs :** **44 agriculteurs** résidant dans le quartier de Sasseme.
* **Parcellaire de base :** **420 parcelles** initiales exploitées par ces agriculteurs.
* **Enrichissement agro-écologique :** Le parcellaire a été enrichi en intégrant les zones d'influence des arbres (*Faidherbia Albida*), ce qui a porté le nombre total d'unités spatiales distinctes à **749 polygones**.
* **Classification des sols :** Ces unités ont été classifiées en **8 types de sols fonctionnels** en croisant trois critères : le type de sol local (`dior`, `dekk`, `dekkMbel`), le type de champ (`case` ou `brousse`) et la présence d'arbres.
* **Systèmes de culture :** Le modèle intègre deux cultures principales, l'**arachide** et le **mil**, ainsi que la **jachère**.
* **Données climatiques :** Les simulations s'appuient sur des données météo couvrant la période de **2018 à 2024**.

---


## 🎯 Objectif du Projet

MAELIA est une plateforme de simulation multi-agents dédiée à la modélisation des systèmes agro-environnementaux. Ce projet vise à organiser les données brutes, les traiter, et les structurer dans le format attendu par MAELIA, spécifiquement pour les répertoires `modeleAgricole`, `modeleCommun`, et `modeleHydrographique`.

## 📂 Structure du Dépôt

-   **`/data`**: Contient les données brutes (fichiers shapefile, CSV, etc.).
-   **`/notebooks`**: Contient les notebooks Jupyter utilisés pour nettoyer et formater les données.
-   **`/includes_sassemeV1`**: Contient les données finales, prêtes à être intégrées dans MAELIA.
-   **`/docs`**: Regroupe la documentation méthodologique (les pages de ce livre).
-   **`/scripts`**: Contient les scripts utilitaires (zipper, etc.).
-   **`/_static`**: Contient les fichiers statiques comme les images et les fichiers à télécharger pour le livre.

## 📖 Principes Méthodologiques

Le processus général suit plusieurs étapes clés :

**1. Collecte des Données Brutes**
   Rassembler toutes les données sources dans le dossier `/data`.

**2. Traitement et Formatage**
   Utiliser les scripts du dossier `/notebooks` pour traiter les données. Les bonnes pratiques suivantes sont respectées :
   - Séparateur **`;`** pour les fichiers CSV.
   - Décimales avec des points (`.`).
   - Encodage en **UTF-8 (sans BOM)**.
   - Utilisation d'outils comme Python ou R pour la manipulation des fichiers afin d'éviter la corruption par des tableurs.

**3. Structuration des Données Finales**
   Organiser les fichiers traités dans les sous-dossiers de `/includes_sassemeV1`.