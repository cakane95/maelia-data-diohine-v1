"""
01c-correction-climat-api.py

Script de détection et correction des valeurs aberrantes dans les données
climatiques annuelles (sortie du script 01-traitement-climat.py) en utilisant
l'API NASA POWER (réanalyse satellite/modèle, gratuite, sans clé API).
Auteurs: (conversion script: Aboubakry BA)
Description: Détecte les valeurs physiquement incohérentes (Tmin, Tmax, ETP, RGI)
             et les remplace par les valeurs historiques réelles récupérées via
             l'API NASA POWER pour la position géographique exacte de la station.
             Génère des fichiers {annee}bis_api.csv corrigés + un journal détaillé
             des corrections effectuées (traçabilité).

Version 2 : correction par API externe (NASA POWER)

Dépendance supplémentaire requise : pip install requests
"""

import requests
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import re
import time
import warnings

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


# ============================================================================
# CONSTANTES
# ============================================================================

# ⚠️ À COMPLÉTER OBLIGATOIREMENT avant la première exécution :
# coordonnées GPS exactes de la station météo de Sob/Sasseme
SITE_LATITUDE = 14.5    # ex: 14.xxxx
SITE_LONGITUDE = -16.5167   # ex: -16.xxxx

# Plages de plausibilité physique (identiques à la Version 1, pour la détection)
PLAGES_PLAUSIBILITE = {
    "Tmin": (15, 32),      # °C
    "Tmax": (28, 45),      # °C
    "ETP":  (1, 9),        # mm/jour
    "RGI":  (10, 30),      # MJ/m²/jour
}

VARIABLES_A_VALIDER = list(PLAGES_PLAUSIBILITE.keys())

SEUIL_ALERTE_RRMM = 300        # mm/jour — au-delà, flag d'alerte sans correction

PATTERN_FICHIER_ANNEE = re.compile(r"^(\d{4})\.csv$")

# Formats de date tolérés en entrée (testés dans cet ordre)
FORMATS_DATE_ACCEPTES = ["%d/%m/%Y", "%Y-%m-%d"]

# Constantes FAO-56 (identiques au script 01, pour recalculer l'ETP
# à partir des variables météo brutes fournies par l'API)
GAMMA = 0.0665
CN = 900
CD = 0.34

# Configuration API NASA POWER
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_POWER_PARAMS = "T2M_MAX,T2M_MIN,T2M,RH2M,WS2M,ALLSKY_SFC_SW_DWN"
NASA_POWER_VALEUR_MANQUANTE = -999
NASA_POWER_TIMEOUT = 30        # secondes
NASA_POWER_PAUSE_ENTRE_APPELS = 1  # secondes, pour ne pas saturer l'API

# Mapping variable MAELIA -> colonne API correspondante
MAPPING_VARIABLE_API = {
    "Tmin": "T2M_MIN",
    "Tmax": "T2M_MAX",
    "RGI":  "ALLSKY_SFC_SW_DWN",
    "ETP":  "ETP_API",   # calculée, pas fournie directement par l'API
}


# ============================================================================
# FONCTIONS DE CALCUL ETP (identiques au script 01, adaptées aux noms API)
# ============================================================================
def saturation_vapor_pressure(T):
    """Calcule la pression de vapeur saturante (kPa) à une température donnée (°C)."""
    return 0.6108 * np.exp((17.27 * T) / (T + 237.3))


def delta_svp(T):
    """Calcule la pente de la courbe de pression de vapeur saturante (kPa/°C)."""
    e_s = saturation_vapor_pressure(T)
    return (4098 * e_s) / ((T + 237.3) ** 2)


def etp_penman_monteith_fao56_api(row):
    """
    Calcule l'ETP FAO-56 à partir des variables NASA POWER
    (mêmes constantes/formule que le script 01, pour rester cohérent).

    Args:
        row (pd.Series): Ligne contenant T2M, RH2M, WS2M, ALLSKY_SFC_SW_DWN

    Returns:
        float: ETP en mm/jour, ou NaN si une variable d'entrée manque
    """
    T = row["T2M"]
    RH = row["RH2M"]
    u2 = row["WS2M"]
    Rn = row["ALLSKY_SFC_SW_DWN"]

    if pd.isna(T) or pd.isna(RH) or pd.isna(u2) or pd.isna(Rn):
        return np.nan

    e_s = saturation_vapor_pressure(T)
    e_a = e_s * RH / 100
    delta = delta_svp(T)

    num = 0.408 * delta * Rn + GAMMA * (CN / (T + 273)) * u2 * (e_s - e_a)
    den = delta + GAMMA * (1 + CD * u2)

    return max(0, num / den)


