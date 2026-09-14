"""Charlie 20 — owner session contract + final canonical wiring."""
import asyncio
import os
import re
import sys
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for k, v in {
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_KEY": "test_sk",
    "STRIPE_SECRET_KEY": "sk_test_fake",
    "STRIPE_WEBHOOK_SECRET": "whsec_test",
    "GOOGLE_TTS_API_KEY": "t",
    "PROXY_TOKEN": "pt",
    "CLAUDE_API_KEY": "t",
}.items():
    os.environ.setdefault(k, v)
import server as srv


def _run(coro):
    return asyncio.run(coro)


def test_owner_session_route_registered_and_requires_jwt():
    async def _case():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=srv.app), base_url="http://test") as c:
            r = await c.post("/industrial/owner-session", json={})
            assert r.status_code != 404
            data = r.json()
            assert data.get("ok") is False
            assert "JWT" in (data.get("erreur") or "")
    _run(_case())


def test_owner_session_is_server_authoritative():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    m = re.search(r'async def industrial_owner_session\(.*?(?=\n@app)', src, re.DOTALL)
    assert m, "owner-session endpoint missing"
    code = m.group(0)
    for required in ["dirigeant_id", "product_entitlements", "eq.industrial", "salaries", "role", "dirigeant", "user_id"]:
        assert required in code
    assert "trial_is_valid" in code
    assert "ensure_legacy_client" in code


def test_owner_frontend_gets_real_server_session():
    html = (ROOT / "connexion-industrial.html").read_text(encoding="utf-8")
    assert "/industrial/owner-session" in html
    assert "aria_industrial_session" in html
    assert "aria_industrial_token" in html
    assert "salarie_id" in html
    assert 'window.location="/poste-dirigeant.html"' in html or "window.location = \"/poste-dirigeant.html\"" in html


def test_industrial_entry_redirect_exists():
    redirects = (ROOT / "_redirects").read_text(encoding="utf-8")
    assert "/industrial /connexion-industrial.html" in " ".join(redirects.split())
    assert "aria_industrial_v1.html" not in redirects


def test_checkout_returns_to_owner_bootstrap():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    assert "https://forgedis.fr/connexion-industrial.html?owner=1&success=1" in src


def test_verifier_forfait_has_no_stale_ent_status():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    start = src.index("async def verifier_forfait(")
    end = src.find("\nasync def ", start + 10)
    code = src[start:end]
    assert "ent_status" not in code
    assert 'verifier_acces(token_recu, "facility")' in code


def test_owner_bootstrap_auto_opens_after_checkout():
    html = (ROOT / "connexion-industrial.html").read_text(encoding="utf-8")
    assert "URLSearchParams" in html
    assert 'q.get("owner")' in html
    assert 'q.get("success")' in html
