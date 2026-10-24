from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path

import minecraft_launcher_lib
import requests

APP_NAME = "MiniCraft"
DATA_DIR = Path.home() / ".minicraft_launcher"
GAME_DIR = DATA_DIR / "game"
PROFILES_FILE = DATA_DIR / "profiles.json"
MODRINTH_API = "https://api.modrinth.com/v2"

DATA_DIR.mkdir(parents=True, exist_ok=True)
GAME_DIR.mkdir(parents=True, exist_ok=True)


def load_profiles():
    if not PROFILES_FILE.exists():
        return [{"name": "Vanilla", "version": "latest-release", "loader": "vanilla"}]
    try:
        data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) and data else [
            {"name": "Vanilla", "version": "latest-release", "loader": "vanilla"}
        ]
    except (OSError, json.JSONDecodeError):
        return [{"name": "Vanilla", "version": "latest-release", "loader": "vanilla"}]


def save_profiles(profiles):
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2), encoding="utf-8")


def list_versions():
    manifest = requests.get(
        "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json",
        timeout=15,
    )
    manifest.raise_for_status()
    data = manifest.json()
    return [v["id"] for v in data["versions"] if v.get("type") == "release"]


def install_vanilla(version: str, progress=None):
    callback = {"setStatus": lambda message: progress and progress(message),
                "setProgress": lambda value: None,
                "setMax": lambda value: None}
    minecraft_launcher_lib.install.install_minecraft_version(
        version, str(GAME_DIR), callback=callback
    )


def launch_vanilla(version: str, username: str, progress=None):
    # Offline username is a local development/testing identity, not account authentication.
    if not username.strip():
        raise ValueError("Enter a player name for offline development mode.")
    if len(username) > 16 or not username.replace("_", "").isalnum():
        raise ValueError("Use 1–16 letters, numbers, or underscores for the player name.")
    options = {
        "username": username,
        "uuid": "00000000-0000-0000-0000-000000000000",
        "token": "",
        "launcherName": APP_NAME,
        "launcherVersion": "0.1.0",
    }
    command = minecraft_launcher_lib.command.get_minecraft_command(
        version, str(GAME_DIR), options
    )
    subprocess.Popen(command, cwd=str(GAME_DIR))


def modrinth_search(query: str, game_version: str, loader: str, limit=15):
    facets = [["project_type:mod"]]
    if game_version:
        facets.append([f"versions:{game_version}"])
    if loader and loader != "vanilla":
        facets.append([f"categories:{loader}"])
    params = {
        "query": query,
        "limit": limit,
        "facets": json.dumps(facets),
        "index": "relevance",
    }
    response = requests.get(f"{MODRINTH_API}/search", params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("hits", [])


def install_modrinth_project(project_id: str, game_version: str, loader: str):
    """Install one compatible Modrinth mod and recursively install required Modrinth deps."""
    mods_dir = GAME_DIR / "mods"
    mods_dir.mkdir(parents=True, exist_ok=True)
    installed_projects = set()

    def install_project(pid):
        if pid in installed_projects:
            return
        installed_projects.add(pid)
        params = {
            "game_versions": json.dumps([game_version]),
            "loaders": json.dumps([loader]),
        }
        r = requests.get(f"{MODRINTH_API}/project/{pid}/version",
                         params=params, timeout=20)
        r.raise_for_status()
        versions = r.json()
        if not versions:
            raise RuntimeError(f"No compatible version found for project {pid}.")
        version = versions[0]

        # Required dependencies first. Dependencies without a project_id may be external.
        for dep in version.get("dependencies", []):
            if dep.get("dependency_type") == "required" and dep.get("project_id"):
                install_project(dep["project_id"])

        files = version.get("files", [])
        chosen = next((f for f in files if f.get("primary")), files[0] if files else None)
        if not chosen or not chosen.get("url") or not chosen.get("filename"):
            raise RuntimeError(f"No downloadable file found for project {pid}.")
        target = mods_dir / Path(chosen["filename"]).name
        if target.exists():
            return
        # Stream to a temporary file, then rename only after the download succeeds.
        temp = target.with_suffix(target.suffix + ".part")
        with requests.get(chosen["url"], stream=True, timeout=60) as download:
            download.raise_for_status()
            with temp.open("wb") as out:
                for chunk in download.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        out.write(chunk)
        temp.replace(target)

    install_project(project_id)


def install_loader(loader: str, version: str, progress=None):
    """Best-effort loader integration using minecraft-launcher-lib's public APIs."""
    callback = {"setStatus": lambda message: progress and progress(message),
                "setProgress": lambda value: None,
                "setMax": lambda value: None}
    loader = loader.lower()
    if loader == "fabric":
        module = getattr(minecraft_launcher_lib, "fabric", None)
        if module is None:
            raise RuntimeError("Fabric installer API is unavailable in this installed launcher library.")
        module.install_fabric(version, str(GAME_DIR), callback=callback)
    elif loader == "forge":
        module = getattr(minecraft_launcher_lib, "forge", None)
        if module is None:
            raise RuntimeError("Forge installer API is unavailable in this installed launcher library.")
        module.install_forge_version(version, str(GAME_DIR), callback=callback)
    elif loader == "quilt":
        raise RuntimeError("Quilt installer is not wired in this prototype yet; use the official Quilt installer.")
    else:
        raise ValueError("Unsupported loader.")
