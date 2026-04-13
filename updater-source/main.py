import os
import json
import hashlib
import requests
import customtkinter as ctk
import threading
from urllib.parse import urlparse

class ModSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ModSync - Minecraft Mod Updater")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # --- CONFIGURACIÓN ---
        # 1. Cambia esto por la URL "RAW" de tu manifest en GitHub
        self.manifest_url = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/manifest.json"
        
        # 2. Carpeta de mods (detecta AppData automáticamente)
        self.mods_folder = os.path.join(os.getenv('APPDATA'), '.minecraft', 'mods')
        
        self.remote_manifest = None
        self.local_mods = {}
        self.selected_qol = {} # Para guardar la elección del usuario

        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        # Sidebar/Status
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="MODSYNC", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(pady=20)

        self.status_box = ctk.CTkTextbox(self.sidebar, width=180, height=300, font=("Consolas", 11))
        self.status_box.pack(padx=10, pady=10)
        self.status_box.configure(state="disabled")

        # Main Content
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        self.tab_core = self.tabview.add("Core Mods (Mandatory)")
        self.tab_qol = self.tabview.add("Optional Features (QoL)")

        self.core_list = ctk.CTkScrollableFrame(self.tab_core)
        self.core_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.qol_list = ctk.CTkScrollableFrame(self.tab_qol)
        self.qol_list.pack(fill="both", expand=True, padx=10, pady=10)

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)

        self.sync_button = ctk.CTkButton(self.main_frame, text="Update Mods", command=self.start_sync, state="disabled")
        self.sync_button.pack(pady=10)

    def log(self, message):
        self.status_box.configure(state="normal")
        self.status_box.insert("end", f"> {message}\n")
        self.status_box.see("end")
        self.status_box.configure(state="disabled")

    def load_initial_data(self):
        threading.Thread(target=self.fetch_manifest, daemon=True).start()

    def fetch_manifest(self):
        self.log("Fetching manifest from GitHub...")
        try:
            response = requests.get(self.manifest_url)
            self.remote_manifest = response.json()
            self.after(0, self.render_mods)
            self.log("Manifest loaded successfully.")
            self.after(0, lambda: self.sync_button.configure(state="normal"))
        except Exception as e:
            self.log(f"Error loading manifest: {e}")

    def render_mods(self):
        # Limpiar listas
        for widget in self.core_list.winfo_children(): widget.destroy()
        for widget in self.qol_list.winfo_children(): widget.destroy()

        for mod in self.remote_manifest["mods"]:
            if mod["category"] == "core":
                label = ctk.CTkLabel(self.core_list, text=f"• {mod['name']}", anchor="w")
                label.pack(fill="x", padx=5, pady=2)
            else:
                var = ctk.BooleanVar(value=True)
                self.selected_qol[mod["id"]] = var
                check = ctk.CTkCheckBox(self.qol_list, text=mod["name"], variable=var)
                check.pack(fill="x", padx=5, pady=5)

    def calculate_hash(self, filepath):
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def start_sync(self):
        self.sync_button.configure(state="disabled")
        threading.Thread(target=self.sync_logic, daemon=True).start()

    def sync_logic(self):
        if not os.path.exists(self.mods_folder):
            os.makedirs(self.mods_folder)
            self.log("Created mods folder.")

        # 1. Identificar qué mods hay que descargar
        to_download = []
        keep_files = [] # Archivos que NO debemos borrar

        for mod in self.remote_manifest["mods"]:
            # Si es QoL y no está seleccionado, ignorar
            if mod["category"] == "qol" and not self.selected_qol[mod["id"]].get():
                continue
            
            local_path = os.path.join(self.mods_folder, mod["filename"])
            keep_files.append(mod["filename"])

            # ¿Necesita descarga?
            needs_download = True
            if os.path.exists(local_path):
                if self.calculate_hash(local_path) == mod["hash"]:
                    needs_download = False
            
            if needs_download:
                to_download.append(mod)

        # 2. Borrar mods obsoletos (que no están en el manifest)
        self.log("Checking for obsolete mods...")
        manifest_filenames = [m["filename"] for m in self.remote_manifest["mods"]]
        for local_file in os.listdir(self.mods_folder):
            if local_file.endswith(".jar") and local_file not in keep_files:
                # Solo borramos si el archivo es parte de lo que gestionamos o es basura
                self.log(f"Removing obsolete mod: {local_file}")
                os.remove(os.path.join(self.mods_folder, local_file))

        # 3. Descargar mods nuevos/actualizados
        total = len(to_download)
        if total == 0:
            self.log("Everything is up to date!")
            self.after(0, lambda: self.progress_bar.set(1))
        else:
            for i, mod in enumerate(to_download):
                self.log(f"Downloading ({i+1}/{total}): {mod['name']}")
                r = requests.get(mod["url"])
                with open(os.path.join(self.mods_folder, mod["filename"]), 'wb') as f:
                    f.write(r.content)
                self.after(0, lambda x=i: self.progress_bar.set((x+1)/total))

        self.log("Sync Complete! You can close and play.")
        self.after(0, lambda: self.sync_button.configure(state="normal", text="Sync Complete ✅"))

if __name__ == "__main__":
    app = ModSyncApp()
    app.mainloop()
