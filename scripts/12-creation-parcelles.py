"""
12-creation-parcelles.py

Script de création du fichier parcelles.shp pour le module agricole MAELIA
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Génère le shapefile des parcelles en subdivisant les îlots
             Dans ce cas, chaque îlot = 1 parcelle

Ce script :
- Charge le fichier ilots.shp comme base
- Crée un identifiant unique pour chaque parcelle (ID_PARCELL)
- Calcule la surface de chaque parcelle en hectares
- Assigne une séquence de cultures de manière aléatoire
- Ajoute les colonnes requises par MAELIA
- Exporte le shapefile final parcelles.shp
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
# CONSTANTES
# ============================================================================
# Séquences de cultures possibles
SEQUENCES_CULTURES = [
    "arachide_mil_jachere",
    "mil_arachide_jachere_arachide"
]

# Valeurs par défaut pour les attributs MAELIA
POURCENTAGE_DEFAULT = 1.0
INDEX_DEP_DEFAULT = 'NA'
CULT_REF_DEFAULT = ''
EXPREST_DEFAULT = 'NA'


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def charger_ilots(ilots_path):
    """
    Charge le shapefile des îlots.

    Args:
        ilots_path (Path): Chemin vers ilots.shp

    Returns:
        GeoDataFrame: Îlots chargés
    """
    print("📂 Chargement du fichier ilots.shp...")

    if not ilots_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {ilots_path}")

    gdf = gpd.read_file(ilots_path)

    print(f"  ✓ {len(gdf)} îlots chargés")
    print(f"  ✓ {gdf.shape[1]} colonnes")
    print(f"  ✓ CRS : {gdf.crs}")

    return gdf


def creer_identifiants_parcelles(gdf):
    """
    Crée les identifiants uniques pour chaque parcelle.
    Format: ID_ILOT_001 (car 1 parcelle par îlot).

    Args:
        gdf (GeoDataFrame): Îlots

    Returns:
        GeoDataFrame: Avec colonne ID_PARCELL
    """
    print("\n🏷️  Création des identifiants de parcelles...")

    # Créer ID_PARCELL au format "ID_ILOT_001"
    gdf['ID_PARCELL'] = gdf['ID_ILOT'].astype(str) + '_001'

    print(f"  ✓ {len(gdf)} identifiants créés")
    print(f"  Format : ID_ILOT_001")
    print(f"  Exemple : {gdf['ID_PARCELL'].iloc[0]}")

    return gdf


def calculer_surfaces(gdf):
    """
    Calcule la surface de chaque parcelle en hectares.

    Args:
        gdf (GeoDataFrame): Parcelles

    Returns:
        GeoDataFrame: Avec colonne SURFACE
    """
    print("\n📐 Calcul des surfaces...")

    # Calculer la surface en m² puis convertir en hectares
    gdf['SURFACE'] = gdf.geometry.area / 10000

    # Statistiques
    surface_totale = gdf['SURFACE'].sum()
    surface_min = gdf['SURFACE'].min()
    surface_max = gdf['SURFACE'].max()
    surface_moyenne = gdf['SURFACE'].mean()

    print(f"  ✓ Surfaces calculées en hectares")
    print(f"  Surface totale : {surface_totale:.2f} ha")
    print(f"  Surface min : {surface_min:.4f} ha")
    print(f"  Surface max : {surface_max:.4f} ha")
    print(f"  Surface moyenne : {surface_moyenne:.4f} ha")

    return gdf


def assigner_sequences(gdf, seed=42):
    """
    Assigne une séquence de cultures de manière aléatoire à chaque parcelle.

    Args:
        gdf (GeoDataFrame): Parcelles
        seed (int): Graine pour la reproductibilité

    Returns:
        GeoDataFrame: Avec colonne SEQUENCE
    """
    print("\n🌾 Assignation des séquences de cultures...")

    # Définir la graine pour la reproductibilité
    np.random.seed(seed)

    # Assigner aléatoirement une séquence
    gdf['SEQUENCE'] = np.random.choice(SEQUENCES_CULTURES, size=len(gdf))

    # Afficher la répartition
    print(f"  ✓ Séquences assignées")
    print(f"\n  Répartition des séquences :")
    repartition = gdf['SEQUENCE'].value_counts()
    for seq, count in repartition.items():
        pourcentage = (count / len(gdf)) * 100
        print(f"    • {seq}")
        print(f"      {count} parcelles ({pourcentage:.1f}%)")

    return gdf


def ajouter_colonnes_maelia(gdf):
    """
    Ajoute les colonnes restantes requises par MAELIA.

    Args:
        gdf (GeoDataFrame): Parcelles

    Returns:
        GeoDataFrame: Avec toutes les colonnes MAELIA
    """
    print("\n➕ Ajout des colonnes MAELIA...")

    colonnes_ajoutees = {
        'POURCENTAG': POURCENTAGE_DEFAULT,  # Pourcentage de la parcelle
        'INDEX_DEP': INDEX_DEP_DEFAULT,     # Index de dépendance
        'CULT_REF': CULT_REF_DEFAULT,       # Culture de référence
        'EXPREST': EXPREST_DEFAULT          # Expérimentation restriction
    }

    for col, valeur in colonnes_ajoutees.items():
        gdf[col] = valeur
        valeur_affichage = f"'{valeur}'" if valeur else 'vide'
        print(f"  ✓ {col} : {valeur_affichage}")

    return gdf


def selectionner_colonnes_finales(gdf):
    """
    Sélectionne et ordonne les colonnes finales pour le shapefile.

    Args:
        gdf (GeoDataFrame): Parcelles complètes

    Returns:
        GeoDataFrame: Parcelles avec colonnes finales uniquement
    """
    print("\n📋 Sélection des colonnes finales...")

    colonnes_finales = [
        'ID_PARCELL',
        'ID_ILOT',
        'ID_EXPL',
        'SEQUENCE',
        'POURCENTAG',
        'INDEX_DEP',
        'CULT_REF',
        'SURFACE',
        'EXPREST',
        'geometry'
    ]

    # Vérifier que toutes les colonnes existent
    colonnes_manquantes = [
        col for col in colonnes_finales if col not in gdf.columns]

    if colonnes_manquantes:
        raise KeyError(
            f"Colonnes manquantes : {', '.join(colonnes_manquantes)}")

    gdf_final = gdf[colonnes_finales].copy()

    print(f"  ✓ {len(colonnes_finales)} colonnes sélectionnées")
    print(f"  Ordre : {', '.join(colonnes_finales[:5])}...")

    return gdf_final


def sauvegarder_shapefile(gdf, output_path):
    """
    Sauvegarde le GeoDataFrame en shapefile.

    Args:
        gdf (GeoDataFrame): Parcelles finales
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du shapefile parcelles.shp...")

    # Créer le dossier de sortie
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    gdf.to_file(output_path, driver='ESRI Shapefile', encoding='utf-8')

    print(f"  ✓ Shapefile sauvegardé : {output_path}")
    print(f"  ✓ {len(gdf)} parcelles × {gdf.shape[1]} colonnes")