# ============================================================================
# FONCTIONS DE CHARGEMENT (identiques à la Version 1)
# ============================================================================
def lister_fichiers_annuels(dossier):
    """
    Liste les fichiers annuels valides (ex: 2020.csv) dans le dossier.

    Args:
        dossier (Path): Dossier contenant les fichiers annuels

    Returns:
        dict: {annee (int): chemin_fichier (Path)}
    """
    fichiers = {}
    for f in sorted(dossier.glob("*.csv")):
        match = PATTERN_FICHIER_ANNEE.match(f.name)
        if match:
            fichiers[int(match.group(1))] = f
    return fichiers


def charger_fichier_annuel(chemin_fichier):
    """
    Charge un fichier annuel de données climatiques.

    Args:
        chemin_fichier (Path): Chemin vers le fichier {annee}.csv

    Returns:
        pd.DataFrame: DataFrame avec DATE convertie en datetime
    """
    df = pd.read_csv(chemin_fichier, sep=";")

    date_convertie = None
    for fmt in FORMATS_DATE_ACCEPTES:
        try:
            date_convertie = pd.to_datetime(df["DATE"], format=fmt)
            break
        except (ValueError, TypeError):
            continue

    if date_convertie is None:
        raise ValueError(
            f"Format de date non reconnu dans {chemin_fichier.name} "
            f"(formats essayés : {FORMATS_DATE_ACCEPTES})"
        )

    df["DATE"] = date_convertie
    df = df.sort_values("DATE").reset_index(drop=True)
    return df


def charger_toutes_les_annees(dossier):
    """
    Charge l'ensemble des fichiers annuels disponibles.

    Args:
        dossier (Path): Dossier contenant les fichiers annuels

    Returns:
        dict: {annee (int): pd.DataFrame}
    """
    fichiers = lister_fichiers_annuels(dossier)
    print(f"📂 {len(fichiers)} fichier(s) annuel(s) détecté(s) : {sorted(fichiers.keys())}")

    donnees = {}
    for annee, chemin in fichiers.items():
        donnees[annee] = charger_fichier_annuel(chemin)
        print(f"  ✓ {chemin.name} chargé ({len(donnees[annee])} jours)")

    return donnees


# ============================================================================
# FONCTIONS DE DÉTECTION DES ANOMALIES (identiques à la Version 1)
# ============================================================================
def est_hors_plage(valeur, plage):
    """
    Vérifie si une valeur est hors de la plage de plausibilité (ou nulle/manquante).

    Args:
        valeur (float): Valeur à tester
        plage (tuple): (min, max) plage acceptable

    Returns:
        bool: True si la valeur est aberrante
    """
    if pd.isna(valeur):
        return True
    borne_min, borne_max = plage
    return valeur == 0 or valeur < borne_min or valeur > borne_max


def detecter_anomalies(df):
    """
    Détecte les valeurs aberrantes sur les variables climatiques (hors RRmm)
    et les remplace temporairement par NaN.

    Args:
        df (pd.DataFrame): DataFrame annuel brut

    Returns:
        pd.DataFrame: DataFrame avec valeurs aberrantes mises à NaN
    """
    df = df.copy()
    for variable, plage in PLAGES_PLAUSIBILITE.items():
        masque = df[variable].apply(lambda v: est_hors_plage(v, plage))
        nb_anomalies = masque.sum()
        if nb_anomalies > 0:
            print(f"  ⚠️  {variable} : {nb_anomalies} valeur(s) aberrante(s) détectée(s)")
        df.loc[masque, variable] = np.nan
    return df


def detecter_anomalies_rrmm(df):
    """
    Détecte les anomalies spécifiques à la précipitation (RRmm) :
    - valeur négative → aberrant (corrigé localement, pas via API)
    - valeur > seuil d'alerte → signalé uniquement

    Args:
        df (pd.DataFrame): DataFrame annuel

    Returns:
        pd.DataFrame: DataFrame avec RRmm négatif mis à NaN
    """
    df = df.copy()
    masque_negatif = df["RRmm"] < 0
    if masque_negatif.sum() > 0:
        print(f"  ⚠️  RRmm : {masque_negatif.sum()} valeur(s) négative(s) détectée(s)")
    df.loc[masque_negatif, "RRmm"] = np.nan

    masque_extreme = df["RRmm"] > SEUIL_ALERTE_RRMM
    if masque_extreme.sum() > 0:
        print(f"  🔔 RRmm : {masque_extreme.sum()} valeur(s) > {SEUIL_ALERTE_RRMM}mm/jour "
              f"(non corrigées, à vérifier manuellement)")

    return df


