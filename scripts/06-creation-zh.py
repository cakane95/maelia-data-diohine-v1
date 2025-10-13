"""
06-creation-zh.py

Script de création du fichier ZH.shp pour le module hydrographique MAELIA
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Génère la Zone Hydrographique unique de la zone d'étude

Ce script :
- Charge le parcellaire enrichi
- Fusionne tous les polygones en une seule entité géographique
- Crée l'attribut ID_ZH avec une valeur fixe
- Exporte le shapefile ZH.shp
"""

import geopandas as gpd
from pathlib import Path
import sys
import warnings

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# CONSTANTES
# ============================================================================
ID_ZONE_HYDRO = 1  # Identifiant de la zone hydrographique


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def charger_parcellaire(parcellaire_path):
    """
    Charge le shapefile du parcellaire enrichi.

    Args:
        parcellaire_path (Path): Chemin vers le shapefile

    Returns:
        GeoDataFrame: Parcellaire chargé
    """
    print("📂 Chargement du parcellaire enrichi...")

    if not parcellaire_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {parcellaire_path}")

    gdf = gpd.read_file(parcellaire_path)
    print(f"  ✓ {len(gdf)} polygones chargés")
    print(f"  ✓ CRS : {gdf.crs}")

    return gdf


def fusionner_parcelles(gdf):
    """
    Fusionne tous les polygones du parcellaire en une seule géométrie
    représentant la Zone Hydrographique.

    Args:
        gdf (GeoDataFrame): Parcellaire

    Returns:
        geometry: Polygone unique de la Zone Hydrographique
    """
    print("\n🔀 Fusion de tous les polygones en Zone Hydrographique unique...")

    # Utiliser union_all() au lieu de unary_union (déprécié)
    try:
        zone_hydro_poly = gdf.union_all()
    except AttributeError:
        # Fallback pour les versions plus anciennes de GeoPandas
        zone_hydro_poly = gdf.unary_union

    print(f"  ✓ Fusion réussie")
    print(f"  ✓ Type de géométrie : {zone_hydro_poly.geom_type}")

    # Calculer la surface si possible
    try:
        surface_m2 = zone_hydro_poly.area
        surface_ha = surface_m2 / 10000
        surface_km2 = surface_ha / 100
        print(
            f"  ✓ Surface totale : {surface_ha:.2f} ha ({surface_km2:.2f} km²)")
    except Exception:
        pass

    return zone_hydro_poly


def creer_geodataframe_zh(geometrie, crs):
    """
    Crée le GeoDataFrame final pour la Zone Hydrographique.

    Args:
        geometrie: Polygone de la Zone Hydrographique
        crs: Système de coordonnées de référence

    Returns:
        GeoDataFrame: GeoDataFrame avec la ZH
    """
    print("\n🌊 Création du GeoDataFrame de la Zone Hydrographique...")

    gdf_zh = gpd.GeoDataFrame(
        {'ID_ZH': [ID_ZONE_HYDRO]},
        geometry=[geometrie],
        crs=crs
    )

    print(f"  ✓ GeoDataFrame créé")
    print(f"    ID_ZH : {ID_ZONE_HYDRO}")
    print(f"    Nombre de polygones : 1")

    return gdf_zh


def sauvegarder_shapefile(gdf, output_path):
    """
    Sauvegarde le GeoDataFrame en shapefile.

    Args:
        gdf (GeoDataFrame): GeoDataFrame à sauvegarder
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du shapefile ZH.shp...")

    # Créer le dossier de sortie
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    gdf.to_file(output_path, driver='ESRI Shapefile', encoding='utf-8')

    print(f"  ✓ Fichier sauvegardé : {output_path}")

    # Lister les fichiers créés
    fichiers_crees = list(output_path.parent.glob(f"{output_path.stem}.*"))
    print(f"\n  Fichiers créés ({len(fichiers_crees)}) :")
    for fichier in sorted(fichiers_crees):
        print(f"    • {fichier.name}")


def afficher_resume(gdf):
    """
    Affiche un résumé du GeoDataFrame final.

    Args:
        gdf (GeoDataFrame): GeoDataFrame final
    """
    print("\n" + "="*70)
    print("RÉSUMÉ DE LA ZONE HYDROGRAPHIQUE")
    print("="*70)

    print(f"\n📊 Attributs :")
    print(f"  • ID_ZH : {gdf['ID_ZH'].iloc[0]}")

    print(f"\n🌍 Géométrie :")
    geom = gdf.geometry.iloc[0]
    print(f"  • Type : {geom.geom_type}")
    print(f"  • Système de coordonnées : {gdf.crs}")

    # Statistiques géométriques
    try:
        surface_m2 = geom.area
        surface_ha = surface_m2 / 10000
        surface_km2 = surface_ha / 100

        print(f"\n📏 Dimensions :")
        print(f"  • Surface : {surface_ha:.2f} ha")
        print(f"  • Surface : {surface_km2:.2f} km²")
        print(f"  • Surface : {surface_m2:.2f} m²")

        # Calculer les bounds
        bounds = geom.bounds
        print(f"\n📐 Emprise géographique :")
        print(f"  • X min : {bounds[0]:.2f}")
        print(f"  • Y min : {bounds[1]:.2f}")
        print(f"  • X max : {bounds[2]:.2f}")
        print(f"  • Y max : {bounds[3]:.2f}")

        largeur = bounds[2] - bounds[0]
        hauteur = bounds[3] - bounds[1]
        print(f"  • Largeur : {largeur:.2f} m")
        print(f"  • Hauteur : {hauteur:.2f} m")

    except Exception as e:
        print(f"  ⚠️  Impossible de calculer les statistiques : {e}")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DE LA ZONE HYDROGRAPHIQUE (ZH)")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_parcellaire_path = base_dir / "data" / "sols" / \
        "shapefiles" / "processed" / "parcellaire_enrichi.shp"
    output_zh_path = base_dir / "tests" / \
        "modeleHydrographique" / "zonesHydrographiques" / "ZH.shp"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Parcellaire enrichi : {input_parcellaire_path}")
    print(f"📤 Zone Hydrographique : {output_zh_path}\n")

    # Traitement des données
    try:
        # 1. Charger le parcellaire
        gdf_parcellaire = charger_parcellaire(input_parcellaire_path)

        # 2. Fusionner tous les polygones
        zone_hydro_poly = fusionner_parcelles(gdf_parcellaire)

        # 3. Créer le GeoDataFrame final
        gdf_zh = creer_geodataframe_zh(zone_hydro_poly, gdf_parcellaire.crs)

        # 4. Afficher un résumé
        afficher_resume(gdf_zh)

        # 5. Sauvegarder le shapefile
        sauvegarder_shapefile(gdf_zh, output_zh_path)

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
