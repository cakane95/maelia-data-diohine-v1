import zipfile
from pathlib import Path
import time

def zip_directory(folder_to_zip, output_path):
    """
    Compresse un dossier entier dans un fichier zip.

    Args:
        folder_to_zip (Path): Le chemin du dossier à compresser.
        output_path (Path): Le chemin complet du fichier zip à créer.
    """
    print(f"Création de l'archive : {output_path.name}...")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # .rglob('*') trouve tous les fichiers dans le dossier et ses sous-dossiers
        for file in folder_to_zip.rglob('*'):
            if file.is_file():
                # On écrit le fichier dans l'archive en conservant l'arborescence
                # file.relative_to(folder_to_zip.parent) garantit que le chemin
                # dans le zip commence par "includes_sassemeV1/..."
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
    output_folder = project_root / "dist"
    
    # Créer un nom de fichier unique avec la date
    timestamp = time.strftime("%Y%m%d")
    output_zip_file = output_folder / f"includes_sassemeV1_{timestamp}.zip"
    
    # 2. S'assurer que le dossier de sortie existe
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # 3. Lancer la compression
    zip_directory(source_folder, output_zip_file)