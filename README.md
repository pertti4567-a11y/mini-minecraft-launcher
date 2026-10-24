# MiniCraft Launcher (prototype)

A lightweight Python + CustomTkinter Minecraft launcher scaffold for Windows/Linux/macOS.

## What works in this prototype

- Dark desktop UI and locally saved named profiles
- Fetches official Minecraft release versions
- Installs vanilla Minecraft using `minecraft-launcher-lib`
- Launches vanilla in **offline development mode**
- Searches Modrinth for mods filtered by game version and loader
- Downloads compatible Modrinth files and recursively installs required Modrinth project dependencies
- Profile settings are stored in `~/.minicraft_launcher/profiles.json`

## Not production-ready yet

- **Microsoft OAuth is intentionally not faked or implemented.** A production launcher needs a registered Microsoft application, the supported Xbox Live → XSTS → Minecraft Services token exchange, secure token storage, refresh/expiry handling, and account ownership checks. Never ask users to paste Microsoft passwords into this app.
- Offline mode is a local testing option only. It does not authenticate the user or provide online-mode access.
- The loader installer methods depend on the installed `minecraft-launcher-lib` version. Quilt is currently a clearly marked integration point.
- Loader-specific launch IDs are not yet mapped in the Play button. Vanilla launching is the working path.
- CurseForge search/download is not included in the UI yet. Its API requires an approved API key and has separate distribution/API terms. Do not scrape its website or ship a private key in a public desktop app.
- Modrinth dependency installation handles required project dependencies returned for the selected version. It does not resolve external dependencies, conflicts, or every special dependency case.
- Profile-specific isolated game directories, mod removal, integrity checks, and installer signatures should be added before broad release.

## Setup

Use Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

The first installation downloads Minecraft libraries and assets and therefore needs internet access. Install a suitable Java runtime for the Minecraft version you want to play.

## Project structure

```text
mini_minecraft_launcher/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── launcher/
    ├── __init__.py
    ├── core.py       # Minecraft install/launch + Modrinth API
    └── ui.py         # CustomTkinter desktop UI
```

## Security / production checklist

1. Register the desktop app and implement Microsoft authorization using the current official flow; use PKCE/state where supported and validate the callback.
2. Store refresh tokens in the operating system credential vault (Windows Credential Manager, macOS Keychain, or Secret Service), never in `profiles.json`.
3. Use per-profile game directories to prevent one profile's mods from affecting another.
4. Verify file hashes when the API provides them; use temporary files and atomic renames.
5. Add cancellation, bounded retries, clear logs, and download progress.
6. Integrate each loader's supported installer/API and map the resulting version ID before enabling Play.
7. Apply for CurseForge API access and follow its terms before enabling CurseForge functionality.

## API references

- Minecraft installation library: https://minecraft-launcher-lib.readthedocs.io/
- Modrinth API search: https://docs.modrinth.com/api/operations/searchprojects/
- Modrinth project versions: https://docs.modrinth.com/api/operations/getprojectversions/
- CurseForge API access: https://support.curseforge.com/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key
