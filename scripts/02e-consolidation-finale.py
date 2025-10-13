"""
02e-consolidation-finale.py

Script de consolidation finale pour créer le fichier typeDeSolParZH.shp
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Consolide les données attributaires agrégées avec la géométrie des parcelles
             pour créer la couche de sol finale requise par MAELIA

Ce script :
- Charge le parcellaire enrichi (.shp) et la table de synthèse (.csv)
- Joint les propriétés de sol agrégées à chaque parcelle via ZONE_PEDO
- Filtre les ZONE_PEDO valides
- Visualise le parcellaire coloré par ZONE_PEDO (validation qualitative)
- Fusionne (dissolve) les parcelles adjacentes de même ZONE_PEDO
- Sauvegarde le GeoDataFrame final en shapefile
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import sys
import warnings
import matplotlib.pyplot as plt

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# CONSTANTES
# ============================================================================
# Liste des 8 ZONE_PEDO valides
ZONES_PEDO_VALIDES = [
    'dior_cb_avec_arbr',
    'dior_cb_sans_arbr',
    'dior_cc_avec_arbr',
    'dior_cc_sans_arbr',
    'dekk_cb_avec_arbr',
    'dekk_cb_sans_arbr',
    'dekkMbel_cb_avec_arbr',
    'dekkMbel_cb_sans_arbr'
]


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def charger_donnees_sources(parcellaire_path, synthese_path):
    """
    Charge le shapefile du parcellaire et la table de synthèse CSV.

    Args:
        parcellaire_path (Path): Chemin vers le shapefile du parcellaire enrichi
        synthese_path (Path): Chemin vers la table de synthèse CSV

    Returns:
        tuple: (gdf_parcellaire, df_synthese)
    """
    print("📂 Chargement des données sources...")

    # Charger le shapefile
    if not parcellaire_path.exists():
        raise FileNotFoundError(f"Shapefile non trouvé : {parcellaire_path}")

    gdf = gpd.read_file(parcellaire_path)
    print(
        f"  ✓ Parcellaire enrichi : {len(gdf)} polygones × {gdf.shape[1]} colonnes")

    # Charger la table de synthèse
    if not synthese_path.exists():
        raise FileNotFoundError(f"Fichier CSV non trouvé : {synthese_path}")

    df = pd.read_csv(synthese_path, sep=';')
    print(f"  ✓ Table de synthèse : {len(df)} lignes × {df.shape[1]} colonnes")

    # Vérifier la présence de la clé de jointure
    colonne_cle = 'ZONE_PEDO'
    if colonne_cle not in gdf.columns:
        raise KeyError(
            f"Colonne '{colonne_cle}' manquante dans le parcellaire")
    if colonne_cle not in df.columns:
        raise KeyError(
            f"Colonne '{colonne_cle}' manquante dans la table de synthèse")

    print(
        f"  ✓ Clé de jointure '{colonne_cle}' présente dans les deux fichiers")

    return gdf, df


def filtrer_zones_valides(gdf):
    """
    Filtre le parcellaire pour ne garder que les ZONE_PEDO valides.

    Args:
        gdf (GeoDataFrame): Parcellaire complet

    Returns:
        GeoDataFrame: Parcellaire filtré
    """
    print("\n🔍 Filtrage des ZONE_PEDO valides...")

    initial = len(gdf)
    gdf_filtre = gdf[gdf['ZONE_PEDO'].isin(ZONES_PEDO_VALIDES)].copy()
    final = len(gdf_filtre)

    print(f"  Avant filtrage : {initial} polygones")
    print(f"  Après filtrage : {final} polygones")
    print(f"  Supprimés : {initial - final} polygones")

    if final == 0:
        raise ValueError("Aucun polygone valide après filtrage!")

    return gdf_filtre


def joindre_proprietes_sols(gdf_parcellaire, df_synthese):
    """
    Joint les propriétés de sol agrégées au parcellaire via ZONE_PEDO.

    Args:
        gdf_parcellaire (GeoDataFrame): Parcellaire filtré avec géométries
        df_synthese (DataFrame): Table de synthèse des propriétés de sol

    Returns:
        GeoDataFrame: Parcellaire enrichi avec toutes les propriétés
    """
    print("\n🔗 Jointure des propriétés de sol...")

    # Simplifier le parcellaire (garder seulement ZONE_PEDO et geometry)
    print("  • Préparation du parcellaire pour la jointure")
    gdf_geom = gdf_parcellaire[['ZONE_PEDO', 'geometry']].copy()

    # Effectuer la jointure
    print("  • Jointure avec la table de synthèse")
    gdf_final = gdf_geom.merge(
        df_synthese,
        on='ZONE_PEDO',
        how='left'
    )

    # Vérifier le résultat
    print(
        f"  • Résultat : {gdf_final.shape[0]} polygones × {gdf_final.shape[1]} colonnes")

    # Vérifier qu'il n'y a pas de valeurs manquantes
    valeurs_manquantes = gdf_final['ID_SOL'].isnull().sum()

    if valeurs_manquantes > 0:
        print(f"  ⚠️  {valeurs_manquantes} polygone(s) sans correspondance")
    else:
        print(f"  ✓ Tous les polygones enrichis avec succès")

    return gdf_final


def visualiser_parcellaire(gdf, titre, colonne_couleur, output_path=None):
    """
    Crée une visualisation du parcellaire coloré par une colonne.

    Args:
        gdf (GeoDataFrame): Parcellaire à visualiser
        titre (str): Titre de la carte
        colonne_couleur (str): Colonne pour la coloration
        output_path (Path, optional): Chemin pour sauvegarder l'image
    """
    print(f"\n📊 Création de la carte : {titre}")

    fig, ax = plt.subplots(1, 1, figsize=(15, 15))

    gdf.plot(
        column=colonne_couleur,
        ax=ax,
        legend=True,
        cmap='tab20',
        edgecolor='black',
        linewidth=0.2,
        legend_kwds={'loc': 'upper left', 'bbox_to_anchor': (1, 1)}
    )

    ax.set_title(titre, fontsize=16, pad=20)
    ax.set_xlabel("Longitude (m)", fontsize=12)
    ax.set_ylabel("Latitude (m)", fontsize=12)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Carte sauvegardée : {output_path}")

    plt.show()
    plt.close()


def fusionner_polygones(gdf):
    """
    Fusionne (dissolve) les polygones adjacents de même ZONE_PEDO.

    Args:
        gdf (GeoDataFrame): Parcellaire avec toutes les parcelles

    Returns:
        GeoDataFrame: Polygones fusionnés par ZONE_PEDO
    """
    print("\n🔀 Fusion des polygones adjacents...")

    print(f"  Avant fusion : {len(gdf)} polygones")

    # Fusionner par ZONE_PEDO
    # aggfunc='first' : pour les colonnes non-géométriques, garder la première valeur
    # (correct car identiques pour une même ZONE_PEDO)
    gdf_fusion = gdf.dissolve(by='ZONE_PEDO', aggfunc='first').reset_index()

    print(f"  Après fusion : {len(gdf_fusion)} polygones")
    print(f"  Réduction : {len(gdf) - len(gdf_fusion)} polygones fusionnés")

    # Afficher les ZONE_PEDO finales
    print(f"\n  Types de sol dans le fichier final :")
    for zone in gdf_fusion['ZONE_PEDO'].values:
        print(f"    • {zone}")

    return gdf_fusion


def sauvegarder_shapefile(gdf, output_path):
    """
    Sauvegarde le GeoDataFrame final en shapefile.

    Args:
        gdf (GeoDataFrame): Polygones fusionnés avec propriétés
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du shapefile final...")

    # Créer le dossier de sortie si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    gdf.to_file(output_path, driver='ESRI Shapefile', encoding='utf-8')

    print(f"  ✓ Shapefile sauvegardé avec succès")
    print(f"  ✓ Emplacement : {output_path}")
    print(f"  ✓ {gdf.shape[0]} polygones × {gdf.shape[1]} colonnes")

    # Lister les fichiers créés
    fichiers_crees = list(output_path.parent.glob(f"{output_path.stem}.*"))
    print(f"\n  Fichiers créés ({len(fichiers_crees)}) :")
    for fichier in sorted(fichiers_crees):
        print(f"    • {fichier.name}")


