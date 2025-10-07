"""
02a-creation-centroides.py

Script de préparation des points de collecte de données sols pour les parcelles avec arbres
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Création du fichier points_echantillonnage_complets.csv à partir du parcellaire enrichi

Ce script :
- Charge le parcellaire enrichi avec les informations sur les arbres
- Nettoie les données (doublons, parcelles problématiques)
- Crée des points géolocalisés (coordonnées réelles pour arbres, centroïdes pour parcelles)
- Enrichit avec les types de champ
- Construit la classification ZONE_PEDO
- Export final en CSV
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import sys
import warnings

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def afficher_stats_arbres(gdf):
    """
    Affiche les statistiques sur la présence d'arbres dans le GeoDataFrame.

    Args:
        gdf (GeoDataFrame): GeoDataFrame contenant la colonne 'Arbre'
    """
    if 'Arbre' in gdf.columns:
        print("\n📊 Statistiques pour la colonne 'Arbre' :")
        comptage_arbres = gdf['Arbre'].value_counts()
        print(
            f"   Parcelles AVEC arbre (Arbre == 1) : {comptage_arbres.get(1, 0)}")
        print(
            f"   Parcelles SANS arbre (Arbre == 0) : {comptage_arbres.get(0, 0)}")
    else:
        print("\n❌ ATTENTION : La colonne 'Arbre' est manquante.")


def charger_parcellaire(shp_path):
    """
    Charge le shapefile du parcellaire enrichi.

    Args:
        shp_path (Path): Chemin vers le fichier shapefile

    Returns:
        GeoDataFrame: Parcellaire chargé
    """
    print(f"📂 Chargement du parcellaire depuis: {shp_path}")

    try:
        gdf = gpd.read_file(shp_path)
        print(f"✓ Fichier '{shp_path.name}' chargé avec succès")
        print(f"  Dimensions: {gdf.shape[0]} lignes × {gdf.shape[1]} colonnes")

        afficher_stats_arbres(gdf)
        return gdf

    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        sys.exit(1)


def selectionner_colonnes(gdf):
    """
    Sélectionne les colonnes nécessaires pour le traitement.

    Args:
        gdf (GeoDataFrame): GeoDataFrame complet

    Returns:
        DataFrame: DataFrame avec colonnes sélectionnées
    """
    print("\n🔍 Sélection des colonnes nécessaires...")

    colonnes_necessaires = [
        'parcel_id',
        'N°_PARCEL',
        'TYP_SOL',
        'Arbre',
        'Long',
        'Lat',
        'X_Centroid',
        'Y_Centroid'
    ]

    try:
        df_selection = gdf[colonnes_necessaires].copy()
        print(f"✓ {len(colonnes_necessaires)} colonnes sélectionnées")
        return df_selection

    except KeyError as e:
        print(f"❌ Erreur : La colonne {e} est introuvable")
        print(f"Colonnes disponibles : {gdf.columns.to_list()}")
        sys.exit(1)


def creer_geodataframes_separes(df):
    """
    Crée deux GeoDataFrames distincts : un pour les arbres, un pour les parcelles.

    Args:
        df (DataFrame): DataFrame avec données de parcelles et arbres

    Returns:
        tuple: (gdf_arbres, gdf_parcelles) en WGS84
    """
    print("\n🌍 Création des GeoDataFrames géolocalisés...")

    # Séparer arbres et parcelles
    df_arbres = df[df['Arbre'] == 1].copy()
    df_parcelles = df[df['Arbre'] != 1].copy()

    print(f"  Arbres (Arbre == 1) : {len(df_arbres)} points")
    print(f"  Parcelles (Arbre == 0) : {len(df_parcelles)} points")

    # GeoDataFrame pour les arbres (coordonnées Long/Lat)
    gdf_arbres = gpd.GeoDataFrame(
        df_arbres,
        geometry=gpd.points_from_xy(df_arbres.Long, df_arbres.Lat),
        crs="EPSG:4326"
    )

    # GeoDataFrame pour les parcelles (centroïdes)
    gdf_parcelles = gpd.GeoDataFrame(
        df_parcelles,
        geometry=gpd.points_from_xy(
            df_parcelles.X_Centroid, df_parcelles.Y_Centroid),
        crs="EPSG:4326"
    )

    print("✓ GeoDataFrames créés (CRS: EPSG:4326)")

    return gdf_arbres, gdf_parcelles


def fusionner_geodataframes(gdf_arbres, gdf_parcelles):
    """
    Fusionne les GeoDataFrames arbres et parcelles.

    Args:
        gdf_arbres (GeoDataFrame): Points pour les arbres
        gdf_parcelles (GeoDataFrame): Points pour les parcelles

    Returns:
        GeoDataFrame: GeoDataFrame fusionné
    """
    print("\n🔗 Fusion des données arbres et parcelles...")

    gdf_final = pd.concat([gdf_arbres, gdf_parcelles], ignore_index=True)

    print(f"✓ Fusion terminée : {len(gdf_final)} points au total")
    print(f"  CRS final : {gdf_final.crs}")

    return gdf_final


def nettoyer_donnees(gdf, df_malou):
    """
    Nettoie les données en supprimant les doublons et parcelles problématiques.

    Args:
        gdf (GeoDataFrame): GeoDataFrame des points
        df_malou (DataFrame): DataFrame avec types de champ

    Returns:
        tuple: (gdf_propre, df_malou_propre)
    """
    print("\n🧹 Nettoyage des données...")

    # Nettoyage de df_malou (doublons sur N°_PARCEL)
    print(f"  df_malou avant : {len(df_malou)} lignes")
    df_malou_clean = df_malou.drop_duplicates(
        subset=['N°_PARCEL'], keep='first').copy()
    print(f"  df_malou après : {len(df_malou_clean)} lignes")

    # Suppression de la parcelle 201 dans gdf
    print(f"  gdf avant : {len(gdf)} lignes")
    gdf_clean = gdf[gdf['N°_PARCEL'] != 201].copy()
    print(f"  gdf après : {len(gdf_clean)} lignes")

    print("✓ Nettoyage terminé")

    return gdf_clean, df_malou_clean


def enrichir_type_champ(gdf, malou_csv_path):
    """
    Enrichit le GeoDataFrame avec les informations de type de champ.

    Args:
        gdf (GeoDataFrame): GeoDataFrame des points
        malou_csv_path (Path): Chemin vers le CSV avec types de champ

    Returns:
        GeoDataFrame: GeoDataFrame enrichi
    """
    print(f"\n📥 Chargement des types de champ depuis: {malou_csv_path}")

    try:
        df_malou = pd.read_csv(malou_csv_path)
        df_malou = df_malou.rename(columns={'N°_PARCELL': 'N°_PARCEL'})
        print(f"✓ {len(df_malou)} enregistrements chargés")

        # Nettoyage
        gdf_clean, df_malou_clean = nettoyer_donnees(gdf, df_malou)

        # Jointure
        print("\n🔗 Jointure avec les types de champ...")
        df_type_champ = df_malou_clean[['N°_PARCEL', 'Type_champ']]

        gdf_enrichi = pd.merge(
            gdf_clean,
            df_type_champ,
            on='N°_PARCEL',
            how='left'
        )

        # Validation
        valeurs_manquantes = gdf_enrichi['Type_champ'].isnull().sum()

        if valeurs_manquantes == 0:
            print("✓ Toutes les parcelles ont trouvé une correspondance")
        else:
            print(
                f"⚠️  ATTENTION : {valeurs_manquantes} parcelle(s) sans correspondance")

        return gdf_enrichi

    except Exception as e:
        print(f"❌ Erreur lors de l'enrichissement: {e}")
        sys.exit(1)


def creer_classification_zone_pedo(gdf):
    """
    Crée les colonnes de classification type_ilot et ZONE_PEDO.

    Args:
        gdf (GeoDataFrame): GeoDataFrame à classifier

    Returns:
        GeoDataFrame: GeoDataFrame avec classification
    """
    print("\n🏷️  Création de la classification ZONE_PEDO...")

    try:
        # Déterminer la présence d'arbre
        presence_arbre = np.where(gdf['Arbre'] == 1, 'avec_arbr', 'sans_arbr')

        # Assurer le type texte
        gdf['TYP_SOL'] = gdf['TYP_SOL'].astype(str)
        gdf['Type_champ'] = gdf['Type_champ'].astype(str)

        # Créer type_ilot
        gdf['type_ilot'] = (
            gdf['TYP_SOL'] + '_' +
            gdf['Type_champ'] + '_' +
            presence_arbre
        )

        # Normaliser en minuscules
        gdf['type_ilot'] = gdf['type_ilot'].str.lower()

        # Créer ZONE_PEDO comme copie de type_ilot
        gdf['ZONE_PEDO'] = gdf['type_ilot']

        print("✓ Colonnes 'type_ilot' et 'ZONE_PEDO' créées")

        # Afficher quelques exemples
        print("\n📋 Exemples de classification :")
        exemples = gdf[['TYP_SOL', 'Type_champ', 'Arbre', 'ZONE_PEDO']].head(3)
        for _, row in exemples.iterrows():
            print(f"  {row['ZONE_PEDO']}")

        return gdf

    except Exception as e:
        print(f"❌ Erreur lors de la classification: {e}")
        sys.exit(1)


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DES POINTS D'ÉCHANTILLONNAGE - SOLS")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    shp_input_path = base_dir / "data" / "sols" / \
        "shapefiles" / "raw" / "Parcellaire_Arbre_Carbone.shp"
    malou_csv_path = base_dir / "data" / "sols" / "csv" / "raw" / "malou_0_30.csv"
    output_points_path = base_dir / "data" / "sols" / "csv" / \
        "processed" / "points_echantillonnage_complets.csv"

    print(f"\n📍 Répertoire du projet: {base_dir}")
    print(f"📥 Fichier shapefile: {shp_input_path}")
    print(f"📥 Fichier types de champ: {malou_csv_path}")
    print(f"📤 Fichier de sortie: {output_points_path}\n")

    # Vérifier l'existence des fichiers d'entrée
    if not shp_input_path.exists():
        print(f"❌ Erreur: Le fichier {shp_input_path} n'existe pas!")
        sys.exit(1)

    if not malou_csv_path.exists():
        print(f"❌ Erreur: Le fichier {malou_csv_path} n'existe pas!")
        sys.exit(1)

    # Traitement des données
    try:
        # 1. Charger le parcellaire enrichi
        gdf_parcelles = charger_parcellaire(shp_input_path)

        # 2. Sélectionner les colonnes nécessaires
        df_selection = selectionner_colonnes(gdf_parcelles)

        # 3. Supprimer les doublons stricts (au niveau du DataFrame)
        print(f"\n🔄 Suppression des doublons stricts...")
        print(f"  Avant: {len(df_selection)} lignes")
        df_selection = df_selection.drop_duplicates()
        print(f"  Après: {len(df_selection)} lignes")

        # 4. Créer les GeoDataFrames séparés (arbres et parcelles)
        gdf_arbres, gdf_parcelles_wgs84 = creer_geodataframes_separes(
            df_selection)

        # 5. Fusionner les deux GeoDataFrames
        gdf_wgs84 = fusionner_geodataframes(gdf_arbres, gdf_parcelles_wgs84)

        # 6. Enrichir avec les types de champ
        gdf_enrichi = enrichir_type_champ(gdf_wgs84, malou_csv_path)

        # 7. Créer la classification ZONE_PEDO
        gdf_final = creer_classification_zone_pedo(gdf_enrichi)

        # 8. Export en CSV
        print(f"\n💾 Export du fichier final...")
        output_points_path.parent.mkdir(parents=True, exist_ok=True)
        gdf_final.to_csv(output_points_path, sep=",", index=False)
        print(f"  ✓ {output_points_path}")
        print(f"  ✓ {len(gdf_final)} points exportés")

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
