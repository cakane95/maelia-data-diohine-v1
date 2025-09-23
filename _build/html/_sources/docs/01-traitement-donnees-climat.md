# Données climatiques brutes – Tour à flux de SOB

## 1. Origine et période des données

Les données analysées proviennent de la tour à flux installée à Niakhar (station SOB), fournies par Olivier Roupsard (CIRAD).  
Elles couvrent la période de **2018 à 2024** et sont enregistrées toutes les **30 minutes** par une instrumentation automatisée multi-capteurs.

---

## 2. Description générale du fichier

- **Nom du fichier source :** `donnees_station_SOB.xlsx`  
- **Format :** Fichier Excel structuré manuellement avec en-têtes multiples  
- **Objectif :** Préparer ces données pour un usage dans MAELIA au format journalier

**Remarque :** La première colonne (sans nom) sert uniquement d’aide visuelle dans le fichier source et est ignorée lors du traitement.

---

## 3. Structure du fichier

| Ligne | Contenu | À utiliser |
|-------|---------|------------|
| 1 à 8 | Métadonnées (instruments, logiciel, qualité, etc.) | Non |
| 9     | Libellés lisibles (ex. Ta (°C), PREC (mm hh-1)) | Non |
| 10    | Noms techniques des colonnes | Oui |
| 11+   | Données toutes les 30 minutes | Oui |

---

## 4. Colonnes clés

| Colonne technique              | Description                                 | Unité       |
|-------------------------------|---------------------------------------------|-------------|
| TIME_START                    | Horodatage de début de mesure               | YYYYMMDDhhmm |
| Air_Temperature_at_2_m        | Température de l'air à 2 mètres             | °C           |
| Precipitation                 | Précipitations toutes les 30 min (×2)       | mm/h         |
| Net_radiation_1               | Rayonnement net instantané                  | W/m²         |
| Relative_Humidity             | Humidité relative                           | %            |
| Wind_Speed                    | Vitesse du vent                             | m/s          |

---

## 5. Traitement prévu pour MAELIA

| Colonne MAELIA | Source technique | Traitement appliqué |
| :--- | :--- | :--- |
| **DATE** | `TIME_START` | Extraction de la date (format **JJ/MM/AAAA**) |
| **RRmm** | `Precipitation` | Somme journalière après correction |
| **Tmin / Tmax** | `Air_Temperature_at_2_m` | Min / max journaliers |
| **RGI** | `Net_radiation_1` | Somme des conversions 30 min (MJ/m²/j).<br>*Note : La variable RGI dans MAELIA correspond ici au **rayonnement net journalier** et non au rayonnement solaire global.* |
| **ETP** | Calculée | Formule journalière Penman-Monteith FAO |
| **ID\_PDG** | Ajouté par le script | **Ajouté par le script avec une valeur fixe de 1** (station centrale unique) |

---

## 6. Justification des agrégations

- **Précipitations :** cumulées sur 24 h après correction (voir section 8)
- **Températures :** min et max extraits des mesures 30 min
- **Rayonnement net :** converti en énergie reçue toutes les 30 min (MJ/m²/30min), puis agrégé
- **ETP :** calculée à partir des moyennes journalières selon Penman-Monteith

---

## 7. Étapes de traitement

1. Chargement des données à partir de la ligne 10
2. Conversion de `TIME_START` en objet `datetime`
3. Correction de la précipitation (division par 2)
4. Conversion de `Net_radiation_1` en MJ/m²/30min, puis cumul par jour
5. Agrégation journalière des variables climatiques
6. Calcul de l’ETP journalière avec la formule FAO-56 Penman-Monteith
7. Export des résultats au format MAELIA (`DATE`, `RRmm`, `Tmin`, `Tmax`, `ETP`, `RGI`)

---

## 8. Remarque importante sur les précipitations

Les précipitations ont été initialement exprimées en **mm/h**, issues de mesures toutes les 30 minutes **multipliées par 2**.

**Correction appliquée :**
- Chaque valeur a été **divisée par 2** pour retrouver le cumul réel sur 30 minutes
- Ensuite, la **somme journalière** est calculée pour obtenir `RRmm`

---

## 9. Conversion du rayonnement net

Le rayonnement net est fourni en **W/m²** (puissance instantanée). Pour obtenir l’énergie reçue pendant chaque intervalle de 30 minutes, on applique :

\[
\text{Net\_radiation\_1 (MJ/m²/30min)} = \text{Net\_radiation_1 (W/m²)} \times \frac{1800}{1\,000\,000} = \text{Net\_radiation_1} \times 0.0018
\]

Ces valeurs sont ensuite **sommées par jour** pour produire `RGI` (rayonnement global intégré en MJ/m²/jour).

---

## 10. Calcul de l’ETP avec la formule Penman-Monteith (FAO-56)

L’évapotranspiration potentielle journalière est estimée selon la formule de Penman-Monteith présentée dans le guide FAO-56 et reprise dans la littérature francophone (voir référence ci-dessous).

\[
ET_0 = \frac{0.408 \cdot \Delta \cdot R_n + \gamma \cdot \frac{900}{T + 273} \cdot u_2 \cdot (e_s - e_a)}{\Delta + \gamma (1 + 0.34 \cdot u_2)}
\]

### Paramètres utilisés :

| Symbole | Description                                  | Unité       |
|---------|----------------------------------------------|-------------|
| \( R_n \)   | Rayonnement net journalier                | MJ/m²/jour  |
| \( T \)     | Température moyenne journalière           | °C          |
| \( u_2 \)   | Vitesse du vent à 2 m                     | m/s         |
| \( e_s \)   | Pression de vapeur saturante              | kPa         |
| \( e_a \)   | Pression de vapeur réelle (via RH)        | kPa         |
| \( \Delta \)| Pente de la courbe de saturation          | kPa/°C      |
| \( \gamma \)| Constante psychrométrique                 | kPa/°C      |

> Cette formule est appliquée **à partir de moyennes et cumuls journaliers**. Elle ne nécessite pas d’adaptation au pas de temps car tous les termes sont agrégés avant calcul.

---

## 11. Références

- Djikou, T. (2006). *Estimation de l'évapotranspiration potentielle dans le bassin du Haut Bani (Mali) à partir des données météorologiques.*  
  Mémoire de Master, Université de Ouagadougou – AMMA-CATCH.  
  [https://amma-catch.osug.fr/IMG/pdf/memoire_djikou_06.pdf](https://amma-catch.osug.fr/IMG/pdf/memoire_djikou_06.pdf)

- Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998).  
  *Crop evapotranspiration – Guidelines for computing crop water requirements – FAO Irrigation and Drainage Paper 56.* FAO, Rome.

---

Ce document sera mis à jour si des modifications interviennent dans la méthode de traitement.