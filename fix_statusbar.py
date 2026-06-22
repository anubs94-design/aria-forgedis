import json
import shutil

APP_JSON = "app.json"
BACKUP = "app.json.backup_before_statusbar_fix"

shutil.copy(APP_JSON, BACKUP)
print(f"[OK] Backup cree : {BACKUP}")

with open(APP_JSON, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

expo = data.get("expo", {})
plugins = expo.get("plugins", [])

before = len(plugins)
plugins = [p for p in plugins if p != "expo-status-bar"]
after = len(plugins)

if before == after:
    print("[INFO] expo-status-bar n'etait pas dans plugins - rien a faire.")
else:
    print(f"[OK] expo-status-bar retire de plugins ({before} -> {after} entrees)")

expo["plugins"] = plugins

with open(APP_JSON, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print("[OK] app.json reecrit proprement.")

with open(APP_JSON, "r", encoding="utf-8") as f:
    json.load(f)
print("SYNTAXE JSON OK")
