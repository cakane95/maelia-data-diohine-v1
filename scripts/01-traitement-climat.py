"""
01-traitement-climat.py

Script de nettoyage des données météorologiques de la station de Sob
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Traitement des données brutes et calcul de l'ETP selon la méthode FAO-56
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings

# Supprimer les avertissements SettingWithCopyWarning
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


# ============================================================================
# CONSTANTES
# ============================================================================
GAMMA = 0.0665  # Constante psychrométrique (kPa/°C)
CN = 900        # Coefficient FAO-56 pour référence herbacée
CD = 0.34       # Coefficient de vent FAO-56


# ============================================================================
# FONCTIONS DE CALCUL
# ============================================================================
def saturation_vapor_pressure(T):
    """
    Calcule la pression de vapeur saturante à une température donnée.

    Args:
        T (float): Température en °C

    Returns:
        float: Pression de vapeur saturante en kPa
    """
    return 0.6108 * np.exp((17.27 * T) / (T + 237.3))


def delta_svp(T):
    """
    Calcule la pente de la courbe de pression de vapeur saturante.

    Args:
        T (float): Température en °C

    Returns:
        float: Pente de la courbe (kPa/°C)
    """
    e_s = saturation_vapor_pressure(T)
    return (4098 * e_s) / ((T + 237.3) ** 2)


def etp_penman_monteith_fao56(row):
    """
    Calcule l'évapotranspiration potentielle selon la méthode FAO-56.

    Args:
        row (pd.Series): Ligne contenant Tmean, RHmean, Wind_Speed_mean, RGI

    Returns:
        float: ETP en mm/jour
    """
    T = row["Tmean"]
    RH = row["RHmean"]
    u2 = row["Wind_Speed_mean"]
    Rn = row["RGI"]  # MJ/m²/jour

    e_s = saturation_vapor_pressure(T)
    e_a = e_s * RH / 100
    delta = delta_svp(T)

    num = 0.408 * delta * Rn + GAMMA * (CN / (T + 273)) * u2 * (e_s - e_a)
    den = delta + GAMMA * (1 + CD * u2)

    return max(0, num / den)


# ============================================================================
# FONCTIONS DE TRAITEMENT
# ============================================================================
def charger_donnees_brutes(input_path):
    """
    Charge et prétraite les données brutes de la station météo.

    Args:
        input_path (Path): Chemin vers le fichier Excel

    Returns:
        pd.DataFrame: DataFrame prétraité
    """
    print(f"📂 Chargement des données depuis: {input_path}")

    # Charger en sautant les 9 premières lignes
    df = pd.read_excel(input_path, header=9)
    df = df.drop(df.columns[0], axis=1)

    # Convertir et créer les colonnes nécessaires
    df["TIME_START"] = pd.to_datetime(df["TIME_START"], format="%Y%m%d%H%M")
    df["DATE"] = df["TIME_START"].dt.strftime("%d/%m/%Y")

    # Corrections des valeurs
    df["Precipitation"] = df["Precipitation"] / 2
    df["RGI_30min"] = df["Net_radiation_1"] * \
        1.8 / 1000  # MJ/m² sur 30 minutes

    print(f"✓ {len(df)} enregistrements chargés")
    return df


def agreger_donnees_journalieres(df):
    """
    Agrège les données de pas de temps 30 minutes en données journalières.

    Args:
        df (pd.DataFrame): DataFrame avec données haute fréquence

    Returns:
        pd.DataFrame: DataFrame journalier
    """
    print("🔄 Agrégation des données journalières...")

    df_daily = df.groupby("DATE").agg({
        "Precipitation": "sum",
        "Air_Temperature_at_2_m": ["min", "max", "mean"],
        "Relative_Humidity": "mean",
        "Wind_Speed": "mean",
        "RGI_30min": "sum"
    }).reset_index()

    # Aplatir les colonnes multi-index
    df_daily.columns = ["DATE", "RRmm", "Tmin", "Tmax", "Tmean",
                        "RHmean", "Wind_Speed_mean", "RGI"]

    print(f"✓ {len(df_daily)} jours agrégés")
    return df_daily


def calculer_etp(df_daily):
    """
    Calcule l'ETP pour chaque jour.

    Args:
        df_daily (pd.DataFrame): DataFrame journalier

    Returns:
        pd.DataFrame: DataFrame avec colonne ETP ajoutée
    """
    print("🌡️  Calcul de l'ETP selon FAO-56...")
    df_daily = df_daily.copy()
    df_daily["ETP"] = df_daily.apply(etp_penman_monteith_fao56, axis=1)
    print(f"✓ ETP calculée (moyenne: {df_daily['ETP'].mean():.2f} mm/jour)")
    return df_daily


def preparer_format_maelia(df_daily):
    """
    Prépare le format final pour MAELIA.

    Args:
        df_daily (pd.DataFrame): DataFrame journalier avec ETP

    Returns:
        pd.DataFrame: DataFrame au format MAELIA
    """
    print("📋 Préparation du format MAELIA...")

    df_maelia = df_daily[["DATE", "RRmm", "Tmin", "Tmax", "ETP", "RGI"]].copy()
    df_maelia["DATE"] = pd.to_datetime(df_maelia["DATE"], format="%d/%m/%Y")

    # Vérifier les doublons
    nb_doublons = df_maelia["DATE"].duplicated().sum()
    if nb_doublons > 0:
        print(f"⚠️  Attention: {nb_doublons} dates dupliquées détectées!")
    else:
        print("✓ Aucune date dupliquée")

    return df_maelia


def exporter_donnees_annuelles(df_journalier, dossier_sortie):
    """
    Découpe et exporte les données par année dans des fichiers CSV séparés.

    Args:
        df_journalier (pd.DataFrame): DataFrame contenant les données journalières
        dossier_sortie (Path): Dossier de destination
    """
    print(f"\n📁 Export des données annuelles vers: {dossier_sortie}")

    dossier_sortie = Path(dossier_sortie)
    dossier_sortie.mkdir(parents=True, exist_ok=True)

    # Copier et préparer les données
    df_copy = df_journalier.copy()
    if df_copy['DATE'].dtype == 'object':
        df_copy['DATE'] = pd.to_datetime(df_copy['DATE'], format='%d/%m/%Y')

    # Trier par date
    df_copy = df_copy.sort_values(by='DATE')
    df_copy['year'] = df_copy['DATE'].dt.year

    # Exporter chaque année
    for year, data_annee in df_copy.groupby('year'):
        data_annee = data_annee.copy()
        data_annee.loc[:, 'DATE'] = data_annee['DATE'].dt.strftime('%d/%m/%Y')

        nom_fichier = f"{year}.csv"
        chemin_fichier = dossier_sortie / nom_fichier

        df_export = data_annee.drop(columns=['year'])
        df_export.to_csv(chemin_fichier, sep=';', index=False)
        print(f"  ✓ {nom_fichier} ({len(df_export)} jours)")

    print(f"\n✅ Exportation terminée!")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("NETTOYAGE DES DONNÉES MÉTÉO - STATION SOB")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_path = base_dir / "data" / "climat" / "raw" / "donnees_station_SOB.xlsx"
    output_path = base_dir / "data" / "climat" / \
        "processed" / "stationSob_journalier_maelia.csv"
    output_dir_maelia = base_dir / "tests" / "modeleCommun" / "meteo" / "observee"

    print(f"\n📍 Répertoire du projet: {base_dir}")
    print(f"📥 Fichier d'entrée: {input_path}")
    print(f"📤 Fichier consolidé: {output_path}")
    print(f"📂 Dossier données annuelles MAELIA: {output_dir_maelia}\n")

    # Vérifier l'existence du fichier d'entrée
    if not input_path.exists():
        print(f"❌ Erreur: Le fichier {input_path} n'existe pas!")
        sys.exit(1)

    # Traitement des données
    try:
        # 1. Charger les données brutes
        df = charger_donnees_brutes(input_path)

        # 2. Agréger en données journalières
        df_daily = agreger_donnees_journalieres(df)

        # 3. Calculer l'ETP
        df_daily = calculer_etp(df_daily)

        # 4. Préparer le format MAELIA
        df_maelia = preparer_format_maelia(df_daily)

        # 5. Exporter le fichier consolidé
        print(f"\n💾 Export du fichier consolidé...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_maelia_export = df_maelia.copy()
        df_maelia_export["DATE"] = df_maelia_export["DATE"].dt.strftime(
            "%d/%m/%Y")
        df_maelia_export.to_csv(output_path, sep=";", index=False)
        print(f"  ✓ {output_path}")

        # 6. Exporter les données annuelles
        exporter_donnees_annuelles(df_maelia, output_dir_maelia)

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