def afficher_apercu(gdf):
    """
    Affiche un aperçu du GeoDataFrame final.

    Args:
        gdf (GeoDataFrame): GeoDataFrame final
    """
    print("\n" + "="*70)
    print("APERÇU DU FICHIER PARCELLES")
    print("="*70)

    print(
        f"\n📊 Dimensions : {gdf.shape[0]} parcelles × {gdf.shape[1]} colonnes")

    print(f"\n📋 Premières parcelles :")
    colonnes_apercu = ['ID_PARCELL', 'ID_ILOT',
                       'ID_EXPL', 'SEQUENCE', 'SURFACE']
    print(gdf[colonnes_apercu].head(10).to_string(index=False))

    # Statistiques
    print(f"\n📈 Statistiques :")
    print(f"  • Nombre d'exploitants distincts : {gdf['ID_EXPL'].nunique()}")
    print(f"  • Nombre d'îlots distincts : {gdf['ID_ILOT'].nunique()}")
    print(f"  • Nombre de séquences distinctes : {gdf['SEQUENCE'].nunique()}")
    print(f"  • Surface totale : {gdf['SURFACE'].sum():.2f} ha")

    # Répartition des séquences
    print(f"\n  Séquences de cultures :")
    for seq, count in gdf['SEQUENCE'].value_counts().items():
        print(f"    • {seq}: {count}")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DU FICHIER PARCELLES")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_ilots_path = base_dir / "tests" / \
        "modeleAgricole" / "ilots" / "dansZone" / "ilots.shp"
    output_parcelles_path = base_dir / "tests" / \
        "modeleAgricole" / "ilots" / "dansZone" / "parcelles.shp"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Fichier ilots : {input_ilots_path}")
    print(f"📤 Fichier parcelles : {output_parcelles_path}\n")

    # Traitement des données
    try:
        # 1. Charger les îlots
        gdf_ilots = charger_ilots(input_ilots_path)

        # 2. Créer une copie pour travailler
        gdf_parcelles = gdf_ilots.copy()

        # 3. Créer les identifiants de parcelles
        gdf_parcelles = creer_identifiants_parcelles(gdf_parcelles)

        # 4. Calculer les surfaces
        gdf_parcelles = calculer_surfaces(gdf_parcelles)

        # 5. Assigner les séquences de cultures
        gdf_parcelles = assigner_sequences(gdf_parcelles, seed=42)

        # 6. Ajouter les colonnes MAELIA
        gdf_parcelles = ajouter_colonnes_maelia(gdf_parcelles)

        # 7. Sélectionner les colonnes finales
        gdf_final = selectionner_colonnes_finales(gdf_parcelles)

        # 8. Afficher un aperçu
        afficher_apercu(gdf_final)

        # 9. Sauvegarder le shapefile
        sauvegarder_shapefile(gdf_final, output_parcelles_path)

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

        print("\n📝 Informations importantes :")
        print("  • Relation îlot-parcelle : 1 îlot = 1 parcelle")
        print("  • Format ID_PARCELL : ID_ILOT_001")
        print("  • Séquences assignées aléatoirement (seed=42)")

        print("\n📝 Prochaines étapes :")
        print("  1. Vérifier le shapefile dans QGIS ou autre SIG")
        print("  2. Ajuster les séquences si nécessaire")
        print("  3. Intégrer parcelles.shp dans le module agricole MAELIA")

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
