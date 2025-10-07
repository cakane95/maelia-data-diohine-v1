"""
11-creation-regles-ferti.py

Script de création du fichier reglesDeDecisions_fertilisation.csv pour MAELIA
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Génère le fichier de règles de fertilisation pour les 6 ITK de Sasseme
             à partir d'un fichier template

Ce script :
- Charge le fichier template des règles de fertilisation
- Crée la structure pour les 6 ITK Sasseme
- Applique les paramètres de fertilisation (NPK, doses, périodes)
- Exporte le fichier final reglesDeDecisions_fertilisation.csv
"""

import pandas as pd
from pathlib import Path
import sys
import warnings

# Supprimer les avertissements
warnings.filterwarnings('ignore')


# ============================================================================
# CONSTANTES
# ============================================================================
# Liste des 6 ITK de Sasseme
ITK_SASSEME = [
    'arachide_precMil',
    'arachide_precJachere',
    'jachere_precMil',
    'jachere_precArachide',
    'mil_precArachide',
    'mil_precMil'
]

# Paramètres de fertilisation à appliquer
PARAMETRES_FERTILISATION = {
    'FERTIALT_NOM_ALTERNATIVE': 'fertilisation minerale',
    'FERTIALT_ORDRE_ALTERNATIVE': 1,
    'FERTIALT_ORDRE_APPORT': 1,
    'FERTIALT_NOM_PRODUIT': 'NPK',
    'FERTIALT_DOSE': 300,            # kg/ha
    'FERTIALT_DOSE_P': 20,           # kg/ha de P
    'FERTIALT_DOSE_K': 10,           # kg/ha de K
    'FERTIALT_PROF_WSOL': 0,
    'FERTIALT_AGRIW': 'oui',
    'FERTIALT_OUTIL': 0,
    'FERTIALT_TPS_TRAVAIL': 0.0625,  # 2 jours/ha → ha/h
    'FERTIALT_N_PASSAGES': 1,
    'FERTIALT_OT_SIMULTANEE': 'NA',
    'FERTIALT_N_SOUS_PERIODES': 1,
    'FERTIALT_DEBUT': 166,           # 15 Juin (jour julien)
    'FERTIALT_FIN': 242              # 30 Août (jour julien)
}


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def charger_fichier_source(fichier_path):
    """
    Charge le fichier template des règles de fertilisation.

    Args:
        fichier_path (Path): Chemin vers le fichier source

    Returns:
        DataFrame: Template chargé
    """
    print("📂 Chargement du fichier source...")

    if not fichier_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {fichier_path}")

    df = pd.read_csv(fichier_path, sep=';')

    print(f"  ✓ Template chargé")
    print(f"  ✓ {len(df)} lignes (paramètres)")
    print(f"  ✓ {df.shape[1]} colonnes")

    return df


def creer_structure_sasseme(df_source):
    """
    Crée la structure du DataFrame pour les ITK Sasseme.

    Args:
        df_source (DataFrame): Template source

    Returns:
        DataFrame: Structure avec colonnes pour les 6 ITK
    """
    print("\n🏗️  Création de la structure pour Sasseme...")

    # Garder les 2 premières colonnes de base
    colonnes_base = df_source.columns[:2].tolist()
    df_sasseme = df_source[colonnes_base].copy()

    # Ajouter une colonne pour chaque ITK, initialisée à "NA"
    for itk in ITK_SASSEME:
        df_sasseme[itk] = "NA"

    print(f"  ✓ Structure créée")
    print(f"  ✓ Colonnes de base : {colonnes_base}")
    print(f"  ✓ ITK ajoutés : {len(ITK_SASSEME)}")

    return df_sasseme


def appliquer_parametres_fertilisation(df):
    """
    Applique les paramètres de fertilisation aux colonnes ITK.

    Args:
        df (DataFrame): DataFrame avec structure Sasseme

    Returns:
        DataFrame: DataFrame avec paramètres appliqués
    """
    print("\n⚙️  Application des paramètres de fertilisation...")

    nb_parametres_appliques = 0

    for parametre, valeur in PARAMETRES_FERTILISATION.items():
        # Trouver la ligne correspondant au paramètre
        mask = df['FERTIALT_NOM_ITK'] == parametre

        if mask.any():
            # Appliquer la valeur à toutes les colonnes ITK
            df.loc[mask, ITK_SASSEME] = valeur
            nb_parametres_appliques += 1

            # Afficher l'application
            if isinstance(valeur, (int, float)):
                print(f"  ✓ {parametre}: {valeur}")
            else:
                print(f"  ✓ {parametre}: '{valeur}'")

    print(f"\n  Total : {nb_parametres_appliques} paramètres appliqués")

    return df


