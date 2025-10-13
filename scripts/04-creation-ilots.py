"""
04-creation-ilots.py

Script de création du fichier ilots.shp pour le module agricole MAELIA
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Crée le shapefile des îlots en assemblant les informations du parcellaire,
             des exploitations et des sols

Ce script :
- Charge le parcellaire enrichi, les exploitations et la table de synthèse des sols
- Joint les informations pour attribuer ID_EXPL, ID_SOL et ID_ZH à chaque îlot
- Crée un identifiant unique pour chaque îlot (ID_ILOT)
- Ajoute les colonnes requises par MAELIA (irrigation, pente, équipements)
- Exporte le shapefile final ilots.shp
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
import sys
import warnings

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# CONSTANTES
# ============================================================================
PREFIXE_ID_ILOT = 'SSM1'  # Préfixe pour ID_EXPL

# Valeurs par défaut pour les attributs MAELIA
CARACT_IRR_DEFAULT = 'N'  # Pas d'irrigation
MATERIEL_DEFAULT = 0      # Pas de matériel
PENTE_MOY_DEFAULT = 0     # Pente moyenne nulle
PENTE_SWAT_DEFAULT = 0    # Pente SWAT nulle


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def charger_donnees_sources(parcellaire_path, exploitations_path, synthese_path):
    """
    Charge toutes les données sources nécessaires.

    Args:
        parcellaire_path (Path): Chemin vers le parcellaire enrichi
        exploitations_path (Path): Chemin vers exploitations.csv
        synthese_path (Path): Chemin vers la table de synthèse des sols

    Returns:
        tuple: (gdf_parcellaire, df_exploitations, df_synthese)
    """
    print("📂 Chargement des données sources...")

    # Vérifier l'existence des fichiers
    fichiers = {
        'Parcellaire': parcellaire_path,
        'Exploitations': exploitations_path,
        'Synthèse sols': synthese_path
    }

    for nom, chemin in fichiers.items():
        if not chemin.exists():
            raise FileNotFoundError(f"Fichier {nom} non trouvé : {chemin}")

    # Charger les fichiers
    gdf_parcellaire = gpd.read_file(parcellaire_path)
    df_exploitations = pd.read_csv(exploitations_path, sep=';')
    df_synthese = pd.read_csv(synthese_path, sep=';')

    print(f"  ✓ Parcellaire : {len(gdf_parcellaire)} parcelles")
    print(f"  ✓ Exploitations : {len(df_exploitations)} exploitants")
    print(f"  ✓ Synthèse sols : {len(df_synthese)} types de sol")

    return gdf_parcellaire, df_exploitations, df_synthese


def joindre_informations_sols(gdf_parcellaire, df_synthese):
    """
    Joint les informations de sol (ID_SOL, ID_ZH) au parcellaire via ZONE_PEDO.

    Args:
        gdf_parcellaire (GeoDataFrame): Parcellaire enrichi
        df_synthese (DataFrame): Table de synthèse des sols

    Returns:
        GeoDataFrame: Parcellaire avec ID_SOL et ID_ZH
    """
    print("\n🔗 Jointure avec les informations de sol...")

    # Sélectionner seulement les colonnes nécessaires
    df_sols_mini = df_synthese[['ZONE_PEDO', 'ID_SOL', 'ID_ZH']].copy()

    # Effectuer la jointure
    gdf_enrichi = gdf_parcellaire.merge(
        df_sols_mini,
        on='ZONE_PEDO',
        how='left'
    )

    # Vérifier les valeurs manquantes
    nb_manquants = gdf_enrichi['ID_SOL'].isnull().sum()

    if nb_manquants > 0:
        print(f"  ⚠️  {nb_manquants} parcelle(s) sans correspondance de sol")
    else:
        print(f"  ✓ Toutes les parcelles enrichies avec ID_SOL et ID_ZH")

    return gdf_enrichi


def joindre_informations_exploitants(gdf, gdf_parcellaire_original):
    """
    Joint les informations d'exploitants (ID_EXPL) au parcellaire.
    Recrée la correspondance NOM_UTILIS -> ID_EXPL.

    Args:
        gdf (GeoDataFrame): Parcellaire enrichi avec sols
        gdf_parcellaire_original (GeoDataFrame): Parcellaire original

    Returns:
        GeoDataFrame: Parcellaire avec ID_EXPL
    """
    print("\n🔗 Jointure avec les informations d'exploitants...")

    # Recréer la table de correspondance NOM_UTILIS -> ID_EXPL
    # (même logique que dans le script 03-creation-exploitations.py)
    df_map_expl = gdf_parcellaire_original[['NOM_UTILIS']].copy()
    df_map_expl = df_map_expl.drop_duplicates().reset_index(drop=True)
    df_map_expl['ID_EXPL'] = PREFIXE_ID_ILOT + '-' + \
        (df_map_expl.index + 1).astype(str).str.zfill(4)

    print(f"  • Correspondance créée pour {len(df_map_expl)} exploitants")

    # Effectuer la jointure
    gdf_enrichi = gdf.merge(df_map_expl, on='NOM_UTILIS', how='left')

    # Vérifier les valeurs manquantes
    nb_manquants = gdf_enrichi['ID_EXPL'].isnull().sum()

    if nb_manquants > 0:
        print(
            f"  ⚠️  {nb_manquants} parcelle(s) sans correspondance d'exploitant")
    else:
        print(f"  ✓ Toutes les parcelles enrichies avec ID_EXPL")

    return gdf_enrichi


def creer_identifiants_ilots(gdf):
    """
    Crée les identifiants uniques pour chaque îlot (ID_ILOT).

    Args:
        gdf (GeoDataFrame): Parcellaire enrichi

    Returns:
        GeoDataFrame: Parcellaire avec ID_ILOT
    """
    print("\n🏷️  Création des identifiants d'îlots (ID_ILOT)...")

    # Réinitialiser l'index
    gdf = gdf.reset_index(drop=True)

    # Créer ID_ILOT (numérotation simple 1, 2, 3, ...)
    gdf['ID_ILOT'] = gdf.index + 1

    print(f"  ✓ {len(gdf)} identifiants créés (1 à {len(gdf)})")

    return gdf


def ajouter_colonnes_maelia(gdf):
    """
    Ajoute les colonnes restantes requises par MAELIA avec valeurs par défaut.

    Args:
        gdf (GeoDataFrame): Parcellaire enrichi

    Returns:
        GeoDataFrame: Parcellaire avec toutes les colonnes MAELIA
    """
    print("\n➕ Ajout des colonnes MAELIA...")

    colonnes_ajoutees = {
        'CARACT_IRR': CARACT_IRR_DEFAULT,      # Caractéristique irrigation
        'MATERIEL': MATERIEL_DEFAULT,          # Matériel disponible
        'LISTE_EQUIS': None,                   # Liste des équipements (vide)
        'PENTE_MOY': PENTE_MOY_DEFAULT,        # Pente moyenne
        'PENTE_SWAT': PENTE_SWAT_DEFAULT,      # Pente SWAT
        'EQU_0': None,                         # Équipement 0 (vide)
        'EQU_1': None,                         # Équipement 1 (vide)
        'EQU_2': None                          # Équipement 2 (vide)
    }

    for col, valeur in colonnes_ajoutees.items():
        gdf[col] = valeur
        print(f"  ✓ {col} : {valeur if valeur is not None else 'NULL'}")

    return gdf


def selectionner_colonnes_finales(gdf):
    """
    Sélectionne et ordonne les colonnes finales pour le shapefile.

    Args:
        gdf (GeoDataFrame): Parcellaire complet

    Returns:
        GeoDataFrame: Parcellaire avec colonnes finales uniquement
    """
    print("\n📋 Sélection des colonnes finales...")

    colonnes_finales = [
        'ID_ILOT',
        'ID_EXPL',
        'ID_SOL',
        'ID_ZH',
        'CARACT_IRR',
        'MATERIEL',
        'LISTE_EQUIS',
        'PENTE_MOY',
        'PENTE_SWAT',
        'EQU_0',
        'EQU_1',
        'EQU_2',
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
    print(f"  ✓ Ordre : {', '.join(colonnes_finales[:4])}...")

    return gdf_final


def sauvegarder_shapefile(gdf, output_path):
    """
    Sauvegarde le GeoDataFrame en shapefile.

    Args:
        gdf (GeoDataFrame): Parcellaire final
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du shapefile ilots.shp...")

    # Créer le dossier de sortie
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    gdf.to_file(output_path, driver='ESRI Shapefile', encoding='utf-8')

    print(f"  ✓ Shapefile sauvegardé : {output_path}")
    print(f"  ✓ {len(gdf)} îlots × {gdf.shape[1]} colonnes")

    # Note sur les noms de colonnes
    print("\n  ℹ️  Note : Les noms de colonnes > 10 caractères sont tronqués")
    print("      par le format Shapefile (ex: LISTE_EQUIS → LISTE_EQUI)")


