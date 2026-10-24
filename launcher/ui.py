import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from . import core


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MiniCraft Launcher")
        self.geometry("1040x690")
        self.minsize(900, 600)
        self.profiles = core.load_profiles()
        self.versions = ["latest-release"]
        self.search_results = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(sidebar, text="MINICRAFT", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=22, pady=(28, 4), sticky="w")
        ctk.CTkLabel(sidebar, text="Lightweight launcher", text_color="#8b95a5").grid(
            row=1, column=0, padx=22, pady=(0, 28), sticky="w")
        ctk.CTkLabel(sidebar, text="PROFILE", text_color="#8b95a5").grid(
            row=2, column=0, padx=22, sticky="w")
        self.profile_menu = ctk.CTkOptionMenu(sidebar, values=self.profile_names(),
                                               command=self.profile_changed)
        self.profile_menu.grid(row=3, column=0, padx=18, pady=(8, 10), sticky="ew")
        ctk.CTkButton(sidebar, text="+ New profile", command=self.new_profile,
                      fg_color="#273449", hover_color="#34465f").grid(
            row=4, column=0, padx=18, pady=4, sticky="ew")
        ctk.CTkLabel(sidebar, text="ACCOUNT", text_color="#8b95a5").grid(
            row=5, column=0, padx=22, pady=(26, 6), sticky="w")
        self.username = ctk.CTkEntry(sidebar, placeholder_text="Offline player name")
        self.username.insert(0, "Player")
        self.username.grid(row=6, column=0, padx=18, pady=4, sticky="ew")
        ctk.CTkLabel(sidebar, text="Offline dev mode only\nMicrosoft OAuth not configured",
                     text_color="#e0b36b", justify="left", wraplength=180).grid(
            row=7, column=0, padx=18, pady=8, sticky="w")
        ctk.CTkLabel(sidebar, text="Prototype • v0.1.0", text_color="#667085").grid(
            row=9, column=0, padx=18, pady=20, sticky="w")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=26, pady=24)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(main, text="Your game. Your setup.", font=ctk.CTkFont(size=30, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkLabel(main, text="Install a release, choose a profile, and play.",
                     text_color="#9ca3af").grid(row=1, column=0, sticky="w", pady=(4, 20))

        game_card = ctk.CTkFrame(main, corner_radius=16)
        game_card.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        game_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(game_card, text="MINECRAFT", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8b95a5").grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")
        self.version_var = tk.StringVar(value="latest-release")
        self.version_menu = ctk.CTkOptionMenu(game_card, variable=self.version_var,
                                              values=["latest-release"])
        self.version_menu.grid(row=1, column=0, padx=20, pady=(0, 18), sticky="w")
        self.loader_var = tk.StringVar(value="vanilla")
        self.loader_menu = ctk.CTkOptionMenu(game_card, variable=self.loader_var,
                                             values=["vanilla", "fabric", "forge", "quilt"])
        self.loader_menu.grid(row=1, column=1, padx=10, pady=(0, 18), sticky="w")
        ctk.CTkButton(game_card, text="Refresh versions", command=self.refresh_versions).grid(
            row=1, column=2, padx=20, pady=(0, 18))

        actions = ctk.CTkFrame(main, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=(0, 18))
        ctk.CTkButton(actions, text="Install / Update", height=42,
                      command=self.install_selected).pack(side="left", padx=(0, 10))
        ctk.CTkButton(actions, text="PLAY", height=42, fg_color="#16804a",
                      hover_color="#11683c", command=self.play).pack(side="left")

        mods = ctk.CTkFrame(main, corner_radius=16)
        mods.grid(row=4, column=0, sticky="nsew")
        mods.grid_columnconfigure(0, weight=1)
        mods.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(mods, text="Modrinth", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=18, pady=(16, 8), sticky="w")
        search_row = ctk.CTkFrame(mods, fg_color="transparent")
        search_row.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")
        search_row.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(search_row, placeholder_text="Search mods (e.g. minimap)")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(search_row, text="Search", command=self.search_mods).grid(row=0, column=1)
        self.results_frame = ctk.CTkScrollableFrame(mods, fg_color="transparent")
        self.results_frame.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")

        self.status = ctk.CTkLabel(self, text="Ready", anchor="w", text_color="#9ca3af")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 8))

    def profile_names(self):
        return [p["name"] for p in self.profiles]

    def selected_profile(self):
        name = self.profile_menu.get()
        return next((p for p in self.profiles if p["name"] == name), self.profiles[0])

    def profile_changed(self, _=None):
        p = self.selected_profile()
        self.version_var.set(p.get("version", "latest-release"))
        self.loader_var.set(p.get("loader", "vanilla"))

    def new_profile(self):
        dialog = ctk.CTkInputDialog(text="Profile name:", title="Create profile")
        name = (dialog.get_input() or "").strip()
        if not name:
            return
        if any(p["name"].lower() == name.lower() for p in self.profiles):
            messagebox.showerror("Profile exists", "Choose a different profile name.")
            return
        self.profiles.append({"name": name, "version": "latest-release", "loader": "vanilla"})
        core.save_profiles(self.profiles)
        self.profile_menu.configure(values=self.profile_names())
        self.profile_menu.set(name)
        self.profile_changed()

    def save_selected_profile(self):
        p = self.selected_profile()
        p["version"] = self.version_var.get()
        p["loader"] = self.loader_var.get()
        core.save_profiles(self.profiles)

    def set_status(self, message):
        self.after(0, lambda: self.status.configure(text=message[:180]))

    def run_background(self, label, work):
        self.set_status(label)
        def task():
            try:
                work()
                self.set_status("Ready")
            except Exception as exc:
                self.set_status("Action failed")
                self.after(0, lambda: messagebox.showerror("Launcher error", str(exc)))
        threading.Thread(target=task, daemon=True).start()

    def refresh_versions(self):
        def work():
            versions = core.list_versions()
            self.after(0, lambda: self.version_menu.configure(values=["latest-release"] + versions))
            self.set_status(f"Loaded {len(versions)} release versions")
        self.run_background("Fetching Minecraft versions…", work)

    def resolved_version(self):
        version = self.version_var.get()
        if version == "latest-release":
            manifest = core.list_versions()
            return manifest[0] if manifest else version
        return version

    def install_selected(self):
        self.save_selected_profile()
        loader = self.loader_var.get()
        version = self.resolved_version()
        def work():
            self.set_status(f"Installing Minecraft {version}…")
            core.install_vanilla(version, self.set_status)
            if loader != "vanilla":
                self.set_status(f"Installing {loader}…")
                core.install_loader(loader, version, self.set_status)
        self.run_background("Preparing installation…", work)

    def play(self):
        self.save_selected_profile()
        version = self.resolved_version()
        loader = self.loader_var.get()
        def work():
            # Launcher library install IDs vary by loader; this prototype launches vanilla only.
            if loader != "vanilla":
                raise RuntimeError("Install/launch for modloader profiles needs loader-specific version ID mapping. Vanilla launch is supported in this prototype.")
            core.install_vanilla(version, self.set_status)
            core.launch_vanilla(version, self.username.get(), self.set_status)
        self.run_background("Starting Minecraft…", work)

    def search_mods(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        version = self.resolved_version()
        loader = self.loader_var.get()
        def work():
            hits = core.modrinth_search(query, version, loader)
            self.search_results = hits
            self.after(0, lambda: self.render_results(hits))
            self.set_status(f"Found {len(hits)} Modrinth projects")
        self.run_background("Searching Modrinth…", work)

    def render_results(self, hits):
        for child in self.results_frame.winfo_children():
            child.destroy()
        if not hits:
            ctk.CTkLabel(self.results_frame, text="No compatible mods found.").pack(anchor="w", padx=8, pady=8)
            return
        for hit in hits:
            row = ctk.CTkFrame(self.results_frame, corner_radius=10)
            row.pack(fill="x", padx=4, pady=4)
            details = ctk.CTkFrame(row, fg_color="transparent")
            details.pack(side="left", fill="x", expand=True, padx=12, pady=8)
            ctk.CTkLabel(details, text=hit.get("title", "Unnamed mod"),
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            desc = hit.get("description", "")
            ctk.CTkLabel(details, text=desc[:160], text_color="#9ca3af",
                         wraplength=500, justify="left").pack(anchor="w")
            ctk.CTkButton(row, text="Install", width=90,
                          command=lambda project=hit: self.install_mod(project)).pack(
                side="right", padx=12, pady=12)

    def install_mod(self, project):
        version = self.resolved_version()
        loader = self.loader_var.get()
        if loader == "vanilla":
            messagebox.showinfo("Choose a loader", "Most mods require Fabric, Forge, or Quilt. Choose the correct loader first.")
            return
        def work():
            core.install_modrinth_project(project["project_id"], version, loader)
        self.run_background(f"Installing {project.get('title', 'mod')} and required dependencies…", work)