# ============================================================================
# FONCTIONS D'INTERROGATION DE L'API NASA POWER
# ============================================================================
def interroger_nasa_power(latitude, longitude, annee):
    """
    Interroge l'API NASA POWER pour récupérer les données climatiques
    journalières d'une année complète, à la position géographique donnée.

    Args:
        latitude (float): Latitude du site
        longitude (float): Longitude du site
        annee (int): Année à interroger

    Returns:
        pd.DataFrame or None: Index = DATE (datetime), colonnes = variables API.
                               None en cas d'échec de la requête.
    """
    params = {
        "parameters": NASA_POWER_PARAMS,
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": f"{annee}0101",
        "end": f"{annee}1231",
        "format": "JSON"
    }

    print(f"  🌐 Requête NASA POWER pour {annee} (lat={latitude}, lon={longitude})...")
    try:
        reponse = requests.get(NASA_POWER_URL, params=params, timeout=NASA_POWER_TIMEOUT)
        reponse.raise_for_status()
        donnees_json = reponse.json()

        parametres = donnees_json["properties"]["parameter"]
        df_api = pd.DataFrame(parametres)
        df_api.index = pd.to_datetime(df_api.index, format="%Y%m%d")
        df_api = df_api.replace(NASA_POWER_VALEUR_MANQUANTE, np.nan)

        # Calcul de l'ETP à partir des variables météo brutes (cohérence FAO-56)
        df_api["ETP_API"] = df_api.apply(etp_penman_monteith_fao56_api, axis=1)

        print(f"  ✓ {len(df_api)} jours récupérés depuis NASA POWER")
        return df_api

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Erreur API NASA POWER pour {annee} : {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"  ❌ Réponse API NASA POWER invalide pour {annee} : {e}")
        return None


# ============================================================================
# FONCTIONS DE CORRECTION
# ============================================================================
def corriger_rrmm(df):
    """
    Corrige les valeurs négatives de précipitation en les remplaçant par 0
    (pas de correction via API pour cette variable, cf. décision méthodologique).

    Args:
        df (pd.DataFrame): DataFrame annuel

    Returns:
        pd.Series: Colonne RRmm corrigée
    """
    return df["RRmm"].fillna(0)


def corriger_avec_api(df_original, df_anomalies, df_api):
    """
    Remplace les valeurs aberrantes (NaN) par les valeurs correspondantes
    issues de l'API NASA POWER pour la même date, et construit le journal
    détaillé des corrections.

    Args:
        df_original (pd.DataFrame): DataFrame brut avant toute modification
        df_anomalies (pd.DataFrame): DataFrame avec anomalies mises à NaN
        df_api (pd.DataFrame or None): Données NASA POWER pour l'année (index = DATE)

    Returns:
        tuple: (pd.DataFrame corrigé au format MAELIA, pd.DataFrame journal des corrections)
    """
    df_corrige = df_anomalies.copy()
    lignes_log = []

    for variable, colonne_api in MAPPING_VARIABLE_API.items():
        manquants = df_corrige[variable].isna()

        for idx in df_corrige.index[manquants]:
            date = df_corrige.loc[idx, "DATE"]
            valeur_originale = df_original.loc[idx, variable]

            valeur_api = None
            if df_api is not None and date in df_api.index:
                valeur_candidate = df_api.loc[date, colonne_api]
                if pd.notna(valeur_candidate):
                    valeur_api = valeur_candidate

            if valeur_api is not None:
                df_corrige.loc[idx, variable] = valeur_api
                lignes_log.append({
                    "DATE": date.strftime("%d/%m/%Y"),
                    "variable": variable,
                    "valeur_originale": valeur_originale,
                    "valeur_corrigee": round(valeur_api, 2),
                    "methode": "API_NASA_POWER"
                })
            else:
                lignes_log.append({
                    "DATE": date.strftime("%d/%m/%Y"),
                    "variable": variable,
                    "valeur_originale": valeur_originale,
                    "valeur_corrigee": None,
                    "methode": "API_indisponible_non_corrige"
                })

    # Correction RRmm (négatifs uniquement, indépendante de l'API)
    avant_rrmm = df_corrige["RRmm"].copy()
    df_corrige["RRmm"] = corriger_rrmm(df_corrige)
    masque_rrmm = avant_rrmm.isna() & df_corrige["RRmm"].notna()
    for idx in df_corrige.index[masque_rrmm]:
        lignes_log.append({
            "DATE": df_corrige.loc[idx, "DATE"].strftime("%d/%m/%Y"),
            "variable": "RRmm",
            "valeur_originale": df_original.loc[idx, "RRmm"],
            "valeur_corrigee": 0,
            "methode": "mise_a_zero_negatif"
        })

    df_log = pd.DataFrame(lignes_log)
    if not df_log.empty:
        df_log = df_log.sort_values(["DATE", "variable"]).reset_index(drop=True)

    return df_corrige, df_log


