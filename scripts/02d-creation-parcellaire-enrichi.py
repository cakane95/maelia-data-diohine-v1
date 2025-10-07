"""
02d-creation-parcellaire-enrichi.py

Script de création du parcellaire enrichi avec classification ZONE_PEDO
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Enrichit le shapefile du parcellaire brut avec les attributs de classification
             nécessaires pour les analyses et la création du fichier typeDeSolParZH.shp

Ce script :
- Charge le shapefile du parcellaire brut
- Charge les données CSV avec les types de champ
- Nettoie les données (doublons, parcelles problématiques)
- Enrichit avec l'attribut Type_champ
- Crée la classification ZONE_PEDO
- Exporte le shapefile enrichi
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
def charger_donnees_brutes(parcellaire_path, csv_path):
    """
    Charge le shapefile du parcellaire et le CSV des types de champ.

    Args:
        parcellaire_path (Path): Chemin vers le shapefile du parcellaire
        csv_path (Path): Chemin vers le CSV avec types de champ

    Returns:
        tuple: (gdf_parcellaire, df_malou)
    """
    print("📂 Chargement des données brutes...")

    # Charger le shapefile
    if not parcellaire_path.exists():
        raise FileNotFoundError(f"Shapefile non trouvé : {parcellaire_path}")

    gdf = gpd.read_file(parcellaire_path)
    print(f"  ✓ Parcellaire chargé : {len(gdf)} entités")

    # Charger le CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier CSV non trouvé : {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"  ✓ Types de champ chargés : {len(df)} enregistrements")

    return gdf, df


def nettoyer_donnees(gdf_parcellaire, df_malou):
    """
    Nettoie les données sources (doublons, parcelles problématiques).

    Args:
        gdf_parcellaire (GeoDataFrame): Parcellaire brut
        df_malou (DataFrame): Types de champ

    Returns:
        tuple: (gdf_nettoyé, df_nettoyé)
    """
    print("\n🧹 Nettoyage des données sources...")

    # Nettoyer df_malou
    print("  • Traitement du CSV :")

    # Renommer la colonne si nécessaire
    if 'N°_PARCELL' in df_malou.columns:
        df_malou = df_malou.rename(columns={'N°_PARCELL': 'N°_PARCEL'})
        print("    ✓ Colonne renommée : N°_PARCELL → N°_PARCEL")

    # Supprimer les doublons
    initial_malou = len(df_malou)
    df_malou = df_malou.drop_duplicates(subset=['N°_PARCEL'], keep='first')
    final_malou = len(df_malou)

    if initial_malou > final_malou:
        print(f"    ✓ {initial_malou - final_malou} doublon(s) supprimé(s)")
    else:
        print("    ✓ Aucun doublon détecté")

    # Nettoyer gdf_parcellaire
    print("  • Traitement du parcellaire :")

    initial_parcelles = len(gdf_parcellaire)
    gdf_parcellaire = gdf_parcellaire[gdf_parcellaire['N°_PARCEL'] != 201].copy(
    )
    final_parcelles = len(gdf_parcellaire)

    if initial_parcelles > final_parcelles:
        print(
            f"    ✓ Parcelle 201 supprimée ({initial_parcelles - final_parcelles} entité(s))")
    else:
        print("    ✓ Aucune suppression nécessaire")

    print(f"\n  Résultat final :")
    print(f"    • Parcellaire : {final_parcelles} entités")
    print(f"    • Types de champ : {final_malou} enregistrements")

    return gdf_parcellaire, df_malou


def enrichir_avec_type_champ(gdf_parcellaire, df_malou):
    """
    Enrichit le parcellaire avec l'attribut Type_champ via jointure.

    Args:
        gdf_parcellaire (GeoDataFrame): Parcellaire nettoyé
        df_malou (DataFrame): Types de champ

    Returns:
        GeoDataFrame: Parcellaire enrichi
    """
    print("\n🔗 Enrichissement avec Type_champ...")

    # Effectuer la jointure
    gdf_enrichi = gdf_parcellaire.merge(
        df_malou[['N°_PARCEL', 'Type_champ']],
        on='N°_PARCEL',
        how='left'
    )

    # Vérifier le résultat
    valeurs_manquantes = gdf_enrichi['Type_champ'].isnull().sum()

    if valeurs_manquantes > 0:
        print(f"  ⚠️  {valeurs_manquantes} entité(s) sans Type_champ")
    else:
        print(f"  ✓ Toutes les entités enrichies avec succès")

    # Afficher la répartition
    print(f"\n  Répartition des types de champ :")
    for type_champ, count in gdf_enrichi['Type_champ'].value_counts().items():
        print(f"    • {type_champ} : {count} entités")

    return gdf_enrichi


def creer_zone_pedo(gdf):
    """
    Crée la colonne de classification ZONE_PEDO.

    Args:
        gdf (GeoDataFrame): Parcellaire enrichi

    Returns:
        GeoDataFrame: Parcellaire avec ZONE_PEDO
    """
    print("\n🏷️  Création de la classification ZONE_PEDO...")

    # Déterminer la présence d'arbre
    print("  • Création de l'indicateur de présence d'arbre")
    presence_arbre = np.where(gdf['Arbre'] == 1, 'avec_arbr', 'sans_arbr')

    # Construire ZONE_PEDO
    print("  • Construction de ZONE_PEDO (TYP_SOL + Type_champ + Arbre)")
    gdf['ZONE_PEDO'] = (
        gdf['TYP_SOL'].astype(str) + '_' +
        gdf['Type_champ'].astype(str) + '_' +
        presence_arbre
    ).str.lower()

    # Nettoyage : remplacer 'dekk/mbel' par 'dekkMbel'
    print("  • Nettoyage de la nomenclature (dekk/mbel → dekkMbel)")
    gdf['ZONE_PEDO'] = gdf['ZONE_PEDO'].str.replace(
        'dekk/mbel', 'dekkMbel', regex=False)

    # Afficher la répartition
    print(f"\n  ✓ ZONE_PEDO créée avec succès")
    print(f"\n  Répartition des classifications :")

    repartition = gdf['ZONE_PEDO'].value_counts().sort_index()
    for zone, count in repartition.items():
        print(f"    • {zone} : {count} entités")

    print(f"\n  Total : {len(repartition)} types de ZONE_PEDO distincts")

    return gdf


def afficher_apercu(gdf):
    """
    Affiche un aperçu du GeoDataFrame enrichi.

    Args:
        gdf (GeoDataFrame): Parcellaire enrichi
    """
    print("\n📊 Aperçu du parcellaire enrichi :")
    print(
        f"\n  Dimensions : {gdf.shape[0]} entités × {gdf.shape[1]} attributs")

    # Colonnes clés
    colonnes_cles = ['N°_PARCEL', 'TYP_SOL',
                     'Arbre', 'Type_champ', 'ZONE_PEDO']
    colonnes_disponibles = [col for col in colonnes_cles if col in gdf.columns]

    print(f"\n  Échantillon de données (5 premières lignes) :")
    print(gdf[colonnes_disponibles].head().to_string(index=False))

    # Statistiques par type de sol
    if 'TYP_SOL' in gdf.columns:
        print(f"\n  Répartition par type de sol (TYP_SOL) :")
        for typ_sol, count in gdf['TYP_SOL'].value_counts().items():
            print(f"    • {typ_sol} : {count} entités")

    # Statistiques présence d'arbres
    if 'Arbre' in gdf.columns:
        print(f"\n  Répartition présence d'arbres :")
        arbre_counts = gdf['Arbre'].value_counts()
        print(
            f"    • Avec arbres (Arbre = 1) : {arbre_counts.get(1, 0)} entités")
        print(
            f"    • Sans arbres (Arbre = 0) : {arbre_counts.get(0, 0)} entités")


def sauvegarder_shapefile(gdf, output_path):
    """
    Sauvegarde le GeoDataFrame enrichi en shapefile.

    Args:
        gdf (GeoDataFrame): Parcellaire enrichi
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du shapefile enrichi...")

    # Créer le dossier de sortie si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    gdf.to_file(output_path, driver='ESRI Shapefile')

    print(f"  ✓ Shapefile sauvegardé avec succès")
    print(f"  ✓ Emplacement : {output_path}")
    print(f"  ✓ {gdf.shape[0]} entités × {gdf.shape[1]} attributs")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DU PARCELLAIRE ENRICHI")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_parcellaire_path = base_dir / "data" / "sols" / \
        "shapefiles" / "raw" / "Parcellaire_Arbre_Carbone.shp"
    malou_csv_path = base_dir / "data" / "sols" / "csv" / "raw" / "malou_0_30.csv"
    output_parcellaire_path = base_dir / "data" / "sols" / \
        "shapefiles" / "processed" / "parcellaire_enrichi.shp"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Parcellaire brut : {input_parcellaire_path}")
    print(f"📥 Types de champ : {malou_csv_path}")
    print(f"📤 Parcellaire enrichi : {output_parcellaire_path}\n")

    # Traitement des données
    try:
        # 1. Charger les données brutes
        gdf_parcellaire, df_malou = charger_donnees_brutes(
            input_parcellaire_path,
            malou_csv_path
        )

        # 2. Nettoyer les données
        gdf_parcellaire, df_malou = nettoyer_donnees(gdf_parcellaire, df_malou)

        # 3. Enrichir avec Type_champ
        gdf_enrichi = enrichir_avec_type_champ(gdf_parcellaire, df_malou)

        # 4. Créer ZONE_PEDO
        gdf_final = creer_zone_pedo(gdf_enrichi)

        # 5. Afficher un aperçu
        afficher_apercu(gdf_final)

        # 6. Sauvegarder le shapefile enrichi
        sauvegarder_shapefile(gdf_final, output_parcellaire_path)

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

        print("\n📝 Prochaines étapes :")
        print("  1. Vérifier le shapefile enrichi dans QGIS ou autre SIG")
        print("  2. Utiliser ce fichier pour créer typeDeSolParZH.shp")
        print("  3. Ce fichier sert de base géométrique pour la consolidation finale")

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