def afficher_apercu(gdf):
    """
    Affiche un aperçu du GeoDataFrame final.

    Args:
        gdf (GeoDataFrame): GeoDataFrame final
    """
    print("\n" + "="*70)
    print("APERÇU DU FICHIER ILOTS")
    print("="*70)

    print(f"\n📊 Dimensions : {gdf.shape[0]} îlots × {gdf.shape[1]} colonnes")

    print(f"\n📋 Premiers îlots :")
    colonnes_cles = ['ID_ILOT', 'ID_EXPL', 'ID_SOL', 'ID_ZH', 'CARACT_IRR']
    print(gdf[colonnes_cles].head(10).to_string(index=False))

    # Statistiques
    print(f"\n📈 Statistiques :")
    print(f"  • Nombre d'exploitants distincts : {gdf['ID_EXPL'].nunique()}")
    print(f"  • Nombre de types de sol distincts : {gdf['ID_SOL'].nunique()}")
    print(f"  • Nombre de zones hydro distinctes : {gdf['ID_ZH'].nunique()}")

    # Répartition par caractéristique irrigation
    print(f"\n  Répartition irrigation :")
    for val, count in gdf['CARACT_IRR'].value_counts().items():
        print(f"    • {val} : {count} îlots")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DU FICHIER ILOTS")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()

    # Entrées
    input_parcellaire_path = base_dir / "data" / "sols" / \
        "shapefiles" / "processed" / "parcellaire_enrichi.shp"
    input_exploitations_path = base_dir / "tests" / \
        "modeleAgricole" / "agriculteurs" / "exploitations.csv"
    input_synthese_path = base_dir / "data" / "sols" / "csv" / \
        "processed" / "donnees_typesDeSol_enrichies.csv"

    # Sortie
    output_ilots_path = base_dir / "tests" / \
        "modeleAgricole" / "ilots" / "dansZone" / "ilots.shp"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Parcellaire enrichi : {input_parcellaire_path}")
    print(f"📥 Exploitations : {input_exploitations_path}")
    print(f"📥 Synthèse sols : {input_synthese_path}")
    print(f"📤 Shapefile ilots : {output_ilots_path}\n")

    # Traitement des données
    try:
        # 1. Charger les données sources
        gdf_parcellaire, df_exploitations, df_synthese = charger_donnees_sources(
            input_parcellaire_path,
            input_exploitations_path,
            input_synthese_path
        )

        # 2. Joindre les informations de sol
        gdf_ilots = joindre_informations_sols(gdf_parcellaire, df_synthese)

        # 3. Joindre les informations d'exploitants
        gdf_ilots = joindre_informations_exploitants(
            gdf_ilots, gdf_parcellaire)

        # 4. Créer les identifiants d'îlots
        gdf_ilots = creer_identifiants_ilots(gdf_ilots)

        # 5. Ajouter les colonnes MAELIA
        gdf_ilots = ajouter_colonnes_maelia(gdf_ilots)

        # 6. Sélectionner les colonnes finales
        gdf_final = selectionner_colonnes_finales(gdf_ilots)

        # 7. Afficher un aperçu
        afficher_apercu(gdf_final)

        # 8. Sauvegarder le shapefile
        sauvegarder_shapefile(gdf_final, output_ilots_path)

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
