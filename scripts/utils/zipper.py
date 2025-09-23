import zipfile
from pathlib import Path
import time
import shutil

def zip_directory(folder_to_zip, output_path):
    """
    Compresse un dossier entier dans un fichier zip, en excluant les .gitkeep.

    Args:
        folder_to_zip (Path): Le chemin du dossier à compresser.
        output_path (Path): Le chemin complet du fichier zip à créer.
    """
    print(f"Création de l'archive : {output_path.name}...")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # .rglob('*') trouve tous les fichiers dans le dossier et ses sous-dossiers
        for file in folder_to_zip.rglob('*'):
            # On vérifie que c'est un fichier ET que son nom n'est pas '.gitkeep'
            if file.is_file() and file.name != '.gitkeep':
                # On écrit le fichier dans l'archive en conservant l'arborescence
                arcname = file.relative_to(folder_to_zip.parent)
                zipf.write(file, arcname=arcname)
                print(f"  -> Ajout de : {arcname}")
    
    print(f"\n✅ L'archive a été créée avec succès dans : {output_path}")

if __name__ == "__main__":
    # Ce bloc s'exécute quand on lance le script directement

    # 1. Définir les chemins
    # Le script est dans "scripts/utils/", donc la racine est deux niveaux au-dessus
    project_root = Path(__file__).parent.parent.parent
    
    source_folder = project_root / "includes_sassemeV1"
    
    # On sauvegarde dans un dossier _static/downloads pour que Jupyter Book le copie
    output_folder = project_root / "_static" / "downloads"
    
    # 2. Créer les noms de fichiers
    # Le fichier avec la date
    timestamp = time.strftime("%d%m%Y") # Format JJMMAAAA
    output_zip_dated = output_folder / f"includes_sassemeV1-{timestamp}.zip"
    
    # Le fichier "latest" pour le lien stable
    output_zip_latest = output_folder / "includes_sassemeV1-latest.zip"
    
    # 3. S'assurer que le dossier de sortie existe
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # 4. Lancer la compression pour créer le fichier daté
    zip_directory(source_folder, output_zip_dated)
    
    # 5. Copier le fichier daté pour créer le lien stable
    shutil.copy(output_zip_dated, output_zip_latest)
    print(f"🔗 Lien stable créé : {output_zip_latest.name}")