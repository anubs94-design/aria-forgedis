"""Charlie 22 — Facility enrollment must use canonical entitlements."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/"server.py").read_text(encoding="utf-8")

def _block():
    m=re.search(r'async def enroler_installation\(.*?(?=\n@app\.post\("/tts"\))',SRC,re.S)
    assert m
    return m.group(0)

def test_enrollment_uses_canonical_facility_authorization():
    b=_block()
    assert 'ensure_legacy_client' in b
    assert 'verifier_acces(aria_token, "facility")' in b
    assert 'rows[0].get("actif")' not in b
    assert 'rows[0].get("forfait"' not in b

def test_installation_token_bound_only_after_access_check():
    b=_block()
    assert b.index('verifier_acces(aria_token, "facility")') < b.index('"token_installation": tok_inst')
    assert '"Prefer": "return=representation"' in b
    assert 'r_bind.status_code' in b

# Final independent CI trigger after canonical enrollment patch.
