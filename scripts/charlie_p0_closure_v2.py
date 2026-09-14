from pathlib import Path
import re

base = Path(__file__).with_name("charlie_p0_closure.py")
text = base.read_text(encoding="utf-8")

pattern = re.compile(r'''# 3\) Kids access response must report canonical authorization, not legacy forfait/actif\.\n.*?\n# 4\) Kids token compatibility''', re.S)
replacement = r'''# 3) Kids access response must report canonical authorization, not legacy forfait/actif.
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

# Callable replacement keeps backslashes literal inside the generated Python source.
text2, n = pattern.subn(lambda _m: replacement, text, count=1)
if n != 1:
    raise RuntimeError(f"could not rewrite closure script section 3: {n}")

code = compile(text2, str(base), "exec")
globals_dict = {"__file__": str(base), "__name__": "__main__"}
exec(code, globals_dict)
