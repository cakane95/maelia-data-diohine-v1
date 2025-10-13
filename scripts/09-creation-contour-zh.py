"""
09-creation-contour-zh.py

Script de création du fichier contourZH.shp et copie de donneesMNT_ZH.csv
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Crée le shapefile du contour de la Zone Hydrographique avec calcul 
             de surface et copie le fichier des données MNT

Ce script :
- Charge le parcellaire enrichi
- Vérifie que le CRS est projeté (nécessaire pour calcul de surface)
- Fusionne tous les polygones en une seule entité
- Calcule la surface en m² et en ha
- Crée les attributs requis (Code_Zone, Surface, Area_ha)
- Exporte le shapefile contourZH.shp
- Copie le fichier donneesMNT_ZH.csv
"""

import geopandas as gpd
import shutil
from pathlib import Path
import sys
import warnings

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# CONSTANTES
# ============================================================================
CODE_ZONE = 'SSM1'  # Code de la zone hydrographique


# ============================================================================
# FONCTIONS UTILITAIRES - CONTOUR ZH
# ============================================================================
def charger_et_verifier_parcellaire(parcellaire_path):
    """
    Charge le parcellaire et vérifie que le CRS est projeté.

    Args:
        parcellaire_path (Path): Chemin vers le shapefile

    Returns:
        GeoDataFrame: Parcellaire chargé

    Raises:
        TypeError: Si le CRS n'est pas projeté
    """
    print("📂 Chargement du parcellaire enrichi...")

    if not parcellaire_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {parcellaire_path}")

    gdf = gpd.read_file(parcellaire_path)
    print(f"  ✓ {len(gdf)} polygones chargés")
    print(f"  ✓ CRS : {gdf.crs}")

    # Vérification critique : le CRS doit être projeté pour les calculs de surface
    print("\n🔍 Vérification du système de coordonnées...")

    if not gdf.crs.is_projected:
        raise TypeError(
            "Le CRS doit être projeté (ex: UTM) pour calculer des surfaces en mètres.\n"
            f"CRS actuel : {gdf.crs}\n"
            "Veuillez reprojeter le shapefile en UTM ou système métrique."
        )

    print(f"  ✓ CRS projeté détecté : {gdf.crs.name}")
    print(f"  ✓ Unités en mètres confirmées")

    return gdf


def fusionner_et_calculer_surface(gdf):
    """
    Fusionne tous les polygones et calcule la surface totale.

    Args:
        gdf (GeoDataFrame): Parcellaire

    Returns:
        tuple: (geometrie_fusionnée, surface_m2, surface_ha)
    """
    print("\n🔀 Fusion de tous les polygones...")

    # Fusionner tous les polygones
    try:
        contour_poly = gdf.union_all()
    except AttributeError:
        contour_poly = gdf.unary_union

    print(f"  ✓ Fusion réussie")
    print(f"  ✓ Type de géométrie : {contour_poly.geom_type}")

    # Calculer la surface
    print("\n📏 Calcul de la surface...")

    # Créer un GeoDataFrame temporaire pour le calcul
    gdf_temp = gpd.GeoDataFrame(geometry=[contour_poly], crs=gdf.crs)

    surface_m2 = gdf_temp.geometry.area.iloc[0]
    surface_ha = surface_m2 / 10000
    surface_km2 = surface_ha / 100

    print(f"  ✓ Surface calculée")
    print(f"    • {surface_m2:,.2f} m²")
    print(f"    • {surface_ha:,.2f} ha")
    print(f"    • {surface_km2:,.2f} km²")

    return contour_poly, surface_m2, surface_ha


def creer_geodataframe_contour(geometrie, surface_m2, surface_ha, crs):
    """
    Crée le GeoDataFrame final du contour avec attributs.

    Args:
        geometrie: Polygone fusionné
        surface_m2 (float): Surface en m²
        surface_ha (float): Surface en ha
        crs: Système de coordonnées

    Returns:
        GeoDataFrame: GeoDataFrame avec attributs finaux
    """
    print("\n🌊 Création du GeoDataFrame final...")

    gdf_contour = gpd.GeoDataFrame(
        {
            'Code_Zone': [CODE_ZONE],
            'Surface': [surface_m2],
            'Area_ha': [surface_ha]
        },
        geometry=[geometrie],
        crs=crs
    )

    # Ordonner les colonnes
    gdf_contour = gdf_contour[['Code_Zone', 'Surface', 'Area_ha', 'geometry']]

    print(f"  ✓ GeoDataFrame créé")
    print(f"    • Code_Zone : {CODE_ZONE}")
    print(f"    • Surface : {surface_m2:,.2f} m²")
    print(f"    • Area_ha : {surface_ha:,.2f} ha")

    return gdf_contour


