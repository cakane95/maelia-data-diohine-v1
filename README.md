# Instanciation du territoire de Diohine (Sasseme) dans MAELIA

Ce dépôt regroupe les outils, scripts et documents nécessaires à l’instanciation du territoire de Diohine dans la plateforme de simulation MAELIA. Pour cette première version, nous utilisons uniquement les données du village de Sasseme.

## 🎯 Objectif

MAELIA est une plateforme de simulation multi-agents dédiée à la modélisation des systèmes agro-environnementaux. Ce projet vise à organiser les données brutes, les traiter et les structurer dans le format attendu par MAELIA, spécifiquement pour les répertoires `modeleAgricole` et `modeleCommun`.

## 📂 Structure du Dépôt

- **`/data`**: Contient les données brutes (fichiers shapefile, CSV, et autres sources). C'est le point de départ.
- **`/notebooks`**: Contient les notebooks Jupyter (ou scripts R/Python) utilisés pour nettoyer, transformer et formater les données brutes.
- **`/includes_sassemeV1`**: Contient les données finales, prêtes à être intégrées dans MAELIA. C'est le résultat du traitement.
    - `modeleAgricole/`
    - `modeleCommun/`
- **`/docs`**: Regroupe la documentation du projet, les notes et les guides méthodologiques.
- **`/figures`**: Contient les graphiques, cartes et autres figures générées lors de l'analyse et du traitement.
- **`/scripts`**: Contient les scripts pour automatiser les processus de validation ou de traitement.

## 🚀 Démarrage Rapide

Pour commencer à travailler sur le projet, clonez ce dépôt sur votre machine locale :

```bash
git clone [https://github.com/cakane95/maelia-data-diohine-v1.git](https://github.com/cakane95/maelia-data-diohine-v1.git)
cd maelia-data-diohine-V1
```

## Workflow d'Instanciation

Le processus se déroule en plusieurs étapes clés :

**1. Collecte des Données Brutes**

Rassembler toutes les données sources (météo, types de sol, exploitants, îlots, parcelles, etc.) dans le dossier /data.

**2. Traitement et Formatage**

Utiliser les scripts du dossier /notebooks pour traiter les données.

⚠️ Bonnes pratiques à respecter :

- Utiliser le séparateur ';' pour les fichiers CSV.
- Les décimales doivent être des points (.).
- Respecter l'ordre et les intitulés exacts des colonnes attendues par MAELIA.
- Encoder tous les fichiers texte en UTF-8 (sans BOM).
- Ne jamais modifier les fichiers .dbf ou .csv avec Excel, car cela peut corrompre les formats. Privilégier des outils comme R, Python, ou QGIS.

**3. Structuration des Données Finales**

Organiser les fichiers traités dans les sous-dossiers de /includes_SassemeV1.

**4. Validation et Automatisation**

Vérifier la conformité de tous les fichiers d'entrée. Une fois le processus validé, créer des scripts dans `/scripts` pour automatiser les tâches répétitives.

Les détails sur les exigences et les erreurs courantes sont disponibles dans la [Documentation](docs/).

### ☑️ Checklist des Données Finales



### 📂 modeleAgricole/

* **📂 agriculteurs/**

  - [x] `exploitations.csv`

  - [x] `materiel.csv`

* **📂 ilots/**

  * **📂 dansZone/**

    - [x] `ilots.shp`

    - [ ] `parcelles.shp`

* **📂 culture/**

  - [ ] `especesCultivees.csv`

  - [ ] `reglesDeDecision.csv`

  - [ ] `reglesDeDecisionFertilisation.csv`

* **📂 Engrais/**

  - [ ] `Engrais.csv`



### 📂 modeleCommun/

* **📂 meteo/**

  - [x] `polygoneMeteoFrance.shp`

  * **📂 observee/**

    - [x] Fichiers météo par année

* **📂 typesDeSol/**

  - [x] `typeDeSolParZH.shp`

* **📂 date/**

- [ ] `joursParMois.csv`



### 📂 modeleHydrographique/

* **📂 zonesHydrographiques/**

  - [x] `ZH.shp`

---