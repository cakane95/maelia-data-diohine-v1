"""
01b-correction-climat.py

Script de détection et correction des valeurs aberrantes dans les données
climatiques annuelles (sortie du script 01-traitement-climat.py)
Auteurs: (conversion script: Aboubakry BA)
Description: Détecte les valeurs physiquement incohérentes (Tmin, Tmax, ETP, RGI)
             et les corrige par interpolation temporelle ou climatologie mensuelle.
             Génère des fichiers {annee}bis.csv corrigés + un journal détaillé
             des corrections effectuées (traçabilité).

Version 1 : correction statistique pure (sans API externe)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import re
import warnings

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


# ============================================================================
# CONSTANTES
# ============================================================================

# Plages de plausibilité physique pour la zone Sob/Sasseme (Sénégal)
# À ajuster si une référence locale plus précise devient disponible
PLAGES_PLAUSIBILITE = {
    "Tmin": (15, 32),      # °C
    "Tmax": (28, 45),      # °C
    "ETP":  (1, 9),        # mm/jour
    "RGI":  (10, 30),      # MJ/m²/jour
}

VARIABLES_A_VALIDER = list(PLAGES_PLAUSIBILITE.keys())

MAX_TROU_INTERPOLATION = 3     # nombre max de jours consécutifs interpolables
SEUIL_ALERTE_RRMM = 300        # mm/jour — au-delà, flag d'alerte sans correction

PATTERN_FICHIER_ANNEE = re.compile(r"^(\d{4})\.csv$")

# Formats de date tolérés en entrée (testés dans cet ordre)
FORMATS_DATE_ACCEPTES = ["%d/%m/%Y", "%Y-%m-%d"]


# ============================================================================
# FONCTIONS DE CHARGEMENT
# ============================================================================
def lister_fichiers_annuels(dossier):
    """
    Liste les fichiers annuels valides (ex: 2020.csv) dans le dossier,
    en excluant les fichiers déjà corrigés (ex: 2020bis.csv).

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
    et les remplace temporairement par NaN pour traitement ultérieur.

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
    - valeur négative → aberrant (à corriger)
    - valeur > seuil d'alerte → à signaler uniquement (pas corrigé automatiquement)

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
              f"(non corrigées automatiquement, à vérifier manuellement)")

    return df


# ============================================================================
# FONCTIONS DE CLIMATOLOGIE
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


# ============================================================================
# FONCTIONS DE CORRECTION
# ============================================================================
def corriger_par_interpolation(df, variable):
    """
    Corrige les trous courts (≤ MAX_TROU_INTERPOLATION jours consécutifs)
    par interpolation linéaire entre les jours valides voisins.
    Les trous en bordure de série (début/fin) ne sont volontairement pas
    traités ici (pas de voisin des deux côtés) : ils seront comblés par
    la climatologie mensuelle à l'étape suivante.

    Args:
        df (pd.DataFrame): DataFrame annuel (valeurs aberrantes = NaN)
        variable (str): Nom de la colonne à corriger

    Returns:
        pd.Series: Colonne partiellement corrigée
    """
    return df[variable].interpolate(
        method="linear",
        limit=MAX_TROU_INTERPOLATION,
        limit_area="inside"
    )


def corriger_par_climatologie(df, variable, climato):
    """
    Corrige les valeurs encore manquantes après interpolation en utilisant
    la médiane mensuelle (climatologie).

    Args:
        df (pd.DataFrame): DataFrame annuel
        variable (str): Nom de la colonne à corriger
        climato (pd.DataFrame): Climatologie mensuelle (voir calculer_climatologie_mensuelle)

    Returns:
        pd.Series: Colonne complétée
    """
    mois = df["DATE"].dt.month
    valeurs_climato = mois.map(climato[variable])
    return df[variable].fillna(valeurs_climato)


def corriger_rrmm(df):
    """
    Corrige les valeurs négatives de précipitation (mises à NaN en amont)
    en les remplaçant par 0 (une précipitation négative n'a pas de sens
    physique ; l'hypothèse la plus sûre reste l'absence de pluie ce jour-là).

    Args:
        df (pd.DataFrame): DataFrame annuel

    Returns:
        pd.Series: Colonne RRmm corrigée
    """
    return df["RRmm"].fillna(0)


