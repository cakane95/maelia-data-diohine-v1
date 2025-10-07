"""
02b-extraction-agregation-donnees.py

Script d'extraction et d'agrégation des données de sols à partir de sources géospatiales
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Extraction des propriétés physiques, hydriques et chimiques des sols 
             à partir d'OpenLandMap, iSDA Africa et Cirad Dataverse

Ce script :
- Charge les points d'échantillonnage créés précédemment
- Extrait les données de texture (argile, sable), densité apparente, carbone/MO
- Récupère l'azote et le pH via l'API iSDA Africa
- Extrait les propriétés hydriques (HCC, HPFP, RUPRH) depuis Cirad Dataverse
- Calcule le rapport C/N
- Agrège les données par ZONE_PEDO (moyenne)
- Exporte la table de synthèse finale
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import sys
import warnings
import rasterio
from rasterio.windows import Window
import gzip
import time
import requests
from getpass import getpass

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# CONSTANTES
# ============================================================================
SOURCE_CRS = "epsg:32628"
VAN_BEMMELEN_FACTOR = 1.724  # Facteur de conversion Carbone -> Matière Organique
EPAISSEUR_MM = 300  # Épaisseur de la couche en mm (30 cm)


# ============================================================================
# FONCTIONS UTILITAIRES - CHARGEMENT
# ============================================================================
def load_geodata_from_wkt(file_path, geometry_col, source_crs):
    """
    Charge un CSV et le convertit en GeoDataFrame en utilisant une colonne WKT.
    Supprime automatiquement les lignes avec des géométries nulles.

    Args:
        file_path (Path): Chemin vers le fichier CSV
        geometry_col (str): Nom de la colonne contenant la géométrie WKT
        source_crs (str): Système de coordonnées source (ex: 'epsg:32628')

    Returns:
        GeoDataFrame: Données géospatiales
    """
    print(f"📂 Chargement des données depuis: {file_path}")

    if not file_path.exists():
        raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")

    df = pd.read_csv(file_path)

    # Nettoyage des géométries nulles
    initial_rows = len(df)
    df = df.dropna(subset=[geometry_col])
    final_rows = len(df)

    if final_rows < initial_rows:
        print(
            f"  🧹 {initial_rows - final_rows} ligne(s) avec géométries nulles supprimées")

    # Conversion en GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df[geometry_col]),
        crs=source_crs
    )

    print(f"✓ {len(gdf)} points chargés")
    return gdf


# ============================================================================
# FONCTIONS D'EXTRACTION - RASTERS
# ============================================================================
def extract_values(raster_url, gdf, band_number=1):
    """
    Extrait les valeurs d'un raster pour chaque point du GeoDataFrame.
    Version améliorée avec gestion des CRS manquants ou invalides.

    Args:
        raster_url (str): URL du raster
        gdf (GeoDataFrame): Points d'échantillonnage
        band_number (int): Numéro de bande à extraire

    Returns:
        list: Valeurs extraites
    """
    print(f"  🌍 Extraction depuis bande {band_number}...")
    print(f"    → Lecture du raster : {raster_url.split('/')[-1]}")

    with rasterio.open(raster_url) as src:
        # Vérification du CRS du raster
        if not src.crs:
            print("    ⚠️  Le raster n'a pas de CRS défini, on suppose EPSG:4326")
            src_crs = "EPSG:4326"
        else:
            src_crs = src.crs

        # Vérification du CRS du GeoDataFrame
        if gdf.crs is None:
            print(
                f"    ⚠️  Le GeoDataFrame n'a pas de CRS défini, on applique {SOURCE_CRS}")
            gdf = gdf.set_crs(SOURCE_CRS, allow_override=True)

        try:
            gdf_proj = gdf.to_crs(src_crs)
        except Exception as e:
            print(
                f"    ⚠️  CRS non standard détecté, reprojection vers WGS84 (EPSG:4326)")
            gdf_proj = gdf.to_crs("EPSG:4326")

        # Extraction pixel par pixel
        values = []
        for pt in gdf_proj.geometry:
            try:
                row, col = src.index(pt.x, pt.y)
                window = Window(col, row, 1, 1)
                data = src.read(band_number, window=window)
                values.append(float(data[0, 0]))
            except IndexError:
                values.append(None)
            except Exception:
                values.append(None)

        print(f"    ✓ Extraction terminée ({len(values)} valeurs)")
        return values


def extract_values_local_gz(local_file_path, gdf, band_number=1):
    """
    Ouvre un fichier .tif.gz local et extrait les valeurs pour chaque point.

    Args:
        local_file_path (Path): Chemin vers le fichier .tif.gz
        gdf (GeoDataFrame): Points d'échantillonnage
        band_number (int): Numéro de la bande

    Returns:
        list: Valeurs extraites
    """
    print(f"  📁 Lecture locale: {local_file_path.name} (bande {band_number})")

    with gzip.open(local_file_path, 'rb') as gz_f:
        with rasterio.open(gz_f) as src:
            gdf_proj = gdf.to_crs(src.crs)
            values = []
            for pt in gdf_proj.geometry:
                try:
                    row, col = src.index(pt.x, pt.y)
                    window = Window(col, row, 1, 1)
                    data = src.read(band_number, window=window)
                    values.append(data[0, 0])
                except IndexError:
                    values.append(None)

    return values


# ============================================================================
# FONCTIONS D'EXTRACTION - API iSDA
# ============================================================================
def obtenir_token_isda(username, password):
    """
    Obtient un token d'accès pour l'API iSDA Africa.

    Args:
        username (str): Email iSDA
        password (str): Mot de passe iSDA

    Returns:
        str: Token d'accès ou None
    """
    base_url = "https://api.isda-africa.com"
    login_payload = {"username": username, "password": password}

    try:
        print(f"🔐 Connexion à l'API iSDA...")
        response = requests.post(f"{base_url}/login", data=login_payload)
        response.raise_for_status()
        token = response.json().get("access_token")
        print("✓ Token obtenu avec succès")
        return token
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention du token: {e}")
        return None


def get_isda_property_reproject(gdf_source, token, property_name, depth="0-20"):
    """
    Interroge l'API iSDA pour obtenir une propriété de sol spécifique.

    Args:
        gdf_source (GeoDataFrame): Points d'échantillonnage
        token (str): Token d'authentification
        property_name (str): Nom de la propriété ('ph', 'nitrogen', etc.)
        depth (str): Profondeur ('0-20' ou '20-50')

    Returns:
        list: Valeurs extraites
    """
    if not token:
        print("❌ Token manquant")
        return None

    print(f"  🌐 Extraction API iSDA: {property_name} ({depth} cm)")
    gdf_wgs84 = gdf_source.to_crs(epsg=4326)

    base_url = "https://api.isda-africa.com"
    query_url = f"{base_url}/isdasoil/v2/soilproperty"
    headers = {"Authorization": f"Bearer {token}"}

    valeurs_extraites = []
    total = len(gdf_wgs84)

    for index, row in gdf_wgs84.iterrows():
        params = {
            "lat": row.geometry.y,
            "lon": row.geometry.x,
            "property": property_name,
            "depth": depth
        }

        try:
            response = requests.get(query_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            value = data['property'][property_name][0]['value']['value']
            valeurs_extraites.append(value)
        except Exception:
            valeurs_extraites.append(None)

        if (index + 1) % 100 == 0:
            print(f"    {index + 1}/{total} points traités")
        time.sleep(0.05)

    return valeurs_extraites


# ============================================================================
# FONCTIONS D'HARMONISATION DES HORIZONS
# ============================================================================
def calculer_horizon_0_30(val_0_20, val_20_50):
    """
    Calcule la valeur pro-rata pour l'horizon 0-30 cm.
    Moyenne pondérée: 20 cm de (0-20) + 10 cm de (20-50).
    """
    if pd.isna(val_0_20) or pd.isna(val_20_50):
        return np.nan
    return ((val_0_20 * 20) + (val_20_50 * 10)) / 30


def calculer_horizon_30_60(val_20_50):
    """
    Calcule la valeur pro-rata pour l'horizon 30-60 cm.
    Extension de la valeur 20-50 cm.
    """
    if pd.isna(val_20_50):
        return np.nan
    return val_20_50


# ============================================================================
# FONCTIONS DE TRAITEMENT PAR SOURCE
# ============================================================================
def extraire_openlandmap(gdf):
    """
    Extrait toutes les données depuis OpenLandMap (argile, sable, densité, carbone).

    Args:
        gdf (GeoDataFrame): Points d'échantillonnage

    Returns:
        GeoDataFrame: GeoDataFrame enrichi
    """
    print("\n" + "="*70)
    print("EXTRACTION OPENLANDMAP")
    print("="*70)

    # URLs des rasters
    rasters = {
        'CLAY_0_30': "https://zenodo.org/records/15528401/files/clay.tot_iso.11277.2020.wpct_m_120m_b0cm..30cm_20200101_20221231_g_epsg.4326_v20250523.tif",
        'CLAY_30_60': "https://zenodo.org/records/15528405/files/clay.tot_iso.11277.2020.wpct_m_120m_b30cm..60cm_20200101_20221231_g_epsg.4326_v20250523.tif",
        'SAND_0_30': "https://zenodo.org/records/15528413/files/sand.tot_iso.11277.2020.wpct_m_120m_b0cm..30cm_20200101_20221231_g_epsg.4326_v20250523.tif",
        'SAND_30_60': "https://zenodo.org/records/15528417/files/sand.tot_iso.11277.2020.wpct_m_120m_b30cm..60cm_20200101_20221231_g_epsg.4326_v20250523.tif",
        'BD_0_30': "https://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/bd.core_iso.11272.2017.g.cm3_m_30m_b0cm..30cm_20200101_20221231_g_epsg.4326_v20250204.tif",
        'BD_30_60': "https://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/bd.core_iso.11272.2017.g.cm3_m_30m_b30cm..60cm_20200101_20221231_g_epsg.4326_v20250204.tif",
        'SOC_0_30': "https://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/oc_iso.10694.1995.wpml_m_30m_b0cm..30cm_20200101_20221231_g_epsg.4326_v20250204.tif",
        'SOC_30_60': "https://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics/oc_iso.10694.1995.wpml_m_30m_b30cm..60cm_20200101_20221231_g_epsg.4326_v20250204.tif"
    }

    # Argile
    print("\n🔹 Teneur en argile (%)")
    gdf['ARG1'] = extract_values(rasters['CLAY_0_30'], gdf)
    gdf['ARG2'] = extract_values(rasters['CLAY_30_60'], gdf)

    # Sable
    print("\n🔹 Teneur en sable (%)")
    gdf['SAB1'] = extract_values(rasters['SAND_0_30'], gdf)
    gdf['SAB2'] = extract_values(rasters['SAND_30_60'], gdf)

    # Densité apparente (avec facteur d'échelle /100)
    print("\n🔹 Densité apparente (g/cm³)")
    dah_brut_0_30 = extract_values(rasters['BD_0_30'], gdf)
    dah_brut_30_60 = extract_values(rasters['BD_30_60'], gdf)
    gdf['DAH1'] = [val / 100 if val is not None else None for val in dah_brut_0_30]
    gdf['DAH2'] = [val / 100 if val is not None else None for val in dah_brut_30_60]

    # Carbone et Matière Organique (avec facteurs d'échelle)
    print("\n🔹 Carbone et matière organique (%)")
    soc_brut_0_30 = extract_values(rasters['SOC_0_30'], gdf)
    soc_brut_30_60 = extract_values(rasters['SOC_30_60'], gdf)

    # Conversion: brut /10 -> g/kg, puis /10 -> %
    gdf['C1'] = [(val / 10 / 10)
                 if val is not None else None for val in soc_brut_0_30]
    gdf['C2'] = [(val / 10 / 10)
                 if val is not None else None for val in soc_brut_30_60]

    # Calcul de la matière organique
    gdf['MO1'] = gdf['C1'] * VAN_BEMMELEN_FACTOR
    gdf['MO2'] = gdf['C2'] * VAN_BEMMELEN_FACTOR

    print(f"\n✓ OpenLandMap terminé")
    print(f"  Moyenne C1: {gdf['C1'].mean():.4f}%")
    print(f"  Moyenne MO1: {gdf['MO1'].mean():.4f}%")

    return gdf


def extraire_isda_africa(gdf, username, password):
    """
    Extrait les données depuis iSDA Africa (azote et pH).

    Args:
        gdf (GeoDataFrame): Points d'échantillonnage
        username (str): Email iSDA
        password (str): Mot de passe iSDA

    Returns:
        GeoDataFrame: GeoDataFrame enrichi
    """
    print("\n" + "="*70)
    print("EXTRACTION iSDA AFRICA")
    print("="*70)

    # Obtenir le token
    token = obtenir_token_isda(username, password)
    if not token:
        print("❌ Impossible de continuer sans token")
        sys.exit(1)

    # Azote (via raster direct)
    print("\n🔹 Azote total (g/kg)")
    n_url = "https://isdasoil.s3.amazonaws.com/soil_data/nitrogen_total/nitrogen_total.tif"
    n_raw_0_20 = extract_values(n_url, gdf, band_number=1)
    n_raw_20_50 = extract_values(n_url, gdf, band_number=2)

    # Facteur d'échelle /100
    n_gkg_0_20 = [val / 100 if val is not None else None for val in n_raw_0_20]
    n_gkg_20_50 = [
        val / 100 if val is not None else None for val in n_raw_20_50]

    # Harmonisation
    gdf['N1'] = [calculer_horizon_0_30(v1, v2)
                 for v1, v2 in zip(n_gkg_0_20, n_gkg_20_50)]
    gdf['N2'] = [calculer_horizon_30_60(v) for v in n_gkg_20_50]

    # pH (via API)
    print("\n🔹 pH du sol")
    ph_values_0_20 = get_isda_property_reproject(
        gdf, token, 'ph', depth="0-20")
    ph_values_20_50 = get_isda_property_reproject(
        gdf, token, 'ph', depth="20-50")

    # Harmonisation
    gdf['PH1'] = [calculer_horizon_0_30(v1, v2) for v1, v2 in zip(
        ph_values_0_20, ph_values_20_50)]
    gdf['PH2'] = [calculer_horizon_30_60(v) for v in ph_values_20_50]

    print(f"\n✓ iSDA Africa terminé")
    print(f"  Moyenne N1: {gdf['N1'].mean():.4f} g/kg")
    print(f"  Moyenne PH1: {gdf['PH1'].mean():.4f}")

    return gdf


def extraire_cirad_dataverse(gdf, base_dir):
    """
    Extrait les propriétés hydriques depuis Cirad Dataverse (fichiers locaux).

    Args:
        gdf (GeoDataFrame): Points d'échantillonnage
        base_dir (Path): Répertoire de base du projet

    Returns:
        GeoDataFrame: GeoDataFrame enrichi
    """
    print("\n" + "="*70)
    print("EXTRACTION CIRAD DATAVERSE")
    print("="*70)

    dossier_raster = base_dir / "data" / "sols" / "raster" / "raw"

    fichiers = [
        {'nom': 'senegal_theta_fc_0_20cm_mask.tif.gz', 'col': 'hcc_0_20'},
        {'nom': 'senegal_theta_fc_20_50cm_mask.tif.gz', 'col': 'hcc_20_50'},
        {'nom': 'senegal_theta_wp_0_20cm_mask.tif.gz', 'col': 'hpfp_0_20'},
        {'nom': 'senegal_theta_wp_20_50cm_mask.tif.gz', 'col': 'hpfp_20_50'},
    ]

    print("\n🔹 Extraction des propriétés hydriques (fractions)")
    for item in fichiers:
        chemin = dossier_raster / item['nom']
        try:
            valeurs = extract_values_local_gz(chemin, gdf)
            gdf[item['col']] = valeurs
        except Exception as e:
            print(f"  ❌ Erreur pour {item['nom']}: {e}")
            sys.exit(1)

    # Harmonisation
    print("\n🔹 Harmonisation des horizons")
    hcc_fraction1 = [calculer_horizon_0_30(
        v1, v2) for v1, v2 in zip(gdf['hcc_0_20'], gdf['hcc_20_50'])]
    hcc_fraction2 = [calculer_horizon_30_60(v) for v in gdf['hcc_20_50']]
    hpfp_fraction1 = [calculer_horizon_0_30(v1, v2) for v1, v2 in zip(
        gdf['hpfp_0_20'], gdf['hpfp_20_50'])]
    hpfp_fraction2 = [calculer_horizon_30_60(v) for v in gdf['hpfp_20_50']]

    # Calcul de la réserve utile
    print("\n🔹 Calcul de la réserve utile (RUPRH)")
    ruprh1 = [(hcc - hpfp) * EPAISSEUR_MM if hcc is not None and hpfp is not None else None
              for hcc, hpfp in zip(hcc_fraction1, hpfp_fraction1)]
    ruprh2 = [(hcc - hpfp) * EPAISSEUR_MM if hcc is not None and hpfp is not None else None
              for hcc, hpfp in zip(hcc_fraction2, hpfp_fraction2)]

    # Conversion en pourcentage pour HCC et HPFP
    gdf['HCC1'] = [v * 100 if v is not None else None for v in hcc_fraction1]
    gdf['HCC2'] = [v * 100 if v is not None else None for v in hcc_fraction2]
    gdf['HPFP1'] = [v * 100 if v is not None else None for v in hpfp_fraction1]
    gdf['HPFP2'] = [v * 100 if v is not None else None for v in hpfp_fraction2]
    gdf['RUPRH1'] = ruprh1
    gdf['RUPRH2'] = ruprh2

    # Nettoyage des colonnes temporaires
    gdf = gdf.drop(columns=['hcc_0_20', 'hcc_20_50',
                   'hpfp_0_20', 'hpfp_20_50'])

    print(f"\n✓ Cirad Dataverse terminé")
    print(f"  Moyenne HCC1: {gdf['HCC1'].mean():.2f}%")
    print(f"  Moyenne RUPRH1: {gdf['RUPRH1'].mean():.2f} mm")

    return gdf


def calculer_rapport_cn(gdf):
    """
    Calcule le rapport C/N.

    Args:
        gdf (GeoDataFrame): GeoDataFrame avec colonnes C et N

    Returns:
        GeoDataFrame: GeoDataFrame avec CN1 et CN2
    """
    print("\n🔹 Calcul du rapport C/N")

    # Conversion N en pourcentage
    gdf['N1_pct'] = gdf['N1'] / 10
    gdf['N2_pct'] = gdf['N2'] / 10

    # Calcul du rapport
    gdf['CN1'] = gdf['C1'] / gdf['N1_pct']
    gdf['CN2'] = gdf['C2'] / gdf['N2_pct']

    # Nettoyage
    gdf = gdf.replace([np.inf, -np.inf], np.nan)
    gdf = gdf.drop(columns=['N1_pct', 'N2_pct'])

    print(f"✓ Rapport C/N calculé (moyenne CN1: {gdf['CN1'].mean():.2f})")

    return gdf


def filtrer_zones_pedo_valides(gdf):
    """
    Filtre les données pour ne garder que les 8 ZONE_PEDO valides.

    Args:
        gdf (GeoDataFrame): GeoDataFrame complet

    Returns:
        GeoDataFrame: GeoDataFrame filtré
    """
    print("\n🔹 Filtrage des ZONE_PEDO valides")

    zones_valides = [
        'dior_cb_avec_arbr',
        'dior_cb_sans_arbr',
        'dior_cc_avec_arbr',
        'dior_cc_sans_arbr',
        'dekk_cb_avec_arbr',
        'dekk_cb_sans_arbr',
        'dekk/mbel_cb_avec_arbr',
        'dekk/mbel_cb_sans_arbr'
    ]

    initial = len(gdf)
    gdf_filtre = gdf[gdf['ZONE_PEDO'].isin(zones_valides)].copy()
    final = len(gdf_filtre)

    print(f"  Avant: {initial} lignes")
    print(f"  Après: {final} lignes")
    print(f"  Supprimées: {initial - final} lignes")

    return gdf_filtre


def agreger_par_zone_pedo(gdf):
    """
    Agrège les données par ZONE_PEDO en calculant la moyenne.

    Args:
        gdf (GeoDataFrame): GeoDataFrame complet

    Returns:
        DataFrame: Table de synthèse agrégée
    """
    print("\n🔹 Agrégation par ZONE_PEDO (moyenne)")

    colonnes_numeriques = [
        'ARG1', 'ARG2', 'SAB1', 'SAB2', 'DAH1', 'DAH2',
        'C1', 'C2', 'MO1', 'MO2', 'N1', 'N2',
        'PH1', 'PH2', 'HCC1', 'HCC2', 'HPFP1', 'HPFP2',
        'RUPRH1', 'RUPRH2', 'CN1', 'CN2'
    ]

    # Conversion en numérique
    for col in colonnes_numeriques:
        gdf[col] = pd.to_numeric(gdf[col], errors='coerce')

    # Agrégation
    df_agrege = gdf.groupby('ZONE_PEDO')[
        colonnes_numeriques].mean().reset_index()

    print(f"✓ {len(df_agrege)} ZONE_PEDO distinctes")

    return df_agrege


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("EXTRACTION ET AGRÉGATION DES DONNÉES DE SOLS")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_csv_path = base_dir / "data" / "sols" / "csv" / \
        "processed" / "points_echantillonnage_complets.csv"
    output_csv_path = base_dir / "data" / "sols" / \
        "csv" / "processed" / "donnees_typesDeSol.csv"

    print(f"\n📍 Répertoire du projet: {base_dir}")
    print(f"📥 Fichier d'entrée: {input_csv_path}")
    print(f"📤 Fichier de sortie: {output_csv_path}\n")

    # Vérifier l'existence du fichier d'entrée
    if not input_csv_path.exists():
        print(f"❌ Erreur: Le fichier {input_csv_path} n'existe pas!")
        sys.exit(1)

    # Traitement des données
    try:
        # 1. Charger les points d'échantillonnage
        gdf_points = load_geodata_from_wkt(
            input_csv_path, 'geometry', SOURCE_CRS)

        # 2. Extraction OpenLandMap
        gdf_points = extraire_openlandmap(gdf_points)

        # 3. Extraction iSDA Africa (avec authentification)
        print("\n" + "="*70)
        print("AUTHENTIFICATION iSDA")
        print("="*70)
        username = input("📧 Email iSDA: ")
        password = getpass("🔑 Mot de passe iSDA: ")

        gdf_points = extraire_isda_africa(gdf_points, username, password)

        # 4. Extraction Cirad Dataverse
        gdf_points = extraire_cirad_dataverse(gdf_points, base_dir)

        # 5. Calcul du rapport C/N
        gdf_points = calculer_rapport_cn(gdf_points)

        # 6. Filtrage des ZONE_PEDO valides
        gdf_points = filtrer_zones_pedo_valides(gdf_points)

        # 7. Agrégation par ZONE_PEDO
        df_synthese = agreger_par_zone_pedo(gdf_points)

        # 8. Export de la table de synthèse
        print(f"\n💾 Export de la table de synthèse...")
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        df_synthese.to_csv(output_csv_path, index=False, sep=';')
        print(f"  ✓ {output_csv_path}")
        print(f"  ✓ {len(df_synthese)} lignes (une par ZONE_PEDO)")

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