def afficher_resume_final(gdf):
    """
    Affiche un résumé du GeoDataFrame final.

    Args:
        gdf (GeoDataFrame): GeoDataFrame final
    """
    print("\n" + "="*70)
    print("RÉSUMÉ DU FICHIER FINAL")
    print("="*70)

    print(f"\n📊 Dimensions :")
    print(f"  Polygones (unités de sol) : {gdf.shape[0]}")
    print(f"  Attributs (colonnes) : {gdf.shape[1]}")

    print(f"\n🏷️  Unités de sol (ZONE_PEDO) :")
    for zone in sorted(gdf['ZONE_PEDO'].values):
        print(f"  • {zone}")

    print(f"\n📋 Colonnes principales :")
    colonnes_cles = ['ID_SOL', 'ID_ZH', 'STU_DOM',
                     'ZONE_PEDO', 'PIRM', 'PRO', 'CSTRU']
    colonnes_disponibles = [col for col in colonnes_cles if col in gdf.columns]
    for col in colonnes_disponibles:
        print(f"  • {col}")

    if 'PIRM' in gdf.columns:
        print(f"\n📈 Quelques statistiques :")
        print(
            f"  • PIRM (Infiltrabilité) : {gdf['PIRM'].min():.2f} - {gdf['PIRM'].max():.2f} mm/h")

    if 'MO1' in gdf.columns:
        print(
            f"  • MO1 (Matière organique H1) : {gdf['MO1'].min():.4f} - {gdf['MO1'].max():.4f} %")

    # Système de coordonnées
    print(f"\n🌍 Système de coordonnées :")
    print(f"  CRS : {gdf.crs}")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CONSOLIDATION FINALE - CRÉATION DE typeDeSolParZH.shp")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_parcellaire_path = base_dir / "data" / "sols" / \
        "shapefiles" / "processed" / "parcellaire_enrichi.shp"
    input_synthese_path = base_dir / "data" / "sols" / "csv" / \
        "processed" / "donnees_typesDeSol_enrichies.csv"
    output_shapefile_path = base_dir / "tests" / \
        "modeleCommun" / "typesDeSol" / "typeDeSolParZH.shp"

    # Chemins pour les visualisations (optionnel)
    output_dir = base_dir / "outputs" / "visualisations"
    viz_avant_fusion = output_dir / "parcellaire_avant_fusion.png"
    viz_apres_fusion = output_dir / "parcellaire_apres_fusion.png"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Parcellaire enrichi : {input_parcellaire_path}")
    print(f"📥 Table de synthèse : {input_synthese_path}")
    print(f"📤 Shapefile final : {output_shapefile_path}\n")

    # Traitement des données
    try:
        # 1. Charger les données sources
        gdf_parcellaire, df_synthese = charger_donnees_sources(
            input_parcellaire_path,
            input_synthese_path
        )

        # 2. Filtrer les ZONE_PEDO valides
        gdf_filtre = filtrer_zones_valides(gdf_parcellaire)

        # 3. Joindre les propriétés de sol
        gdf_enrichi = joindre_proprietes_sols(gdf_filtre, df_synthese)

        # 4. Visualisation avant fusion (optionnel)
        print("\n" + "="*70)
        print("VISUALISATION AVANT FUSION")
        print("="*70)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            visualiser_parcellaire(
                gdf_enrichi,
                "Répartition Spatiale des Unités de Sol (ID_SOL)",
                'ID_SOL',
                viz_avant_fusion
            )
        except Exception as e:
            print(f"  ⚠️  Visualisation ignorée : {e}")

        # 5. Fusionner les polygones
        print("\n" + "="*70)
        print("FUSION DES POLYGONES")
        print("="*70)

        gdf_fusion = fusionner_polygones(gdf_enrichi)

        # 6. Visualisation après fusion (optionnel)
        print("\n" + "="*70)
        print("VISUALISATION APRÈS FUSION")
        print("="*70)

        try:
            visualiser_parcellaire(
                gdf_fusion,
                "Carte des Unités de Sol Homogènes (après fusion)",
                'ZONE_PEDO',
                viz_apres_fusion
            )
        except Exception as e:
            print(f"  ⚠️  Visualisation ignorée : {e}")

        # 7. Sauvegarder le shapefile final
        print("\n" + "="*70)
        print("SAUVEGARDE")
        print("="*70)

        sauvegarder_shapefile(gdf_fusion, output_shapefile_path)

        # 8. Afficher un résumé final
        afficher_resume_final(gdf_fusion)

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
