"""
02c-ajout-donnees-expertes.py

Script d'enrichissement des données de sols avec la littérature scientifique et le dire d'experts
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Complète la table de synthèse avec les données manquantes issues de la 
             littérature (thèses) et du dire d'experts

Ce script :
- Charge la table de synthèse agrégée créée par le script 02b
- Ajoute les variables globales (PIRM, PRO, CSTRU) depuis la littérature/expertise
- Ajoute les variables par couche (KSAT, P, EG, CAL) depuis la littérature/expertise
- Crée les identifiants requis par MAELIA (ID_ZH, STU_DOM, ID_SOL)
- Nettoie et réorganise les colonnes pour le format final
- Exporte la table enrichie et complète
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# CONSTANTES
# ============================================================================
# Valeurs globales fixes
ID_ZONE_HYDRO = 'SSM1'  # Identifiant de la zone hydrographique
PROFONDEUR_SOL = 60     # Profondeur totale du sol (cm)
STRUCTURE_SOL = 0.5     # Qualité de la structure (note experte)
PROFONDEUR_H1 = 30      # Profondeur cumulative horizon 1 (cm)
PROFONDEUR_H2 = 60      # Profondeur cumulative horizon 2 (cm)
ELEMENTS_GROSSIERS = 0  # Teneur en éléments grossiers (%)
TENEUR_CALCAIRE = 0     # Teneur en calcaire (%)


# ============================================================================
# DICTIONNAIRES DE DONNÉES EXPERTES
# ============================================================================
# PIRM : Infiltrabilité du sol (mm/h)
# Source : Thèse de Waly Faye + Hypothèses
PIRM_MAP = {
    'dior_cb_avec_arbr': 840.48,
    'dior_cb_sans_arbr': 696.00,
    'dior_cc_avec_arbr': 840.48,      # Hypothèse: cc_avec_arbr ≈ cb_avec_arbr
    'dior_cc_sans_arbr': 696.00,      # Hypothèse: cc_sans_arbr ≈ cb_sans_arbr
    'dekk_cb_avec_arbr': 420.24,      # Hypothèse: dekk ≈ 50% de dior
    'dekk_cb_sans_arbr': 348.00,      # Hypothèse: dekk ≈ 50% de dior
    'dekk/mbel_cb_avec_arbr': 420.24,  # Hypothèse: dekk/mbel ≈ dekk
    'dekk/mbel_cb_sans_arbr': 348.00  # Hypothèse: dekk/mbel ≈ dekk
}

# KSAT : Conductivité hydraulique à saturation (mm/h)
# Source : Thèse de Waly Faye + Hypothèses
KSAT_PROFIL_MAP = {
    'dior_cb_avec_arbr': 674.64,
    'dior_cb_sans_arbr': 480.24,
    'dekk_cb_avec_arbr': 322.74,
    'dekk_cb_sans_arbr': 296.28,
    'dior_cc_avec_arbr': 674.64,      # Hypothèse
    'dior_cc_sans_arbr': 480.24,      # Hypothèse
    'dekk/mbel_cb_avec_arbr': 322.74,  # Hypothèse
    'dekk/mbel_cb_sans_arbr': 296.28  # Hypothèse
}

# Facteur de répartition KSAT entre horizons
KSAT2_FACTOR = 0.75  # KSAT2 = 75% de KSAT1


# ============================================================================
# FONCTIONS D'AJOUT DE VARIABLES
# ============================================================================
def ajouter_pirm(df):
    """
    Ajoute la variable PIRM (infiltrabilité du sol) en mm/h.

    Args:
        df (DataFrame): Table de synthèse

    Returns:
        DataFrame: Table enrichie avec PIRM
    """
    print("\n🔹 Ajout de PIRM (Infiltrabilité du sol)")
    print("  Source : Thèse de Waly Faye + Hypothèses agronomiques")

    df['PIRM'] = df['ZONE_PEDO'].map(PIRM_MAP)

    # Vérifier que toutes les valeurs ont été trouvées
    valeurs_manquantes = df['PIRM'].isnull().sum()
    if valeurs_manquantes > 0:
        print(f"  ⚠️  {valeurs_manquantes} valeur(s) manquante(s) détectée(s)")
    else:
        print(f"  ✓ Toutes les valeurs affectées")

    print(f"  Plage : {df['PIRM'].min():.2f} - {df['PIRM'].max():.2f} mm/h")

    return df


def ajouter_ksat(df):
    """
    Ajoute les variables KSAT1 et KSAT2 (conductivité hydraulique) en mm/h.

    Args:
        df (DataFrame): Table de synthèse

    Returns:
        DataFrame: Table enrichie avec KSAT1 et KSAT2
    """
    print("\n🔹 Ajout de KSAT (Conductivité hydraulique à saturation)")
    print("  Source : Thèse de Waly Faye + Hypothèses")
    print("  Répartition : KSAT2 = 75% de KSAT1")

    # Créer colonne temporaire avec valeur de profil
    df['ksat_profil'] = df['ZONE_PEDO'].map(KSAT_PROFIL_MAP)

    # Appliquer la répartition
    df['KSAT1'] = df['ksat_profil']
    df['KSAT2'] = df['ksat_profil'] * KSAT2_FACTOR

    # Supprimer la colonne temporaire
    df = df.drop(columns=['ksat_profil'])

    print(
        f"  ✓ KSAT1 : {df['KSAT1'].min():.2f} - {df['KSAT1'].max():.2f} mm/h")
    print(
        f"  ✓ KSAT2 : {df['KSAT2'].min():.2f} - {df['KSAT2'].max():.2f} mm/h")

    return df


def ajouter_variables_fixes(df):
    """
    Ajoute les variables avec valeurs fixes (PRO, CSTRU, P1, P2, EG, CAL).

    Args:
        df (DataFrame): Table de synthèse

    Returns:
        DataFrame: Table enrichie
    """
    print("\n🔹 Ajout des variables fixes")

    # Variables globales
    print("  Variables globales :")
    df['PRO'] = PROFONDEUR_SOL
    print(f"    ✓ PRO (Profondeur totale) : {PROFONDEUR_SOL} cm")

    df['CSTRU'] = STRUCTURE_SOL
    print(f"    ✓ CSTRU (Qualité structure) : {STRUCTURE_SOL}")

    # Profondeurs des horizons
    print("  Profondeurs des horizons :")
    df['P1'] = PROFONDEUR_H1
    df['P2'] = PROFONDEUR_H2
    print(f"    ✓ P1 : {PROFONDEUR_H1} cm (profondeur cumulative H1)")
    print(f"    ✓ P2 : {PROFONDEUR_H2} cm (profondeur cumulative H2)")

    # Éléments grossiers et calcaire
    print("  Autres propriétés (dire d'expert) :")
    df['EG1'] = ELEMENTS_GROSSIERS
    df['EG2'] = ELEMENTS_GROSSIERS
    print(f"    ✓ EG1, EG2 (Éléments grossiers) : {ELEMENTS_GROSSIERS}%")

    df['CAL1'] = TENEUR_CALCAIRE
    df['CAL2'] = TENEUR_CALCAIRE
    print(f"    ✓ CAL1, CAL2 (Calcaire) : {TENEUR_CALCAIRE}%")

    return df


def ajouter_identifiants(df):
    """
    Ajoute les identifiants requis par MAELIA (ID_ZH, STU_DOM, ID_SOL).

    Args:
        df (DataFrame): Table de synthèse

    Returns:
        DataFrame: Table enrichie avec identifiants
    """
    print("\n🔹 Ajout des identifiants MAELIA")

    # ID_ZH : Identifiant de la zone hydrographique
    df['ID_ZH'] = ID_ZONE_HYDRO
    print(f"  ✓ ID_ZH : {ID_ZONE_HYDRO}")

    # STU_DOM : Classification selon texture dominante
    df['STU_DOM'] = np.where(
        df['ZONE_PEDO'].str.contains('dior'),
        'sableux',
        'argileux'
    )
    print(f"  ✓ STU_DOM : Classification texture (sableux/argileux)")

    # Nettoyage de ZONE_PEDO (remplacer '/' par nomenclature propre)
    print("\n  Nettoyage de ZONE_PEDO :")
    print(f"    Avant : {df['ZONE_PEDO'].unique().tolist()}")
    df['ZONE_PEDO'] = df['ZONE_PEDO'].str.replace(
        'dekk/mbel', 'dekkMbel', regex=False)
    print(f"    Après : {df['ZONE_PEDO'].unique().tolist()}")

    # ID_SOL : Identifiant unique composite
    df['ID_SOL'] = df.apply(
        lambda row: f"{row['ID_ZH']}-{row['STU_DOM']}-{row['ZONE_PEDO']}",
        axis=1
    )
    print(f"  ✓ ID_SOL : Identifiant unique composite créé")

    return df


def nettoyer_colonnes(df):
    """
    Supprime les colonnes intermédiaires non nécessaires pour le modèle.

    Args:
        df (DataFrame): Table complète

    Returns:
        DataFrame: Table nettoyée
    """
    print("\n🔹 Nettoyage des colonnes intermédiaires")

    colonnes_a_supprimer = ['C1', 'C2', 'N1', 'N2']
    colonnes_existantes = [
        col for col in colonnes_a_supprimer if col in df.columns]

    if colonnes_existantes:
        df = df.drop(columns=colonnes_existantes)
        print(
            f"  ✓ {len(colonnes_existantes)} colonne(s) supprimée(s) : {', '.join(colonnes_existantes)}")
    else:
        print("  ℹ️  Aucune colonne intermédiaire à supprimer")

    return df


def reorganiser_colonnes(df):
    """
    Réorganise les colonnes dans l'ordre requis par MAELIA.

    Args:
        df (DataFrame): Table complète

    Returns:
        DataFrame: Table avec colonnes réorganisées
    """
    print("\n🔹 Réorganisation des colonnes")

    # Définir l'ordre final
    colonnes_identifiants = ['ID_SOL', 'ID_ZH', 'STU_DOM', 'ZONE_PEDO']
    colonnes_globales = ['PIRM', 'CSTRU', 'PRO']
    colonnes_par_couche = [
        'P1', 'P2',
        'ARG1', 'ARG2',
        'SAB1', 'SAB2',
        'DAH1', 'DAH2',
        'MO1', 'MO2',
        'PH1', 'PH2',
        'CN1', 'CN2',
        'HCC1', 'HCC2',
        'HPFP1', 'HPFP2',
        'RUPRH1', 'RUPRH2',
        'KSAT1', 'KSAT2',
        'EG1', 'EG2',
        'CAL1', 'CAL2'
    ]

    ordre_final = colonnes_identifiants + colonnes_globales + colonnes_par_couche

    # Vérifier que toutes les colonnes existent
    colonnes_manquantes = [col for col in ordre_final if col not in df.columns]
    if colonnes_manquantes:
        print(f"  ⚠️  Colonnes manquantes : {', '.join(colonnes_manquantes)}")

    # Appliquer l'ordre
    colonnes_disponibles = [col for col in ordre_final if col in df.columns]
    df = df[colonnes_disponibles]

    print(f"  ✓ Colonnes réorganisées ({len(colonnes_disponibles)} colonnes)")
    print(f"  ✓ Ordre : Identifiants → Globales → Par couche")

    return df


def afficher_resume(df):
    """
    Affiche un résumé de la table finale.

    Args:
        df (DataFrame): Table finale
    """
    print("\n" + "="*70)
    print("RÉSUMÉ DE LA TABLE FINALE")
    print("="*70)

    print(f"\n📊 Dimensions :")
    print(f"  Lignes (types de sol) : {df.shape[0]}")
    print(f"  Colonnes (variables) : {df.shape[1]}")

    print(f"\n🏷️  Types de sol (ZONE_PEDO) :")
    for zone in df['ZONE_PEDO'].values:
        print(f"  • {zone}")

    print(f"\n📋 Groupes de variables :")
    print(f"  • Identifiants : 4 colonnes (ID_SOL, ID_ZH, STU_DOM, ZONE_PEDO)")
    print(f"  • Variables globales : 3 colonnes (PIRM, CSTRU, PRO)")
    print(f"  • Variables par couche : {df.shape[1] - 7} colonnes")

    print(f"\n📈 Statistiques clés :")
    print(f"  • PIRM : {df['PIRM'].min():.2f} - {df['PIRM'].max():.2f} mm/h")
    if 'KSAT1' in df.columns:
        print(
            f"  • KSAT1 : {df['KSAT1'].min():.2f} - {df['KSAT1'].max():.2f} mm/h")
    if 'MO1' in df.columns:
        print(f"  • MO1 : {df['MO1'].min():.4f} - {df['MO1'].max():.4f} %")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("ENRICHISSEMENT DES DONNÉES DE SOLS")
    print("Ajout des données de littérature et dire d'experts")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_csv_path = base_dir / "data" / "sols" / \
        "csv" / "processed" / "donnees_typesDeSol.csv"
    output_csv_path = base_dir / "data" / "sols" / "csv" / \
        "processed" / "donnees_typesDeSol_enrichies.csv"

    print(f"\n📍 Répertoire du projet: {base_dir}")
    print(f"📥 Fichier d'entrée: {input_csv_path}")
    print(f"📤 Fichier de sortie: {output_csv_path}\n")

    # Vérifier l'existence du fichier d'entrée
    if not input_csv_path.exists():
        print(f"❌ Erreur: Le fichier {input_csv_path} n'existe pas!")
        print("   Veuillez d'abord exécuter le script 02b-extraction-agregation-donnees.py")
        sys.exit(1)

    # Traitement des données
    try:
        # 1. Charger la table de synthèse
        print("📂 Chargement de la table de synthèse...")
        df_synthese = pd.read_csv(input_csv_path, sep=';')
        print(
            f"✓ {df_synthese.shape[0]} lignes × {df_synthese.shape[1]} colonnes chargées")

        # Afficher les ZONE_PEDO présentes
        print(f"\n  Types de sol détectés :")
        for zone in df_synthese['ZONE_PEDO'].values:
            print(f"    • {zone}")

        # 2. Ajouter les variables issues de la littérature
        print("\n" + "="*70)
        print("AJOUT DES DONNÉES DE LITTÉRATURE")
        print("="*70)

        df_synthese = ajouter_pirm(df_synthese)
        df_synthese = ajouter_ksat(df_synthese)

        # 3. Ajouter les variables fixes (dire d'expert)
        print("\n" + "="*70)
        print("AJOUT DES DONNÉES EXPERTES")
        print("="*70)

        df_synthese = ajouter_variables_fixes(df_synthese)

        # 4. Ajouter les identifiants MAELIA
        print("\n" + "="*70)
        print("CRÉATION DES IDENTIFIANTS")
        print("="*70)

        df_synthese = ajouter_identifiants(df_synthese)

        # 5. Nettoyage
        print("\n" + "="*70)
        print("NETTOYAGE ET FINALISATION")
        print("="*70)

        df_synthese = nettoyer_colonnes(df_synthese)
        df_synthese = reorganiser_colonnes(df_synthese)

        # 6. Afficher un résumé
        afficher_resume(df_synthese)

        # 7. Sauvegarder
        print("\n" + "="*70)
        print("SAUVEGARDE")
        print("="*70)

        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        df_synthese.to_csv(output_csv_path, index=False, sep=';')

        print(f"\n💾 Table enrichie sauvegardée avec succès")
        print(f"  ✓ {output_csv_path}")
        print(
            f"  ✓ {df_synthese.shape[0]} lignes × {df_synthese.shape[1]} colonnes")

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
