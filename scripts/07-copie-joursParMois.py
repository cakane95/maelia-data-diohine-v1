"""
07-copie-joursParMois.py

Script de copie du fichier joursParMois.csv pour MAELIA
Auteurs: Cheikhou Akhmed KANE (conversion script: Aboubakry BA)
Description: Copie le fichier joursParMois.csv depuis les données brutes vers 
             le répertoire du modèle commun MAELIA

Ce script :
- Vérifie l'existence du fichier source
- Crée le dossier de destination si nécessaire
- Copie le fichier vers le répertoire MAELIA
"""

import shutil
from pathlib import Path
import sys


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def verifier_fichier_source(source_path):
    """
    Vérifie l'existence du fichier source.

    Args:
        source_path (Path): Chemin vers le fichier source

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
    print("📂 Vérification du fichier source...")

    if not source_path.exists():
        raise FileNotFoundError(f"Fichier source introuvable : {source_path}")

    # Afficher des informations sur le fichier
    taille = source_path.stat().st_size
    print(f"  ✓ Fichier trouvé : {source_path.name}")
    print(f"  ✓ Taille : {taille} octets")


def creer_dossier_destination(destination_path):
    """
    Crée le dossier de destination s'il n'existe pas.

    Args:
        destination_path (Path): Chemin complet du fichier de destination
    """
    print("\n📁 Préparation du dossier de destination...")

    dossier = destination_path.parent

    if not dossier.exists():
        dossier.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Dossier créé : {dossier}")
    else:
        print(f"  ✓ Dossier existe déjà : {dossier}")


def copier_fichier(source_path, destination_path):
    """
    Copie le fichier source vers la destination.

    Args:
        source_path (Path): Chemin source
        destination_path (Path): Chemin destination
    """
    print("\n📋 Copie du fichier...")

    # Vérifier si le fichier de destination existe déjà
    if destination_path.exists():
        print(f"  ⚠️  Le fichier de destination existe déjà")
        print(f"     Il sera écrasé")

    # Effectuer la copie
    shutil.copy2(source_path, destination_path)

    print(f"  ✓ Fichier copié avec succès")

    # Vérifier que la copie a réussi
    if destination_path.exists():
        taille_dest = destination_path.stat().st_size
        taille_src = source_path.stat().st_size

        if taille_dest == taille_src:
            print(
                f"  ✓ Vérification : tailles identiques ({taille_dest} octets)")
        else:
            print(f"  ⚠️  Attention : tailles différentes")
            print(f"     Source : {taille_src} octets")
            print(f"     Destination : {taille_dest} octets")


def afficher_resume(source_path, destination_path):
    """
    Affiche un résumé de l'opération.

    Args:
        source_path (Path): Chemin source
        destination_path (Path): Chemin destination
    """
    print("\n" + "="*70)
    print("RÉSUMÉ DE LA COPIE")
    print("="*70)

    print(f"\n📥 Source :")
    print(f"  {source_path}")

    print(f"\n📤 Destination :")
    print(f"  {destination_path}")

    print(f"\n📊 Informations :")
    print(f"  • Nom du fichier : {source_path.name}")
    print(f"  • Taille : {source_path.stat().st_size} octets")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
def main():
    """
    Fonction principale du script.
    """
    print("=" * 70)
    print("COPIE DU FICHIER joursParMois.csv")
    print("=" * 70)

    # Définir les chemins
    base_dir = Path(__file__).parent.parent.resolve()
    source_path = base_dir / "data" / "commun" / "csv" / "raw" / "joursParMois.csv"
    destination_path = base_dir / "tests" / \
        "modeleCommun" / "date" / "joursParMois.csv"

    print(f"\n📍 Répertoire du projet : {base_dir}")
    print(f"📥 Fichier source : {source_path}")
    print(f"📤 Fichier destination : {destination_path}\n")

    # Processus de copie
    try:
        # 1. Vérifier le fichier source
        verifier_fichier_source(source_path)

        # 2. Créer le dossier de destination
        creer_dossier_destination(destination_path)

        # 3. Copier le fichier
        copier_fichier(source_path, destination_path)

        # 4. Afficher un résumé
        afficher_resume(source_path, destination_path)

        print("\n" + "=" * 70)
        print("✅ COPIE TERMINÉE AVEC SUCCÈS")
        print("=" * 70)

    except FileNotFoundError as e:
        print(f"\n❌ Erreur : Fichier source introuvable")
        print(f"   {e}")
        sys.exit(1)
    except PermissionError as e:
        print(f"\n❌ Erreur : Permission refusée")
        print(f"   {e}")
        print("\n   Vérifiez que :")
        print("   • Vous avez les droits d'accès au dossier")
        print("   • Le fichier de destination n'est pas ouvert")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors de la copie : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