def sauvegarder_shapefile_contour(gdf, output_path):
    """
    Sauvegarde le GeoDataFrame du contour en shapefile.

    Args:
        gdf (GeoDataFrame): GeoDataFrame à sauvegarder
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du shapefile contourZH.shp...")

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


# ============================================================================
# FONCTIONS UTILITAIRES - COPIE MNT
# ============================================================================
def verifier_fichier_source(source_path):
    """
    Vérifie l'existence du fichier source.

    Args:
        source_path (Path): Chemin source

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Fichier source introuvable : {source_path}")


def copier_fichier_mnt(source_path, destination_path):
    """
    Copie le fichier donneesMNT_ZH.csv.

    Args:
        source_path (Path): Chemin source
        destination_path (Path): Chemin destination
    """
    print("\n📋 Copie du fichier donneesMNT_ZH.csv...")

    # Vérifier le fichier source
    verifier_fichier_source(source_path)

    # Créer le dossier de destination
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    # Copier
    shutil.copy2(source_path, destination_path)

    print(f"  ✓ Fichier copié avec succès")
    print(f"    Source : {source_path}")
    print(f"    Destination : {destination_path}")


def afficher_resume(gdf_contour):
    """
    Affiche un résumé du fichier créé.

    Args:
        gdf_contour (GeoDataFrame): GeoDataFrame du contour
    """
    print("\n" + "="*70)
    print("RÉSUMÉ DU CONTOUR ZH")
    print("="*70)

    print(f"\n📊 Attributs :")
    print(f"  • Code_Zone : {gdf_contour['Code_Zone'].iloc[0]}")
    print(f"  • Surface : {gdf_contour['Surface'].iloc[0]:,.2f} m²")
    print(f"  • Area_ha : {gdf_contour['Area_ha'].iloc[0]:,.2f} ha")

    print(f"\n🌍 Géométrie :")
    geom = gdf_contour.geometry.iloc[0]
    print(f"  • Type : {geom.geom_type}")
    print(f"  • CRS : {gdf_contour.crs}")

    # Bounds
    bounds = geom.bounds
    print(f"\n📐 Emprise :")
    print(f"  • X : {bounds[0]:.2f} à {bounds[2]:.2f}")
    print(f"  • Y : {bounds[1]:.2f} à {bounds[3]:.2f}")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DU CONTOUR ZH ET COPIE DES DONNÉES MNT")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()

    # Entrées
    input_parcellaire_path = base_dir / "data" / "sols" / \
        "shapefiles" / "processed" / "parcellaire_enrichi.shp"
    source_mnt_path = base_dir / "data" / "hydro" / \
        "csv" / "raw" / "donneesMNT_ZH.csv"

    # Sorties
    output_contour_path = base_dir / "tests" / "modeleHydrographique" / \
        "zonesHydrographiques" / "contourZH.shp"
    destination_mnt_path = base_dir / "tests" / "modeleHydrographique" / \
        "zonesHydrographiques" / "donneesMNT_ZH.csv"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Parcellaire : {input_parcellaire_path}")
    print(f"📥 Données MNT : {source_mnt_path}")
    print(f"📤 Contour ZH : {output_contour_path}")
    print(f"📤 MNT destination : {destination_mnt_path}\n")

    # Traitement des données
    try:
        # === PARTIE 1 : CRÉATION DU CONTOUR ZH ===
        print("=" * 70)
        print("PARTIE 1 : CRÉATION DU CONTOUR ZH")
        print("=" * 70)

        # 1. Charger et vérifier le parcellaire
        gdf_parcellaire = charger_et_verifier_parcellaire(
            input_parcellaire_path)

        # 2. Fusionner et calculer la surface
        contour_poly, surface_m2, surface_ha = fusionner_et_calculer_surface(
            gdf_parcellaire)

        # 3. Créer le GeoDataFrame final
        gdf_contour = creer_geodataframe_contour(
            contour_poly,
            surface_m2,
            surface_ha,
            gdf_parcellaire.crs
        )

        # 4. Sauvegarder le shapefile
        sauvegarder_shapefile_contour(gdf_contour, output_contour_path)

        # 5. Afficher un résumé
        afficher_resume(gdf_contour)

        # === PARTIE 2 : COPIE DES DONNÉES MNT ===
        print("\n" + "=" * 70)
        print("PARTIE 2 : COPIE DES DONNÉES MNT")
        print("=" * 70)

        # 6. Copier le fichier MNT
        copier_fichier_mnt(source_mnt_path, destination_mnt_path)

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

        print("\n📝 Fichiers créés :")
        print(f"  1. contourZH.shp : {surface_ha:.2f} ha")
        print(f"  2. donneesMNT_ZH.csv : Données d'altitude")

    except FileNotFoundError as e:
        print(f"\n❌ Erreur : Fichier introuvable")
        print(f"   {e}")
        sys.exit(1)
    except TypeError as e:
        print(f"\n❌ Erreur : Problème de CRS")
        print(f"   {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
