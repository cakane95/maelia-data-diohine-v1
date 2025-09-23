# Introduction

Ce livre interactif détaille, étape par étape, le processus d'instanciation du territoire de Diohine (village de Sasseme) pour la plateforme de simulation MAELIA.

MAELIA est une plateforme de simulation multi-agents dédiée à la modélisation des systèmes agro-environnementaux. Ce projet vise à collecter et/ou organiser les données brutes, les traiter, et les structurer dans le format attendu par MAELIA, spécifiquement pour les répertoires `modeleAgricole`, `modeleCommun`, et `modeleHydrographique`.

Ce livre regroupe les outils, scripts et documents nécessaires pour passer des données brutes aux fichiers finaux requis par le modèle. L'objectif est de fournir des données prêtes à l'emploi et de garantir la transparence et la reproductibilité de la méthodologie.

Le résultat de ce travail est une arborescence de fichiers prête à l'emploi pour MAELIA. Vous pouvez télécharger la version la plus récente de ces données via le lien ci-dessous.

```{warning}
Le fichier `especesCultivees.csv` n'est pas inclus dans ce zip.
```

[**Télécharger les données finales (.zip)**](/_static/downloads/includes_sassemeV1-latest.zip)


## Périmètre de l'Instanciation

Cette première version de l'instanciation se concentre sur un périmètre précis :

* **Acteurs :** **44 agriculteurs** résidant dans le quartier de Sasseme.
* **Parcellaire de base :** **420 parcelles** initiales exploitées par ces agriculteurs.
* **Enrichissement agro-écologique :** Le parcellaire a été enrichi en intégrant les zones d'influence des arbres (*Faidherbia Albida*), ce qui a porté le nombre total d'unités spatiales distinctes à **749 polygones**.
* **Classification des sols :** Ces unités ont été classifiées en **8 types de sols** en croisant trois critères : le type de sol local (`dior`, `dekk`, `dekkMbel`), le type de champ (`case` ou `brousse`) et la présence d'arbres.
* **Systèmes de culture :** Le modèle intègre deux cultures principales, l'**arachide** et le **mil**, ainsi que la **jachère**. La gestion de ces cultures est définie par **6 itinéraires techniques (ITK)** de base qui tiennent compte du précédent cultural.
* **Opérations techniques :** Seules **3 opérations techniques** principales sont modélisées : la préparation du sol (`PREPA`), le semis (`SEMIS`) et la récolte (`RECOLTE`).
* **Fertilisation :** Une seule stratégie de fertilisation est considérée, basée sur un apport d'engrais minéral de type **NPK**.
* **Données climatiques :** Les simulations s'appuient sur des données météo couvrant la période de **2018 à 2024**.

## Structure du Livre

Ce livre est organisé pour refléter la structure modulaire de la plateforme MAELIA. Vous trouverez trois parties principales, chacune correspondant à un module du modèle :

* **Le Module Commun** contient la documentation et l'implémentation pour les fichiers des dossiers `meteo`, `typesDeSol` et `date`.
* **Le Module Agricole** regroupe le travail sur les fichiers des dossiers `agriculteurs`, `ilots`, `Engrais` et `culture`.
* **Le Module Hydrographique** détaille la création des fichiers du dossier `zonesHydrographiques`.