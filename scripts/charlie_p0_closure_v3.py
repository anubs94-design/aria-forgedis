from pathlib import Path
import re

base = Path(__file__).with_name("charlie_p0_closure.py")
text = base.read_text(encoding="utf-8")

# Replace fragile section 3 (Kids response) with a scoped regex edit.
p3 = re.compile(r'''# 3\) Kids access response must report canonical authorization, not legacy forfait/actif\.\n.*?\n# 4\) Kids token compatibility''', re.S)
r3 = r'''# 3) Kids access response must report canonical authorization, not legacy forfait/actif.
vk_start = src.index("async def verify_kids_access")
vk_end = src.index('@app.post("/ask-kids")', vk_start)
vk = src[vk_start:vk_end]
vk_pattern = re.compile(
    r'"forfait"\s*:\s*cl\.get\("forfait"\s*,\s*forfait\).*?\n\s*"email"\s*:\s*cl\.get\("email"\s*,\s*""\).*?\n\s*"actif"\s*:\s*cl\.get\("actif"\s*,\s*False\)\s*,?',
    re.S,
)
vk_repl = '"forfait": forfait,  # valeur canonique issue de verifier_acces\n                "email": cl.get("email", ""),\n                "actif": True,  # verifier_acces a deja valide le droit Kids'
vk2, n = vk_pattern.subn(vk_repl, vk, count=1)
if n != 1:
    raise RuntimeError(f"verify_kids_access canonical response regex: got {n}")
src = src[:vk_start] + vk2 + src[vk_end:]

# 4) Kids token compatibility'''
text, n = p3.subn(lambda _m: r3, text, count=1)
if n != 1:
    raise RuntimeError(f"rewrite section 3 failed: {n}")

# Replace fragile section 5 with edits scoped strictly to ensure_legacy_client.
p5 = re.compile(r'''# 5\) ensure_legacy_client: respect explicit deletion requests; otherwise reactivation is compatibility only\.\n.*?\n# 6\) Pending user claims''', re.S)
r5 = r'''# 5) ensure_legacy_client: respect explicit deletion requests; otherwise reactivation is compatibility only.
elc_start = src.index("async def ensure_legacy_client")
elc_end = src.index('@app.post("/industrial/claim-ownership")', elc_start)
elc = src[elc_start:elc_end]
elc, n = re.subn(
    r'params=\{"email": f"eq\.\{email\}", "select": "token,forfait,actif"\}',
    'params={"email": f"eq.{email}", "select": "token,forfait,actif,suppression_demandee"}',
    elc,
    count=1,
)
if n != 1:
    raise RuntimeError(f"ensure_legacy_client select regex: {n}")
elc, n = re.subn(
    r'if existing:\n\s*# Réactiver si nécessaire\n\s*if not existing\[0\]\.get\("actif"\):',
    'if existing:\n        if existing[0].get("suppression_demandee"):\n            raise RuntimeError("Compte en cours de suppression: reactivation automatique interdite")\n        # Réactiver le conteneur legacy si nécessaire; les droits restent canoniques ailleurs.\n        if not existing[0].get("actif"):',
    elc,
    count=1,
)
if n != 1:
    raise RuntimeError(f"ensure_legacy_client deletion guard regex: {n}")
src = src[:elc_start] + elc + src[elc_end:]

# 6) Pending user claims'''
text, n = p5.subn(lambda _m: r5, text, count=1)
if n != 1:
    raise RuntimeError(f"rewrite section 5 failed: {n}")

code = compile(text, str(base), "exec")
exec(code, {"__file__": str(base), "__name__": "__main__"})
