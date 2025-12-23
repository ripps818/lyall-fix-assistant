# Lyall's Linux Game Fix Assistant

A simple set of tools to automate the installation, updating, and launching of [Lyall's Game Fixes](https://codeberg.org/Lyall) on Linux (Bazzite, Steam Deck, standard distros).

**Repo:** [https://github.com/ripps818/lyall-fix-assistant](https://github.com/ripps818/lyall-fix-assistant)

## 🚀 Features

* **Auto-Discovery:** Fetches the latest list of fixes directly from Codeberg.
* **Smart Installation:** Automatically scans your Steam library (including SD cards) to find installed games.
* **Auto-Configuration:** The wrapper script detects which DLLs are installed (e.g., `dinput8`, `winmm`) and **automatically applies the correct WINEDLLOVERRIDES** for you.
* **Silent Updates:** Checks for mod updates in the background when you launch the game.

## 📥 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/ripps818/lyall-fix-assistant.git
    cd lyall-fix-assistant
    ```

2.  Install requirements:
    ```bash
    pip install requests vdf
    ```

3.  **Setup the Wrapper (One time setup):**
    Copy the `lyall` wrapper to your home folder for easy access.
    ```bash
    cp lyall ~/lyall
    chmod +x ~/lyall
    ```
    *Note: Ensure the `DB_PATH` inside `~/lyall` points to your `installed_fixes.json`.*

## 🎮 Usage

### 1. Manager Script (`lyall_assistant.py`)
Run this to browse fixes, install new ones, or uninstall old ones.
```bash
python lyall_assistant.py

```

### The Menu

1. **Select a Fix:** The script lists all available fixes from Lyall's repository.
2. **First-Time Install:** Select a game fix. The script will scan your Steam library and ask you to confirm which installed game matches the fix.
3. **Manage:** Press `[C]` to check updates for all installed games or `[U]` to uninstall a fix.

---

## ⚡ Auto-Update on Launch (Optional)

You can use the included `lyall` wrapper script to automatically check for updates every time you launch a game in Steam.

### 1. Setup the Wrapper

Copy the `lyall` script to your home directory so it's easy to access:

```bash
cp lyall ~/lyall
chmod +x ~/lyall

```

### 2. Configuration

Open `~/lyall` in a text editor. You **must** edit the `DB_PATH` variable to point to where `lyall_assistant.py` is saving your database.

```python
# Inside ~/lyall
DB_PATH = os.path.expanduser("~/lyall-fix-assistant/installed_fixes.json")

```

### 3. Steam Launch Options

Set your Steam Launch Options to run `~/lyall` before the game command.

**Basic Usage:**

```bash
~/lyall %command%

```

**With Gamemode or MangoHud:**

```bash
gamemoderun ~/lyall %command%

```

*Note: The wrapper has a 24-hour cooldown by default (editable in the script) to prevent slowing down game launches.*

## ❤️ Credits

* **[Lyall](https://codeberg.org/Lyall)** for creating these incredible game fixes.
* This script is a fan-made tool to make managing them easier on Linux.


##### This tool was created with the aid of an AI assistant