# Création du Fichier des Exploitations Agricoles (`exploitations.csv`)

## 1. Objectif

Ce document décrit la méthodologie pour générer le fichier `exploitations.csv`, une des entrées requises par le module agricole de MAELIA. Ce fichier contient la liste unique de tous les exploitants agricoles et leur type, avec un identifiant standardisé.

## 2. Fichiers Source et Cible

* **Fichier en Entrée :** `data/sols/shapefiles/processed/parcellaire_enrichi.shp`
* **Fichier en Sortie :** `includes_sassemeV1/modeleAgricole/agriculteurs/exploitations.csv`

## 3. Méthodologie

### 3.1. Création de l'Identifiant Exploitant (ID_EXPL)

L'identifiant unique pour chaque exploitant (`ID_EXPL`) est généré en plusieurs étapes.
1.  D'abord, une liste de tous les noms d'exploitants uniques est extraite de la colonne **`'NOM_UTILIS'`**.
2.  Ensuite, un nouvel **identifiant standardisé** est assigné à chaque nom, en suivant le format `'SSM1-XXXX'`, où `XXXX` est un numéro séquentiel sur quatre chiffres (ex: `'SSM1-0001'`, `'SSM1-0002'`, etc.).

### 3.2. Définition du Type d'Exploitant (TYPE_EXPL)

Un type d'exploitant est défini pour chaque agriculteur en se basant sur la colonne **`'UTL_2012'`**. Deux catégories sont créées :
* **`avec_UTL`** : si la valeur dans la colonne `'UTL_2012'` est **supérieure** à 0.
* **`sans_UTL`** : si la valeur dans la colonne `'UTL_2012'` est égale à 0.

## 4. Résultat Final

Le fichier de sortie `exploitations.csv` est une table de correspondance contenant deux colonnes : **`ID_EXPL`** (l'identifiant standardisé nouvellement créé) et **`TYPE_EXPL`**. Chaque ligne correspond à un exploitant unique.

### 5. Création du Fichier Matériel (`materiel.csv`)

Le fichier `materiel.csv` liste les équipements d'irrigation disponibles pour les exploitants. Pour le territoire de Sasseme, il n'y a **pas de matériel d'irrigation** utilisé.

Par conséquent, un fichier `materiel.csv` est créé contenant uniquement la ligne d'en-tête requise par MAELIA, avec la première colonne vide :
`;SIJ (ha/jr);travail (h/jr)`