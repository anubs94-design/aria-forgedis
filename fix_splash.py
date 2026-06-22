# -*- coding: utf-8 -*-
import json
import shutil

APP_JSON = "app.json"
BACKUP = "app.json.backup_before_splash_fix"

def main():
    shutil.copy(APP_JSON, BACKUP)
    print(f"[OK] Backup cree : {BACKUP}")

    with open(APP_JSON, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    expo = data.get("expo", {})

    if "splash" not in expo:
        print("[INFO] Pas de cle splash trouvee - rien a faire.")
        return

    splash = expo.pop("splash")
    print(f"[OK] Cle splash retiree de la racine : {splash}")

    splash_plugin_config = {
        "image": splash.get("image", "./assets/splash.png"),
        "resizeMode": splash.get("resizeMode", "contain"),
        "backgroundColor": splash.get("backgroundColor", "#ffffff"),
    }

    plugins = expo.setdefault("plugins", [])
    plugins = [p for p in plugins if not (isinstance(p, list) and p and p[0] == "expo-splash-screen")]
    plugins.append(["expo-splash-screen", splash_plugin_config])
    expo["plugins"] = plugins

    print(f"[OK] Plugin expo-splash-screen ajoute avec config : {splash_plugin_config}")

    with open(APP_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("[OK] app.json reecrit proprement.")
    print("--- Verification syntaxe JSON ---")
    with open(APP_JSON, "r", encoding="utf-8") as f:
        json.load(f)
    print("SYNTAXE JSON OK")

if __name__ == "__main__":
    main()
