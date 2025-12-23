import os
import json
import requests
import vdf # pip install vdf
import zipfile
import io
import sys
import shutil

# --- CONFIGURATION ---
STATE_FILE = "installed_fixes.json"
LYALL_REPOS_API = "https://codeberg.org/api/v1/users/Lyall/repos"
RELEASE_API = "https://codeberg.org/api/v1/repos/Lyall/{}/releases/latest"

STEAM_PATHS = [
    os.path.expanduser("~/.local/share/Steam"),
    os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam"),
    os.path.expanduser("~/.steam/steam")
]
# ---------------------

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def parse_game_name(repo_name, description):
    """Extracts a clean Game Name from the description."""
    desc_clean = description.strip() if description else ""
    
    prefixes = ["Fix for ", "A fix for ", "Mod for ", "An ASI plugin for ", "Plugin for "]
    game_name = desc_clean
    
    found_prefix = False
    for p in prefixes:
        if game_name.lower().startswith(p.lower()):
            game_name = game_name[len(p):]
            found_prefix = True
            break
    
    if not found_prefix:
        game_name = repo_name.replace("Fix", "").replace("Tweak", "")
    else:
        stop_words = [" that ", " which ", " adding ", ".", ","]
        for s in stop_words:
            if s in game_name:
                game_name = game_name.split(s)[0]

    return game_name.strip()

def get_lyall_repos():
    """Fetches repos and parses their details."""
    print("🌍 Fetching repository list from Codeberg...")
    try:
        results = []
        page = 1
        while True:
            r = requests.get(f"{LYALL_REPOS_API}?page={page}")
            r.raise_for_status()
            data = r.json()
            if not data: break
            
            for repo in data:
                if any(x in repo['name'] for x in ['Fix', 'Patch', 'Tweak']):
                    game_title = parse_game_name(repo['name'], repo.get('description', ''))
                    results.append({
                        "repo": repo['name'],
                        "game_title": game_title,
                        "description": repo.get('description', ''),
                        "updated_at": repo.get('updated_at', '1970-01-01')
                    })
            page += 1
        return results
    except Exception as e:
        print(f"❌ Error fetching repos: {e}")
        return []

def get_installed_games():
    """Scans Steam library folders to find installed games."""
    games = {} 
    library_folders = set()

    for base_path in STEAM_PATHS:
        if os.path.exists(base_path):
            library_folders.add(base_path)
            vdf_path = os.path.join(base_path, 'steamapps', 'libraryfolders.vdf')
            if os.path.exists(vdf_path):
                try:
                    with open(vdf_path, 'r') as f:
                        data = vdf.load(f)
                        for k, v in data.get('libraryfolders', {}).items():
                            if 'path' in v:
                                library_folders.add(v['path'])
                except: pass

    for lib in library_folders:
        apps_path = os.path.join(lib, 'steamapps')
        if not os.path.exists(apps_path): continue
        
        for file in os.listdir(apps_path):
            if file.startswith("appmanifest_") and file.endswith(".acf"):
                try:
                    with open(os.path.join(apps_path, file), 'r') as f:
                        manifest = vdf.load(f)
                        name = manifest.get('AppState', {}).get('name')
                        install_dir = manifest.get('AppState', {}).get('installdir')
                        if name and install_dir:
                            full_path = os.path.join(apps_path, 'common', install_dir)
                            if os.path.exists(full_path):
                                games[name] = full_path
                except: pass
    return games

def install_update_fix(repo_name, game_path, state, game_name, interactive=True):
    print(f"⬇️  Checking releases for {repo_name}...")
    try:
        r = requests.get(RELEASE_API.format(repo_name))
        if r.status_code == 404:
            print("   ⚠️ No releases found.")
            if interactive: input("\nPress Enter to continue...")
            return
        r.raise_for_status()
        release = r.json()
    except Exception as e:
        print(f"   ❌ API Error: {e}")
        if interactive: input("\nPress Enter to continue...")
        return

    latest_tag = release['tag_name']
    local_data = state.get(repo_name, {})

    if local_data.get('tag') == latest_tag and local_data.get('path') == game_path:
        print(f"   ✅ {repo_name} is up to date ({latest_tag}).")
        if interactive: input("\nPress Enter to continue...")
        return

    print(f"   🚀 Installing {latest_tag} to: {game_path}")
    
    asset = next((a for a in release['assets'] if a['name'].endswith('.zip')), None)
    if not asset:
        print("   ❌ No zip file in release.")
        if interactive: input("\nPress Enter to continue...")
        return

    if 'files' in local_data:
        uninstall_fix(repo_name, state, quiet=True)

    try:
        zip_resp = requests.get(asset['browser_download_url'])
        z = zipfile.ZipFile(io.BytesIO(zip_resp.content))
        
        # --- NEW: Filter Junk Files ---
        all_files = z.namelist()
        files_to_extract = []
        
        for f in all_files:
            # Skip the instruction file and any hidden macOS folders
            if "EXTRACT_TO_GAME_FOLDER" in f or "__MACOSX" in f:
                continue
            files_to_extract.append(f)
            z.extract(f, game_path)
        # ------------------------------

        # Post-Download Check for DLLs
        dlls = [f for f in files_to_extract if f.endswith('.dll')]
        override_cmd = ""
        
        if 'winmm.dll' in dlls: 
            override_cmd = 'WINEDLLOVERRIDES="winmm=n,b" %command%'
        elif 'dinput8.dll' in dlls: 
            override_cmd = 'WINEDLLOVERRIDES="dinput8=n,b" %command%'
        elif 'dsound.dll' in dlls: 
            override_cmd = 'WINEDLLOVERRIDES="dsound=n,b" %command%'
        elif 'version.dll' in dlls:
            override_cmd = 'WINEDLLOVERRIDES="version=n,b" %command%'

        state[repo_name] = {
            "game_name": game_name,
            "path": game_path,
            "tag": latest_tag,
            "files": files_to_extract # Only track actual files
        }
        save_json(STATE_FILE, state)
        print("   ✨ Success!")
        if override_cmd:
            print(f"\n   ⚠️  IMPORTANT: Set this Steam Launch Option:")
            print(f"      {override_cmd}")
            
    except Exception as e:
        print(f"   ❌ Installation failed: {e}")

    if interactive:
        input("\nPress Enter to return to menu...")