def corriger_annee(df_original, df_anomalies, climato):
    """
    Applique la correction complète (interpolation puis climatologie) sur
    toutes les variables d'une année, et construit le journal des corrections.

    Args:
        df_original (pd.DataFrame): DataFrame brut avant toute modification
        df_anomalies (pd.DataFrame): DataFrame avec anomalies mises à NaN
        climato (pd.DataFrame): Climatologie mensuelle

    Returns:
        tuple: (pd.DataFrame corrigé au format MAELIA, pd.DataFrame journal des corrections)
    """
    df_corrige = df_anomalies.copy()
    lignes_log = []

    for variable in VARIABLES_A_VALIDER:
        avant_interpolation = df_corrige[variable].copy()

        # Étape 1 : interpolation pour les trous courts
        df_corrige[variable] = corriger_par_interpolation(df_corrige, variable)
        methode = pd.Series(
            np.where(avant_interpolation.isna() & df_corrige[variable].notna(),
                     "interpolation", None),
            index=df_corrige.index
        )

        # Étape 2 : climatologie mensuelle pour ce qui reste (trous longs, bords)
        avant_climato = df_corrige[variable].copy()
        df_corrige[variable] = corriger_par_climatologie(df_corrige, variable, climato)
        methode = methode.where(
            ~(avant_climato.isna() & df_corrige[variable].notna()),
            "climatologie_mensuelle_mediane"
        )

        # Construction du journal pour cette variable
        masque_corrige = methode.notna()
        for idx in df_corrige.index[masque_corrige]:
            lignes_log.append({
                "DATE": df_corrige.loc[idx, "DATE"].strftime("%d/%m/%Y"),
                "variable": variable,
                "valeur_originale": df_original.loc[idx, variable],
                "valeur_corrigee": round(df_corrige.loc[idx, variable], 2),
                "methode": methode.loc[idx]
            })

    # Correction RRmm (négatifs uniquement)
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

    Args:
        df_corrige (pd.DataFrame): DataFrame corrigé
        annee (int): Année concernée
        dossier_sortie (Path): Dossier de destination
    """
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    chemin_fichier = dossier_sortie / f"{annee}bis.csv"

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
    chemin_fichier = dossier_logs / f"{annee}_log_corrections.csv"

    if df_log.empty:
        df_log = pd.DataFrame(columns=["DATE", "variable", "valeur_originale",
                                        "valeur_corrigee", "methode"])

    df_log.to_csv(chemin_fichier, sep=";", index=False)
    print(f"  ✓ {chemin_fichier.name} exporté ({len(df_log)} correction(s) enregistrée(s))")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CORRECTION DES VALEURS ABERRANTES - DONNÉES CLIMATIQUES SOB")
    print("Version 1 : Statistique (interpolation + climatologie mensuelle)")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    dossier_annees = base_dir / "tests" / "modeleCommun" / "meteo" / "observee"
    dossier_logs = base_dir / "data" / "climat" / "processed" / "rapports_corrections"

    print(f"\n📍 Répertoire du projet: {base_dir}")
    print(f"📥 Dossier des fichiers annuels: {dossier_annees}")
    print(f"📤 Dossier de sortie (fichiers bis): {dossier_annees}")
    print(f"📄 Dossier des journaux de correction: {dossier_logs}\n")

    # Vérifier l'existence du dossier d'entrée
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

        # 2. Détecter les anomalies pour chaque année (nécessaire avant climatologie)
        print("\n🔍 Détection des valeurs aberrantes par année...")
        donnees_originales = {annee: df.copy() for annee, df in donnees.items()}
        donnees_nettoyees = {}
        for annee, df in donnees.items():
            print(f"\n  Année {annee} :")
            df_nettoye = detecter_anomalies(df)
            df_nettoye = detecter_anomalies_rrmm(df_nettoye)
            donnees_nettoyees[annee] = df_nettoye

        # 3. Calculer la climatologie mensuelle sur l'ensemble des années valides
        climato = calculer_climatologie_mensuelle(donnees_nettoyees)

        # 4. Corriger chaque année et exporter
        print("\n🔧 Correction des valeurs aberrantes par année...")
        for annee in sorted(donnees.keys()):
            print(f"\n  Année {annee} :")
            df_corrige, df_log = corriger_annee(
                donnees_originales[annee],
                donnees_nettoyees[annee],
                climato
            )
            exporter_fichier_corrige(df_corrige, annee, dossier_annees)
            exporter_log_corrections(df_log, annee, dossier_logs)

        print("\n" + "=" * 70)
        print("✅ CORRECTION TERMINÉE AVEC SUCCÈS")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
