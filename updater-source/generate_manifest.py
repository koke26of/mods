import os
import hashlib
import json

def get_file_hash(filepath):
    """Calcula el hash SHA-256 de un archivo."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_manifest(base_dir, base_url, modpack_name="Mi Modpack"):
    manifest = {
        "modpack_name": modpack_name,
        "version": "1.0.0",
        "minecraft_version": "1.20.1",
        "forge_version": "47.2.0",
        "mods": []
    }

    # Estructura esperada: mods/core/ y mods/qol/
    categories = ["core", "qol"]
    
    for category in categories:
        cat_path = os.path.join(base_dir, category)
        if not os.path.exists(cat_path):
            print(f"Advertencia: No se encontró la carpeta {cat_path}")
            continue

        for filename in os.listdir(cat_path):
            if filename.endswith(".jar"):
                file_path = os.path.join(cat_path, filename)
                print(f"Procesando [{category}]: {filename}")
                
                file_hash = get_file_hash(file_path)
                file_size = os.path.getsize(file_path)
                
                # Construir la URL (ajustar según cómo lo subas a GitHub)
                mod_url = f"{base_url}/{category}/{filename}"
                
                manifest["mods"].append({
                    "id": filename.replace(".jar", "").lower(),
                    "name": filename.replace(".jar", ""),
                    "category": category,
                    "filename": filename,
                    "url": mod_url,
                    "hash": file_hash,
                    "size": file_size
                })

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        print("\n¡Éxito! manifest.json generado correctamente.")

if __name__ == "__main__":
    # CONFIGURACIÓN MANUAL
    BASE_URL_GITHUB = "https://raw.githubusercontent.com/koke26of/mods/refs/heads/main/updater-source/mods_local"
    
    # Asegúrate de tener carpetas 'core' y 'qol' con tus mods dentro de una carpeta 'mods_local'
    if not os.path.exists("mods_local"):
        os.makedirs("mods_local/core")
        os.makedirs("mods_local/qol")
        print("He creado una carpeta 'mods_local'. Pon tus mods en 'core' o 'qol' y vuelve a ejecutar este script.")
    else:
        generate_manifest("mods_local", BASE_URL_GITHUB)