def uninstall_fix(repo_name, state, quiet=False):
    data = state.get(repo_name)
    if not data: return
    path = data['path']
    files = data['files']
    
    if not quiet: print(f"🗑️  Uninstalling {repo_name} from {data['game_name']}...")
    for f in files:
        full_path = os.path.join(path, f)
        if os.path.exists(full_path) and not os.path.isdir(full_path):
            try: os.remove(full_path)
            except: pass
    
    if not quiet:
        del state[repo_name]
        save_json(STATE_FILE, state)
        print("   ✅ Uninstalled.")

def check_installed_updates(state):
    """Loops through all installed fixes and checks for updates."""
    if not state:
        print("No fixes installed yet.")
        return

    print("\n--- 🔄 Checking Installed Fixes ---")
    for repo_name, data in list(state.items()):
        if os.path.exists(data['path']):
            # interactive=False to avoid pausing on every game check
            install_update_fix(repo_name, data['path'], state, data['game_name'], interactive=False)
        else:
            print(f"⚠️  Game folder missing for {repo_name}, skipping.")
    print("-----------------------------------")

def main():
    state = load_json(STATE_FILE)
    
    # 1. Auto-update installed fixes on startup
    if state:
        check_installed_updates(state)
        print("") # formatting space

    repos = get_lyall_repos()
    sort_mode = "alpha" 

    # 2. Main Menu
    while True:
        if sort_mode == "alpha":
            repos.sort(key=lambda x: x['game_title'].lower())
            sort_display = "🔤 Alphabetical"
        else:
            repos.sort(key=lambda x: x['updated_at'], reverse=True)
            sort_display = "📅 Last Updated"

        print(f"\n--- 🛠️  Lyall's Fixes ({sort_display}) ---")
        
        for idx, r in enumerate(repos):
            repo_id = r['repo']
            game_title = r['game_title']
            status = "✅ Installed" if repo_id in state else ""
            print(f"{idx + 1}. {game_title} ({repo_id}) {status}")
        
        print("\nCommands:")
        print(" [Number] Install/Update")
        print(" [C]      Check for updates (Installed Games)")
        print(f" [S]      Sort (Currently: {sort_display})")
        print(" [U]      Uninstall a fix")
        print(" [Q]      Quit")
        
        choice = input("Select: ").lower()

        if choice == 'q': break
        
        if choice == 'c':
            check_installed_updates(state)
            input("\nCheck complete. Press Enter to continue...")
            continue

        if choice == 's':
            sort_mode = "date" if sort_mode == "alpha" else "alpha"
            continue
        
        if choice == 'u':
            installed = list(state.keys())
            if not installed:
                print("No fixes installed.")
                input("Press Enter...")
                continue
            for i, k in enumerate(installed):
                data = state[k]
                print(f"{i+1}. {data['game_name']} ({k})")
            try:
                u_choice = int(input("Number to uninstall: ")) - 1
                if 0 <= u_choice < len(installed):
                    uninstall_fix(installed[u_choice], state)
            except: pass
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(repos):
                repo_obj = repos[idx]
                repo_name = repo_obj['repo']
                
                if repo_name in state:
                    # Update existing
                    install_update_fix(repo_name, state[repo_name]['path'], state, state[repo_name]['game_name'], interactive=True)
                else:
                    # New Install
                    print(f"\nSelect installed game folder for: {repo_obj['game_title']}")
                    games = get_installed_games()
                    game_names = sorted(list(games.keys()))
                    
                    for i, g in enumerate(game_names):
                        print(f"{i+1}. {g}")
                    
                    g_choice = input(f"Enter number (or custom path): ")
                    
                    target_path = ""
                    target_game_name = "Custom Path"
                    
                    if g_choice.isdigit() and 0 <= int(g_choice)-1 < len(game_names):
                        target_game_name = game_names[int(g_choice)-1]
                        target_path = games[target_game_name]
                    else:
                        target_path = g_choice.strip()
                    
                    if os.path.exists(target_path):
                        install_update_fix(repo_name, target_path, state, target_game_name, interactive=True)
                    else:
                        print("❌ Invalid path.")
                        input("Press Enter...")
        except ValueError:
            pass

if __name__ == "__main__":
    main()
