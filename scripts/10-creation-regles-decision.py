"""
10-creation-regles-decision.py

Script de création du fichier reglesDeDecision.csv pour le module agricole MAELIA
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Génère les règles de décision pour le territoire de Sasseme à partir
             d'un fichier source, en créant 6 ITK spécifiques et en les paramétrant

Ce script :
- Charge le fichier source reglesDeDecisionsextended.csv
- Crée une structure pour 6 ITK spécifiques (arachide, jachere, mil)
- Remplit l'en-tête (12 premières lignes) pour définir les ITK
- Initialise toutes les opérations à "désactivé"
- Active et paramètre PREPA, SEMIS et RECOLTE via configuration
- Exporte le fichier reglesDeDecision.csv
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
# Liste des 6 ITK pour Sasseme
ITK_SASSEME = [
    'arachide_precMil',
    'arachide_precJachere',
    'jachere_precMil',
    'jachere_precArachide',
    'mil_precArachide',
    'mil_precMil'
]

# Configuration des opérations techniques
CONFIGURATION_SASSEME = {
    'PREPA': {
        'IS_PREPA': {'valeur': 'O'},
        'PREPA_TEMPS': {'valeur': 0.0417},
        'PREPA_DEBUT': {'valeur': 121},
        'PREPA_FIN': {'valeur': 151}
    },
    'SEMIS': {
        'IS_SEMIS': {'valeur': 'O'},
        'SEMIS_DEBUT': {'valeur': 152},
        'SEMIS_FIN': {'valeur': 181},
        # Paramètres spécifiques à l'arachide
        'SEMIS_CUMUL_PLUIE': {
            'valeur': 20,
            'condition': {'ligne_condition': 'ID_ESPECE', 'valeur_attendue': 'arachide'}
        },
        'SEMIS_N_J_CUMUL_PLUIE': {
            'valeur': 1,
            'condition': {'ligne_condition': 'ID_ESPECE', 'valeur_attendue': 'arachide'}
        }
    },
    'RECOLTE': {
        'IS_RECOLTE': {'valeur': 'O'},
        'RECOLTE_TEMPS': {'valeur': 0.0179},
        'RECOLTE_DEBUT': {'valeur': 258},
        'RECOLTE_FIN': {'valeur': 288}
    }
}


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def charger_fichier_source(source_path):
    """
    Charge le fichier source des règles de décision.

    Args:
        source_path (Path): Chemin vers le fichier source

    Returns:
        DataFrame: Règles de décision source
    """
    print("📂 Chargement du fichier source...")

    if not source_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {source_path}")

    df = pd.read_csv(source_path, sep=';')

    print(f"  ✓ {df.shape[0]} règles × {df.shape[1]} colonnes (ITK) chargées")

    return df


def creer_structure_itk(df_source, nouvelle_liste_itk):
    """
    Crée la structure du nouveau DataFrame avec les colonnes de base
    et de nouvelles colonnes vides pour les ITK.

    Args:
        df_source (DataFrame): DataFrame source
        nouvelle_liste_itk (list): Liste des nouveaux ITK

    Returns:
        DataFrame: Nouveau DataFrame avec structure cible
    """
    print("\n🏗️  Création de la structure pour les nouveaux ITK...")

    # Colonnes de base à conserver
    colonnes_base = ["NOM_ITK_AFFICHAGE", "X.", "gel"]

    # Créer le nouveau DataFrame
    df_cible = df_source[colonnes_base].copy()

    # Ajouter les colonnes pour les nouveaux ITK (vides)
    for itk in nouvelle_liste_itk:
        df_cible[itk] = pd.NA

    print(
        f"  ✓ Structure créée : {df_cible.shape[0]} lignes × {df_cible.shape[1]} colonnes")
    print(f"  ✓ {len(nouvelle_liste_itk)} colonnes ITK ajoutées")

    return df_cible


def ajouter_lignes_semis(df):
    """
    Ajoute les lignes de paramètres de pluie pour le semis si elles manquent.

    Args:
        df (DataFrame): DataFrame à modifier

    Returns:
        DataFrame: DataFrame avec lignes ajoutées si nécessaire
    """
    print("\n🌧️  Vérification des paramètres de semis...")

    ligne_cumul_pluie = 'SEMIS_CUMUL_PLUIE'
    ligne_n_j_cumul_pluie = 'SEMIS_N_J_CUMUL_PLUIE'

    if ligne_cumul_pluie in df['NOM_ITK_AFFICHAGE'].values:
        print("  ✓ Les lignes de paramètres de pluie existent déjà")
        return df

    print(f"  • Ligne '{ligne_cumul_pluie}' manquante, ajout en cours...")

    # Trouver où insérer (après la dernière ligne SEMIS_)
    lignes_semis = df[df['NOM_ITK_AFFICHAGE'].str.startswith(
        'SEMIS_', na=False)]

    if not lignes_semis.empty:
        index_insertion = lignes_semis.index[-1] + 1
    else:
        index_insertion = len(df)

    # Créer les nouvelles lignes
    nouvelle_ligne1 = pd.DataFrame({
        'NOM_ITK_AFFICHAGE': [ligne_cumul_pluie],
        'X.': ['[mm]'],
        'gel': ['NA']
    })

    nouvelle_ligne2 = pd.DataFrame({
        'NOM_ITK_AFFICHAGE': [ligne_n_j_cumul_pluie],
        'X.': ['[jour]'],
        'gel': ['NA']
    })

    # Insérer les lignes
    df_partie1 = df.iloc[:index_insertion]
    df_partie2 = df.iloc[index_insertion:]
    df = pd.concat([df_partie1, nouvelle_ligne1,
                   nouvelle_ligne2, df_partie2], ignore_index=True)

    print("  ✓ Lignes ajoutées avec succès")

    return df


def remplir_entete_itk(df_cible):
    """
    Remplit les 12 lignes d'en-tête pour chaque ITK.

    Args:
        df_cible (DataFrame): DataFrame avec structure vide

    Returns:
        DataFrame: DataFrame avec en-tête rempli
    """
    print("\n📝 Remplissage de l'en-tête des ITK...")

    # Colonnes des ITK (après les 3 colonnes de base)
    colonnes_itk = df_cible.columns[3:]

    nb_itk_traites = 0

    # Remplir l'en-tête pour chaque ITK
    for itk in colonnes_itk:
        # Extraire culture et précédent du nom
        try:
            culture, precedent = itk.split('_prec')
            precedent = precedent.lower()
        except ValueError:
            print(
                f"  ⚠️  Format incorrect pour '{itk}', attendu 'culture_precPrecedent'")
            continue

        # Remplir les valeurs d'en-tête
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE']
                     == 'NOM_ITK_AFFICHAGE', itk] = itk
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE'] == 'ID_ITK', itk] = itk
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE'] == 'IDS_SDCS', itk] = '*'
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE']
                     == 'IDS_SDCS_CLASS', itk] = '*'
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE']
                     == 'ID_ESPECE', itk] = culture
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE'] == 'MATERIEL', itk] = 'NA'
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE']
                     == 'ID_PREC', itk] = precedent
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE'] == 'ZONE_PEDO', itk] = ''
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE']
                     == 'ZONE_PEDO_CLASS', itk] = 'NA'
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE'] == 'TYPE_EXPL', itk] = 'all'
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE'] == 'CLIMAT', itk] = ''
        df_cible.loc[df_cible['NOM_ITK_AFFICHAGE']
                     == 'IS_CULTURE_HIVER', itk] = 'N'

        nb_itk_traites += 1

    print(f"  ✓ En-tête rempli pour {nb_itk_traites} ITK")

    return df_cible


def initialiser_operations_a_na(df_cible):
    """
    Initialise toutes les opérations techniques à 'NA' ou 'N' (désactivé).

    Args:
        df_cible (DataFrame): DataFrame avec en-tête rempli

    Returns:
        DataFrame: DataFrame avec opérations initialisées
    """
    print("\n🔄 Initialisation des opérations à 'désactivé'...")

    # Colonnes des ITK
    colonnes_itk = df_cible.columns[3:]

    # Remplir toutes les cellules après la ligne 12 avec 'NA'
    df_cible.loc[12:, colonnes_itk] = 'NA'

    # Mettre les lignes 'IS_' à 'N' (Non)
    lignes_is = (df_cible['NOM_ITK_AFFICHAGE'].str.startswith(
        'IS_', na=False)) & (df_cible.index > 11)
    df_cible.loc[lignes_is, colonnes_itk] = 'N'

    print(f"  ✓ Toutes les opérations initialisées")
    print(f"  ✓ Lignes IS_* mises à 'N'")
    print(f"  ✓ Autres lignes mises à 'NA'")

    return df_cible


def appliquer_parametres_specifiques(df_cible, configuration):
    """
    Active et paramètre les opérations spécifiques (PREPA, SEMIS, RECOLTE).

    Args:
        df_cible (DataFrame): DataFrame avec opérations initialisées
        configuration (dict): Dictionnaire de configuration

    Returns:
        DataFrame: DataFrame avec paramètres appliqués
    """
    print("\n⚙️  Application des paramètres spécifiques...")

    colonnes_itk = df_cible.columns[3:]
    nb_params_appliques = 0
    nb_params_conditionnel = 0

    for operation, params in configuration.items():
        print(f"\n  • Opération : {operation}")

        for nom_param, details in params.items():
            valeur = details['valeur']
            condition = details.get('condition')

            # Trouver la ligne du paramètre
            ligne_index = df_cible.index[df_cible['NOM_ITK_AFFICHAGE'] == nom_param]

            if ligne_index.empty:
                print(f"    ⚠️  Paramètre '{nom_param}' non trouvé")
                continue

            if not condition:
                # Paramètre sans condition : appliquer à tous les ITK
                df_cible.loc[ligne_index, colonnes_itk] = valeur
                nb_params_appliques += 1
            else:
                # Paramètre avec condition : appliquer seulement si condition remplie
                nom_ligne_condition = condition['ligne_condition']
                valeur_attendue = condition['valeur_attendue']

                ligne_condition_index = df_cible.index[df_cible['NOM_ITK_AFFICHAGE']
                                                       == nom_ligne_condition]

                # Identifier les colonnes qui remplissent la condition
                colonnes_a_modifier = [
                    col for col in colonnes_itk
                    if df_cible.loc[ligne_condition_index, col].iloc[0] == valeur_attendue
                ]

                df_cible.loc[ligne_index, colonnes_a_modifier] = valeur
                nb_params_conditionnel += 1
                print(
                    f"    ✓ {nom_param} = {valeur} (si {nom_ligne_condition} = {valeur_attendue})")

    print(f"\n  ✓ {nb_params_appliques} paramètres généraux appliqués")
    print(f"  ✓ {nb_params_conditionnel} paramètres conditionnels appliqués")

    return df_cible


def afficher_resume(df_final):
    """
    Affiche un résumé du fichier créé.

    Args:
        df_final (DataFrame): DataFrame final
    """
    print("\n" + "="*70)
    print("RÉSUMÉ DU FICHIER REGLES DE DECISION")
    print("="*70)

    print(f"\n📊 Dimensions :")
    print(f"  • {df_final.shape[0]} règles")
    print(f"  • {df_final.shape[1]} colonnes")
    print(f"  • {df_final.shape[1] - 3} ITK")

    print(f"\n🌱 ITK créés :")
    colonnes_itk = df_final.columns[3:]
    for i, itk in enumerate(colonnes_itk, 1):
        print(f"  {i}. {itk}")

    print(f"\n⚙️  Opérations activées :")
    operations_actives = df_final[df_final['NOM_ITK_AFFICHAGE'].str.startswith(
        'IS_', na=False)]

    for _, row in operations_actives.iterrows():
        nom_operation = row['NOM_ITK_AFFICHAGE']
        valeurs = row[colonnes_itk].value_counts()
        if 'O' in valeurs.index:
            print(f"  • {nom_operation} : {valeurs['O']} ITK activés")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("CRÉATION DES RÈGLES DE DÉCISION")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    input_regles_path = base_dir / "data" / "ITK" / \
        "csv" / "raw" / "reglesDeDecisionsextended.csv"
    output_regles_path = base_dir / "tests" / \
        "modeleAgricole" / "culture" / "reglesDeDecision.csv"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Fichier source : {input_regles_path}")
    print(f"📤 Fichier sortie : {output_regles_path}\n")

    # Traitement des données
    try:
        # 1. Charger le fichier source
        df_source = charger_fichier_source(input_regles_path)

        # 2. Créer la structure avec les 6 ITK
        df_sasseme = creer_structure_itk(df_source, ITK_SASSEME)

        # 3. Ajouter les lignes de semis si nécessaire
        df_sasseme = ajouter_lignes_semis(df_sasseme)

        # 4. Remplir l'en-tête des ITK
        df_sasseme = remplir_entete_itk(df_sasseme)

        # 5. Initialiser toutes les opérations à 'désactivé'
        df_sasseme = initialiser_operations_a_na(df_sasseme)

        # 6. Appliquer les paramètres spécifiques
        df_sasseme = appliquer_parametres_specifiques(
            df_sasseme, CONFIGURATION_SASSEME)

        # 7. Afficher un résumé
        afficher_resume(df_sasseme)

        # 8. Sauvegarder le fichier
        print("\n💾 Sauvegarde du fichier...")
        output_regles_path.parent.mkdir(parents=True, exist_ok=True)
        df_sasseme.to_csv(output_regles_path, sep=';', index=False)
        print(f"  ✓ Fichier sauvegardé : {output_regles_path}")

        print("\n" + "=" * 70)
        print("✅ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        print("=" * 70)

        print("\n📝 Prochaines étapes :")
        print("  1. Vérifier le fichier généré")
        print("  2. Intégrer dans le module agricole MAELIA")
        print("  3. Les 6 ITK sont prêts pour la simulation")

    except FileNotFoundError as e:
        print(f"\n❌ Erreur : Fichier introuvable")
        print(f"   {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors du traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
