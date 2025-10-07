"""
05-creation-polygone-meteo.py

Script de création du fichier polygoneMeteoFrance.shp pour MAELIA
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Génère l'enveloppe géographique globale de la zone d'étude pour 
             associer les données climatiques dans MAELIA

Ce script :
- Charge le parcellaire enrichi
- Fusionne tous les polygones en une seule entité géographique
- Calcule les coordonnées du centroïde (POSX, POSY)
- Crée les attributs requis (ID_PDG, ALTI_MOY)
- Exporte le shapefile polygoneMeteoFrance.shp
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
ID_POLYGONE = '0001'      # Identifiant du polygone météo
ALTITUDE_MOYENNE = 0.0    # Altitude moyenne (valeur par défaut)


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
    Fusionne tous les polygones du parcellaire en une seule géométrie.

    Args:
        gdf (GeoDataFrame): Parcellaire

    Returns:
        geometry: Polygone unique représentant l'enveloppe de la zone
    """
    print("\n🔀 Fusion de tous les polygones en une seule entité...")

    # Utiliser union_all() au lieu de unary_union (déprécié)
    try:
        zone_etude_poly = gdf.union_all()
    except AttributeError:
        # Fallback pour les versions plus anciennes de GeoPandas
        zone_etude_poly = gdf.unary_union

    print(f"  ✓ Fusion réussie")
    print(f"  ✓ Type de géométrie : {zone_etude_poly.geom_type}")

    return zone_etude_poly


def calculer_centroid(geometrie):
    """
    Calcule le centroïde d'une géométrie.

    Args:
        geometrie: Géométrie dont on veut le centroïde

    Returns:
        Point: Centroïde de la géométrie
    """
    print("\n📍 Calcul du centroïde de la zone d'étude...")

    centroid = geometrie.centroid

    print(f"  ✓ Centroïde calculé")
    print(f"    POSX : {centroid.x:.4f}")
    print(f"    POSY : {centroid.y:.4f}")

    return centroid


def creer_geodataframe_meteo(geometrie, centroid, crs):
    """
    Crée le GeoDataFrame final pour le polygone météo.

    Args:
        geometrie: Polygone de la zone d'étude
        centroid: Point du centroïde
        crs: Système de coordonnées de référence

    Returns:
        GeoDataFrame: GeoDataFrame avec le polygone météo
    """
    print("\n🌍 Création du GeoDataFrame météo...")

    gdf_meteo = gpd.GeoDataFrame(
        {
            'ID_PDG': [ID_POLYGONE],
            'POSX': [centroid.x],
            'POSY': [centroid.y],
            'ALTI_MOY': [ALTITUDE_MOYENNE]
        },
        geometry=[geometrie],
        crs=crs
    )

    print(f"  ✓ GeoDataFrame créé")
    print(f"    Lignes : {len(gdf_meteo)}")
    print(f"    Colonnes : {list(gdf_meteo.columns)}")

    return gdf_meteo


def sauvegarder_shapefile(gdf, output_path):
    """
    Sauvegarde le GeoDataFrame en shapefile.

    Args:
        gdf (GeoDataFrame): GeoDataFrame à sauvegarder
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du shapefile polygoneMeteoFrance.shp...")

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
    print("RÉSUMÉ DU POLYGONE MÉTÉO")
    print("="*70)

    print(f"\n📊 Attributs du polygone :")
    for col in gdf.columns:
        if col != 'geometry':
            valeur = gdf[col].iloc[0]
            if isinstance(valeur, float):
                print(f"  • {col} : {valeur:.4f}")
            else:
                print(f"  • {col} : {valeur}")

    print(f"\n🌍 Géométrie :")
    geom = gdf.geometry.iloc[0]
    print(f"  • Type : {geom.geom_type}")
    print(f"  • Système de coordonnées : {gdf.crs}")

    # Calculer la surface si possible
    try:
        surface_m2 = geom.area
        surface_ha = surface_m2 / 10000
        print(f"  • Surface : {surface_ha:.2f} ha ({surface_m2:.2f} m²)")
    except Exception:
        pass


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DU POLYGONE MÉTÉO")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_parcellaire_path = base_dir / "data" / "sols" / \
        "shapefiles" / "processed" / "parcellaire_enrichi.shp"
    output_meteo_poly_path = base_dir / "tests" / \
        "modeleCommun" / "meteo" / "polygoneMeteoFrance.shp"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Parcellaire enrichi : {input_parcellaire_path}")
    print(f"📤 Polygone météo : {output_meteo_poly_path}\n")

    # Traitement des données
    try:
        # 1. Charger le parcellaire
        gdf_parcellaire = charger_parcellaire(input_parcellaire_path)

        # 2. Fusionner tous les polygones
        zone_etude_poly = fusionner_parcelles(gdf_parcellaire)

        # 3. Calculer le centroïde
        centroid = calculer_centroid(zone_etude_poly)

        # 4. Créer le GeoDataFrame final
        gdf_meteo = creer_geodataframe_meteo(
            zone_etude_poly,
            centroid,
            gdf_parcellaire.crs
        )

        # 5. Afficher un résumé
        afficher_resume(gdf_meteo)

        # 6. Sauvegarder le shapefile
        sauvegarder_shapefile(gdf_meteo, output_meteo_poly_path)

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

        print("\n📝 Prochaines étapes :")
        print("  1. Vérifier le shapefile dans QGIS ou autre SIG")
        print("  2. Ce polygone sera utilisé pour associer les données climatiques")
        print("  3. Intégrer dans le module météo de MAELIA")

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
