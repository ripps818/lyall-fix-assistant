# Lyall's Linux Game Fix Manager

A simple Python CLI tool to automate the installation and updating of [Lyall's Game Fixes](https://codeberg.org/Lyall) on Linux (Bazzite, Steam Deck, standard distros).

Lyall's fixes are essential for many games running on Proton/Wine (e.g., *Metaphor: ReFantazio*, *Final Fantasy XVI*, *Black Myth: Wukong*), often enabling ultrawide support, FOV sliders, and removing FPS caps. This tool ensures they stay up-to-date without manual file management.

## 🚀 Features

* **Auto-Discovery:** Fetches the latest list of fixes directly from Codeberg.
* **Smart Detection:** Automatically scans your Steam library folders (including SD cards) to find where your games are installed.
* **One-Click Updates:** Remembers your game paths. If a game updates and breaks the fix, simply run the script to reinstall the latest version instantly.
* **Safety First:**
    * Detects required DLL overrides (e.g., `dinput8`, `winmm`) and tells you exactly what launch options to use in Steam.
    * Filters out junk files (like `EXTRACT_TO_GAME_FOLDER` placeholders) to keep your game directories clean.
* **Clean Uninstall:** removing a fix only deletes the mod files, leaving your game data untouched.

## 📋 Prerequisites

You need Python installed (pre-installed on most Linux distros, including Bazzite/SteamOS). You also need two small libraries to handle web requests and Steam config files.

Open your terminal and run:

```bash
pip install requests vdf

```

## 📥 Installation

1. Clone this repository or download the script:
```bash
git clone [https://github.com/YOUR_USERNAME/lyall-linux-assistant.git](https://github.com/YOUR_USERNAME/lyall-linux-assistant.git)
cd lyall-linux-assistant

```



## 🎮 Usage

Run the script from your terminal:

```bash
python lyall_assistant.py

```

### The Menu

1. **Select a Fix:** The script lists all available fixes from Lyall's repository.
2. **First-Time Install:** Select a game fix. The script will scan your Steam library and ask you to confirm which installed game matches the fix.
3. **Automatic Updates:** On subsequent runs, the script checks all installed fixes. If Lyall has released a new version, it can update them automatically.

### Steam Launch Options

**Important:** Most of these fixes are ASI plugins or DLL wrappers. If the script detects a DLL (like `dinput8.dll`), it will warn you to set a launch option in Steam.

Example:

1. Right-click the game in Steam -> **Properties**.
2. In **Launch Options**, add:
```text
WINEDLLOVERRIDES="dinput8=n,b" %command%

```



## 🛠️ Configuration

The script creates a local file named `installed_fixes.json` in the same directory.

* This file tracks which fixes are installed and where your games are located.
* **Do not share this file**, as it contains your local file paths.

## ❤️ Credits

* **[Lyall](https://codeberg.org/Lyall)** for creating these incredible game fixes.
* This script is a fan-made tool to make managing them easier on Linux.

##### This tool was created with the aid of an AI assistant