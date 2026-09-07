"""
01d-correction-climat-hybride.py

Script de détection et correction des valeurs aberrantes dans les données
climatiques annuelles (sortie du script 01-traitement-climat.py), combinant
une estimation statistique (interpolation + climatologie mensuelle) et une
estimation via l'API NASA POWER, avec double vérification.
Auteurs: (conversion script: Aboubakry BA)
Description: Pour chaque valeur aberrante, calcule à la fois une estimation
             statistique et une estimation API. Si les deux concordent (écart
             sous un seuil), la valeur API est retenue avec un haut niveau de
             confiance. Si elles divergent, la valeur API est tout de même
             retenue mais l'écart est signalé pour révision humaine possible.
             En cas d'indisponibilité de l'API, repli automatique sur la
             valeur statistique. Génère des fichiers {annee}bis_hybride.csv
             + un journal détaillé et transparent des corrections.

Version 3 : hybride (statistique + API NASA POWER, double vérification)

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

# Plages de plausibilité physique (pour la détection des anomalies)
PLAGES_PLAUSIBILITE = {
    "Tmin": (15, 32),      # °C
    "Tmax": (28, 45),      # °C
    "ETP":  (1, 9),        # mm/jour
    "RGI":  (10, 30),      # MJ/m²/jour
}

VARIABLES_A_VALIDER = list(PLAGES_PLAUSIBILITE.keys())

MAX_TROU_INTERPOLATION = 3         # jours consécutifs interpolables (estimation stat.)
SEUIL_ALERTE_RRMM = 300            # mm/jour — au-delà, flag d'alerte sans correction
SEUIL_DIVERGENCE_PCT = 15          # % d'écart au-delà duquel stat/API sont jugées divergentes

PATTERN_FICHIER_ANNEE = re.compile(r"^(\d{4})\.csv$")

# Formats de date tolérés en entrée (testés dans cet ordre)
FORMATS_DATE_ACCEPTES = ["%d/%m/%Y", "%Y-%m-%d"]

# Constantes FAO-56 (identiques au script 01, pour l'ETP calculée depuis l'API)
GAMMA = 0.0665
CN = 900
CD = 0.34

# Configuration API NASA POWER
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_POWER_PARAMS = "T2M_MAX,T2M_MIN,T2M,RH2M,WS2M,ALLSKY_SFC_SW_DWN"
NASA_POWER_VALEUR_MANQUANTE = -999
NASA_POWER_TIMEOUT = 30            # secondes
NASA_POWER_PAUSE_ENTRE_APPELS = 1  # secondes

# Mapping variable MAELIA -> colonne API correspondante
MAPPING_VARIABLE_API = {
    "Tmin": "T2M_MIN",
    "Tmax": "T2M_MAX",
    "RGI":  "ALLSKY_SFC_SW_DWN",
    "ETP":  "ETP_API",
}


# ============================================================================
# FONCTIONS DE CALCUL ETP (identiques aux scripts 01 / 01c)
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
    Calcule l'ETP FAO-56 à partir des variables NASA POWER.

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
# FONCTIONS DE CHARGEMENT
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
    Charge un fichier annuel de données climatiques. Tolère plusieurs
    formats de date (voir FORMATS_DATE_ACCEPTES).

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
# FONCTIONS DE DÉTECTION DES ANOMALIES
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
    - valeur négative → aberrant (corrigée localement, mise à 0)
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
# FONCTIONS DE CLIMATOLOGIE (estimation statistique)
# ============================================================================
def calculer_climatologie_mensuelle(donnees_toutes_annees):
    """
    Calcule la médiane mensuelle de chaque variable sur l'ensemble des années
    disponibles, en excluant les valeurs déjà identifiées comme aberrantes.

    Args:
        donnees_toutes_annees (dict): {annee: pd.DataFrame nettoyé (NaN sur anomalies)}

    Returns:
        pd.DataFrame: Index = mois (1-12), colonnes = variables, valeurs = médiane
    """
    print("\n📊 Calcul de la climatologie mensuelle (médiane, valeurs valides uniquement)...")

    df_combine = pd.concat(donnees_toutes_annees.values(), ignore_index=True)
    df_combine["mois"] = df_combine["DATE"].dt.month

    climato = df_combine.groupby("mois")[VARIABLES_A_VALIDER].median()

    for variable in VARIABLES_A_VALIDER:
        print(f"  ✓ {variable} : médianes mensuelles calculées "
              f"(ex. janvier={climato.loc[1, variable]:.2f}, "
              f"juillet={climato.loc[7, variable]:.2f})")

    return climato


def estimer_serie_statistique(df_anomalies, variable, climato):
    """
    Construit une estimation statistique complète pour une variable :
    interpolation linéaire (trous courts) puis climatologie mensuelle
    (trous longs, bords). Ne modifie pas les valeurs déjà valides.

    Args:
        df_anomalies (pd.DataFrame): DataFrame avec anomalies mises à NaN
        variable (str): Nom de la colonne
        climato (pd.DataFrame): Climatologie mensuelle

    Returns:
        pd.Series: Estimation statistique pour toutes les lignes
    """
    serie_interpolee = df_anomalies[variable].interpolate(
        method="linear",
        limit=MAX_TROU_INTERPOLATION,
        limit_area="inside"
    )
    mois = df_anomalies["DATE"].dt.month
    valeurs_climato = mois.map(climato[variable])
    return serie_interpolee.fillna(valeurs_climato)


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
# FONCTIONS DE CORRECTION HYBRIDE
# ============================================================================
def corriger_rrmm(df):
    """
    Corrige les valeurs négatives de précipitation en les remplaçant par 0.

    Args:
        df (pd.DataFrame): DataFrame annuel

    Returns:
        pd.Series: Colonne RRmm corrigée
    """
    return df["RRmm"].fillna(0)


def corriger_annee_hybride(df_original, df_anomalies, climato, df_api):
    """
    Applique la correction hybride avec double vérification : pour chaque
    valeur aberrante, compare l'estimation statistique et l'estimation API,
    retient la valeur API si elle est disponible (en signalant si les deux
    méthodes divergent), et se replie sur la statistique si l'API est
    indisponible pour cette date.

    Args:
        df_original (pd.DataFrame): DataFrame brut avant toute modification
        df_anomalies (pd.DataFrame): DataFrame avec anomalies mises à NaN
        climato (pd.DataFrame): Climatologie mensuelle
        df_api (pd.DataFrame or None): Données NASA POWER pour l'année

    Returns:
        tuple: (pd.DataFrame corrigé au format MAELIA, pd.DataFrame journal des corrections)
    """
    df_corrige = df_anomalies.copy()
    lignes_log = []

    for variable in VARIABLES_A_VALIDER:
        estimation_stat = estimer_serie_statistique(df_anomalies, variable, climato)
        colonne_api = MAPPING_VARIABLE_API[variable]
        masque_manquant = df_anomalies[variable].isna()

        for idx in df_corrige.index[masque_manquant]:
            date = df_corrige.loc[idx, "DATE"]
            valeur_originale = df_original.loc[idx, variable]
            valeur_stat = estimation_stat.loc[idx]

            valeur_api = None
            if df_api is not None and date in df_api.index:
                candidate = df_api.loc[date, colonne_api]
                if pd.notna(candidate):
                    valeur_api = candidate

            ecart_pct = None

            if valeur_api is not None and pd.notna(valeur_stat):
                if valeur_api != 0:
                    ecart_pct = round(abs(valeur_stat - valeur_api) / abs(valeur_api) * 100, 1)
                if ecart_pct is not None and ecart_pct <= SEUIL_DIVERGENCE_PCT:
                    valeur_finale = valeur_api
                    methode = "API_confirmee_stat"
                else:
                    # Écart non calculable (division par zéro) ou > seuil :
                    # la valeur API est tout de même retenue par défaut
                    # (donnée géo-datée), la divergence est tracée pour
                    # révision humaine possible.
                    valeur_finale = valeur_api
                    methode = "API_ET_stat_divergentes"

            elif valeur_api is not None and pd.isna(valeur_stat):
                valeur_finale = valeur_api
                methode = "API_seule_(stat_indisponible)"

            elif valeur_api is None and pd.notna(valeur_stat):
                valeur_finale = valeur_stat
                methode = "stat_seule_(API_indisponible)"

            else:
                valeur_finale = np.nan
                methode = "non_corrige_aucune_source"

            df_corrige.loc[idx, variable] = valeur_finale
            lignes_log.append({
                "DATE": date.strftime("%d/%m/%Y"),
                "variable": variable,
                "valeur_originale": valeur_originale,
                "valeur_stat": round(valeur_stat, 2) if pd.notna(valeur_stat) else None,
                "valeur_api": round(valeur_api, 2) if valeur_api is not None else None,
                "ecart_pct": ecart_pct,
                "valeur_corrigee": round(valeur_finale, 2) if pd.notna(valeur_finale) else None,
                "methode": methode
            })

    # Correction RRmm (négatifs uniquement, indépendante de la logique hybride)
    avant_rrmm = df_corrige["RRmm"].copy()
    df_corrige["RRmm"] = corriger_rrmm(df_corrige)
    masque_rrmm = avant_rrmm.isna() & df_corrige["RRmm"].notna()
    for idx in df_corrige.index[masque_rrmm]:
        lignes_log.append({
            "DATE": df_corrige.loc[idx, "DATE"].strftime("%d/%m/%Y"),
            "variable": "RRmm",
            "valeur_originale": df_original.loc[idx, "RRmm"],
            "valeur_stat": None,
            "valeur_api": None,
            "ecart_pct": None,
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

    Args:
        df_corrige (pd.DataFrame): DataFrame corrigé
        annee (int): Année concernée
        dossier_sortie (Path): Dossier de destination
    """
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    chemin_fichier = dossier_sortie / f"{annee}bis_hybride.csv"

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
    chemin_fichier = dossier_logs / f"{annee}_log_corrections_hybride.csv"

    colonnes = ["DATE", "variable", "valeur_originale", "valeur_stat",
                "valeur_api", "ecart_pct", "valeur_corrigee", "methode"]
    if df_log.empty:
        df_log = pd.DataFrame(columns=colonnes)

    df_log.to_csv(chemin_fichier, sep=";", index=False)

    repartition = df_log["methode"].value_counts()
    print(f"  ✓ {chemin_fichier.name} exporté ({len(df_log)} ligne(s))")
    for methode, count in repartition.items():
        print(f"      - {methode} : {count}")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CORRECTION DES VALEURS ABERRANTES - DONNÉES CLIMATIQUES SOB")
    print("Version 3 : Hybride (statistique + API NASA POWER)")
    print("=" * 70)

    if SITE_LATITUDE is None or SITE_LONGITUDE is None:
        print("\n❌ Erreur : les coordonnées GPS de la station (SITE_LATITUDE, "
              "SITE_LONGITUDE) ne sont pas renseignées en haut du script.")
        print("   Veuillez les compléter avant de relancer.")
        sys.exit(1)

    base_dir = Path(__file__).parent.parent.resolve()
    dossier_annees = base_dir / "tests" / "modeleCommun" / "meteo" / "observee"
    dossier_logs = base_dir / "data" / "climat" / "processed" / "rapports_corrections"

    print(f"\n📍 Répertoire du projet: {base_dir}")
    print(f"📥 Dossier des fichiers annuels: {dossier_annees}")
    print(f"📤 Dossier de sortie (fichiers bis_hybride): {dossier_annees}")
    print(f"📄 Dossier des journaux de correction: {dossier_logs}")
    print(f"🌍 Coordonnées du site: lat={SITE_LATITUDE}, lon={SITE_LONGITUDE}")
    print(f"⚖️  Seuil de divergence stat/API: {SEUIL_DIVERGENCE_PCT}%\n")

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

        # 3. Calculer la climatologie mensuelle (base de l'estimation statistique)
        climato = calculer_climatologie_mensuelle(donnees_nettoyees)

        # 4. Interroger l'API et appliquer la correction hybride, année par année
        print("\n🌐 Interrogation de l'API NASA POWER et correction hybride...")
        for i, annee in enumerate(sorted(donnees.keys())):
            print(f"\n  Année {annee} :")
            df_api = interroger_nasa_power(SITE_LATITUDE, SITE_LONGITUDE, annee)

            df_corrige, df_log = corriger_annee_hybride(
                donnees_originales[annee],
                donnees_nettoyees[annee],
                climato,
                df_api
            )
            exporter_fichier_corrige(df_corrige, annee, dossier_annees)
            exporter_log_corrections(df_log, annee, dossier_logs)

            if i < len(donnees) - 1:
                time.sleep(NASA_POWER_PAUSE_ENTRE_APPELS)

        print("\n" + "=" * 70)
        print("✅ CORRECTION HYBRIDE TERMINÉE")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