def valider_resultats(df):
    """
    Valide le DataFrame final et affiche des statistiques.

    Args:
        df (DataFrame): DataFrame final
    """
    print("\n🔍 Validation des résultats...")

    # Compter les valeurs non-NA pour chaque ITK
    print("\n  Paramètres configurés par ITK :")
    for itk in ITK_SASSEME:
        nb_configures = (df[itk] != "NA").sum()
        print(f"    • {itk}: {nb_configures}/{len(df)} paramètres")

    # Vérifier les paramètres clés
    parametres_cles = [
        'FERTIALT_NOM_PRODUIT',
        'FERTIALT_DOSE',
        'FERTIALT_DEBUT',
        'FERTIALT_FIN'
    ]

    print("\n  Vérification des paramètres clés :")
    for param in parametres_cles:
        mask = df['FERTIALT_NOM_ITK'] == param
        if mask.any():
            valeur = df.loc[mask, ITK_SASSEME[0]].iloc[0]
            print(f"    ✓ {param}: {valeur}")


def sauvegarder_fichier(df, output_path):
    """
    Sauvegarde le DataFrame final en CSV.

    Args:
        df (DataFrame): DataFrame à sauvegarder
        output_path (Path): Chemin de sortie
    """
    print("\n💾 Sauvegarde du fichier...")

    # Créer le dossier de sortie
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sauvegarder
    df.to_csv(output_path, sep=';', index=False)

    print(f"  ✓ Fichier sauvegardé : {output_path}")
    print(f"  ✓ {len(df)} lignes × {df.shape[1]} colonnes")


def afficher_apercu(df):
    """
    Affiche un aperçu du DataFrame final.

    Args:
        df (DataFrame): DataFrame final
    """
    print("\n" + "="*70)
    print("APERÇU DU FICHIER FINAL")
    print("="*70)

    print(f"\n📊 Dimensions : {df.shape[0]} lignes × {df.shape[1]} colonnes")

    print(f"\n📋 ITK configurés :")
    for itk in ITK_SASSEME:
        print(f"  • {itk}")

    print(f"\n📝 Premiers paramètres (15 premières lignes) :")
    # Afficher seulement les colonnes essentielles pour la lisibilité
    colonnes_apercu = ['FERTIALT_NOM_ITK'] + ITK_SASSEME[:3]
    print(df[colonnes_apercu].head(15).to_string(index=False))

    print("\n  ... (voir le fichier complet pour tous les paramètres)")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DES RÈGLES DE FERTILISATION")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_regles_path = base_dir / "data" / "ITK" / "csv" / \
        "raw" / "reglesDeDecisions_fertilisation.csv"
    output_ferti_path = base_dir / "tests" / "modeleAgricole" / \
        "culture" / "reglesDeDecisions_fertilisation.csv"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Fichier template : {input_regles_path}")
    print(f"📤 Fichier de sortie : {output_ferti_path}\n")

    # Traitement des données
    try:
        # 1. Charger le fichier source
        df_source = charger_fichier_source(input_regles_path)

        # 2. Créer la structure pour Sasseme
        df_sasseme = creer_structure_sasseme(df_source)

        # 3. Appliquer les paramètres de fertilisation
        df_final = appliquer_parametres_fertilisation(df_sasseme)

        # 4. Valider les résultats
        valider_resultats(df_final)

        # 5. Afficher un aperçu
        afficher_apercu(df_final)

        # 6. Sauvegarder le fichier
        sauvegarder_fichier(df_final, output_ferti_path)

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

        print("\n📝 Informations sur la fertilisation :")
        print(f"  • Produit : NPK")
        print(f"  • Dose totale : 300 kg/ha")
        print(f"  • Dont P : 20 kg/ha")
        print(f"  • Dont K : 10 kg/ha")
        print(f"  • Période : 15 juin - 30 août (jours 166-242)")
        print(f"  • Nombre de passages : 1")

        print("\n📝 Prochaines étapes :")
        print("  1. Vérifier le fichier généré")
        print("  2. Ajuster les paramètres si nécessaire")
        print("  3. Intégrer dans le module agricole MAELIA")

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