# ============================================================================
# FONCTIONS D'EXPORT
# ============================================================================
def exporter_fichier_corrige(df_corrige, annee, dossier_sortie):
    """
    Exporte le fichier annuel corrigé au format MAELIA standard.
    Nommage distinct de la Version 1 (_api) pour permettre la comparaison
    entre les deux méthodes de correction.

    Args:
        df_corrige (pd.DataFrame): DataFrame corrigé
        annee (int): Année concernée
        dossier_sortie (Path): Dossier de destination
    """
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    chemin_fichier = dossier_sortie / f"{annee}bis_api.csv"

    df_export = df_corrige.copy()
    df_export["DATE"] = df_export["DATE"].dt.strftime("%d/%m/%Y")
    df_export = df_export[["DATE", "RRmm", "Tmin", "Tmax", "ETP", "RGI"]]

    df_export.to_csv(chemin_fichier, sep=";", index=False)
    print(f"  ✓ {chemin_fichier.name} exporté ({len(df_export)} jours)")


def exporter_log_corrections(df_log, annee, dossier_logs):
    """
    Exporte le journal détaillé des corrections effectuées pour une année.

    Args:
        df_log (pd.DataFrame): Journal des corrections
        annee (int): Année concernée
        dossier_logs (Path): Dossier de destination des logs
    """
    dossier_logs.mkdir(parents=True, exist_ok=True)
    chemin_fichier = dossier_logs / f"{annee}_log_corrections_api.csv"

    if df_log.empty:
        df_log = pd.DataFrame(columns=["DATE", "variable", "valeur_originale",
                                        "valeur_corrigee", "methode"])

    df_log.to_csv(chemin_fichier, sep=";", index=False)

    nb_reussies = (df_log["methode"] == "API_NASA_POWER").sum()
    nb_echouees = (df_log["methode"] == "API_indisponible_non_corrige").sum()
    print(f"  ✓ {chemin_fichier.name} exporté "
          f"({nb_reussies} corrigée(s) via API, {nb_echouees} échec(s))")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CORRECTION DES VALEURS ABERRANTES - DONNÉES CLIMATIQUES SOB")
    print("Version 2 : API NASA POWER (réanalyse satellite)")
    print("=" * 70)

    # Vérification des coordonnées avant tout traitement
    if SITE_LATITUDE is None or SITE_LONGITUDE is None:
        print("\n❌ Erreur : les coordonnées GPS de la station (SITE_LATITUDE, "
              "SITE_LONGITUDE) ne sont pas renseignées en haut du script.")
        print("   Veuillez les compléter avant de relancer.")
        sys.exit(1)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    dossier_annees = base_dir / "tests" / "modeleCommun" / "meteo" / "observee"
    dossier_logs = base_dir / "data" / "climat" / "processed" / "rapports_corrections"

    print(f"\n📍 Répertoire du projet: {base_dir}")
    print(f"📥 Dossier des fichiers annuels: {dossier_annees}")
    print(f"📤 Dossier de sortie (fichiers bis_api): {dossier_annees}")
    print(f"📄 Dossier des journaux de correction: {dossier_logs}")
    print(f"🌍 Coordonnées du site: lat={SITE_LATITUDE}, lon={SITE_LONGITUDE}\n")

    if not dossier_annees.exists():
        print(f"❌ Erreur: Le dossier {dossier_annees} n'existe pas!")
        print("   Veuillez d'abord exécuter 01-traitement-climat.py")
        sys.exit(1)

    try:
        # 1. Charger toutes les années disponibles
        donnees = charger_toutes_les_annees(dossier_annees)

        if not donnees:
            print(f"❌ Erreur: Aucun fichier annuel valide trouvé dans {dossier_annees}")
            sys.exit(1)

        # 2. Détecter les anomalies pour chaque année
        print("\n🔍 Détection des valeurs aberrantes par année...")
        donnees_originales = {annee: df.copy() for annee, df in donnees.items()}
        donnees_nettoyees = {}
        for annee, df in donnees.items():
            print(f"\n  Année {annee} :")
            df_nettoye = detecter_anomalies(df)
            df_nettoye = detecter_anomalies_rrmm(df_nettoye)
            donnees_nettoyees[annee] = df_nettoye

        # 3. Interroger l'API et corriger, année par année
        print("\n🌐 Interrogation de l'API NASA POWER et correction...")
        for i, annee in enumerate(sorted(donnees.keys())):
            print(f"\n  Année {annee} :")
            df_api = interroger_nasa_power(SITE_LATITUDE, SITE_LONGITUDE, annee)

            df_corrige, df_log = corriger_avec_api(
                donnees_originales[annee],
                donnees_nettoyees[annee],
                df_api
            )
            exporter_fichier_corrige(df_corrige, annee, dossier_annees)
            exporter_log_corrections(df_log, annee, dossier_logs)

            # Pause entre les appels pour ne pas saturer l'API
            if i < len(donnees) - 1:
                time.sleep(NASA_POWER_PAUSE_ENTRE_APPELS)

        print("\n" + "=" * 70)
        print("✅ CORRECTION TERMINÉE")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
