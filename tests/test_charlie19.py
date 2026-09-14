
"""
Tests Charlie 19 — P0 HTML bootstrap + trial_is_valid
"""
import sys, os, re, asyncio, json, datetime as dt
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

for k, v in {
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_KEY": "test_sk",
    "STRIPE_SECRET_KEY": "sk_test_fake",
    "STRIPE_WEBHOOK_SECRET": "whsec_test",
    "GOOGLE_TTS_API_KEY": "t",
    "PROXY_TOKEN": "pt",
    "CLAUDE_API_KEY": "ta",
}.items():
    os.environ.setdefault(k, v)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import server as srv

def run(c): return asyncio.run(c)


# ══════════════════════════════════════════════════════════════════
# 1. HTML : <script src> ne contient PLUS de JS inline
# ══════════════════════════════════════════════════════════════════

HTML_FILE = os.path.join(ROOT, 'connexion-industrial.html')

def test_html_no_script_src_with_inline_js():
    if not os.path.exists(HTML_FILE):
        pytest.skip()
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()
    # Parser chaque balise <script> individuellement
    import html as _html_mod
    bad = []
    for m in re.finditer(r'<script([^>]*)>(.*?)</script>', html, re.DOTALL):
        attrs, content = m.group(1), m.group(2)
        if 'src=' in attrs and content.strip():
            bad.append((attrs.strip(), content.strip()[:40]))
    assert not bad, f"<script src> avec contenu inline encore présent: {bad}"

def test_html_functions_in_standalone_script():
    """Les fonctions JS sont dans un <script> SANS src."""
    if not os.path.exists(HTML_FILE):
        pytest.skip()
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()
    for fn in ['modeProprietaire', 'claimerProprietaire', 'fermerProp', 'signupProprietaire']:
        # Trouver la position de la fonction
        fn_pos = html.find(f'function {fn}')
        assert fn_pos >= 0, f"function {fn} absente"
        # Trouver la balise script enclosante
        script_start = html.rfind('<script', 0, fn_pos)
        # La balise script ne doit pas avoir src=
        script_tag = html[script_start:html.find('>', script_start)+1]
        assert 'src=' not in script_tag, \
            f"function {fn} est dans <script src> — JS non exécuté ! Tag: {script_tag}"

def test_html_signup_mode_present():
    """L'overlay propose un formulaire de création de compte."""
    if not os.path.exists(HTML_FILE):
        pytest.skip()
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()
    assert 'prop-signup-email' in html, "Champ email signup absent"
    assert 'prop-signup-mdp' in html, "Champ mdp signup absent"
    assert 'signupProprietaire' in html, "Fonction signupProprietaire absente"

def test_html_redirect_to_industrial_not_industrial_html():
    """La redirection post-claim pointe vers /industrial (app), pas /industrial.html (marketing)."""
    if not os.path.exists(HTML_FILE):
        pytest.skip()
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()
    assert "'/industrial'" in html or '"/industrial"' in html, \
        "Redirection vers /industrial absente"
    # Vérifier que les redirections window.location vont vers /industrial et non /industrial.html
    redirects = re.findall(r"window\.location\s*=\s*['\"]([^'\"]+)['\"]", html)
    for dest in redirects:
        assert not dest.endswith('.html'), \
            f"Redirection vers {dest!r} — doit pointer vers /industrial, pas {dest!r}"


# ══════════════════════════════════════════════════════════════════
# 2. trial_is_valid() helper
# ══════════════════════════════════════════════════════════════════

def test_trial_is_valid_exists():
    assert hasattr(srv, 'trial_is_valid'), "trial_is_valid() absent de server.py"

def test_trial_is_valid_active_future():
    future = (dt.datetime.utcnow() + dt.timedelta(days=10)).isoformat() + "Z"
    assert srv.trial_is_valid("active", future) is True

def test_trial_is_valid_trialing_future():
    future = (dt.datetime.utcnow() + dt.timedelta(days=5)).isoformat() + "Z"
    assert srv.trial_is_valid("trialing", future) is True

def test_trial_is_valid_active_past():
    """Trial actif mais ends_at passé → False."""
    past = (dt.datetime.utcnow() - dt.timedelta(days=1)).isoformat() + "Z"
    assert srv.trial_is_valid("active", past) is False

def test_trial_is_valid_canceled_future():
    """Statut canceled même avec date future → False."""
    future = (dt.datetime.utcnow() + dt.timedelta(days=10)).isoformat() + "Z"
    assert srv.trial_is_valid("canceled", future) is False

def test_trial_is_valid_past_due_future():
    """Statut past_due même avec date future → False."""
    future = (dt.datetime.utcnow() + dt.timedelta(days=10)).isoformat() + "Z"
    assert srv.trial_is_valid("past_due", future) is False

def test_trial_is_valid_no_ends_at():
    """Trial sans ends_at → False (fail-closed)."""
    assert srv.trial_is_valid("trialing", None) is False
    assert srv.trial_is_valid("active", "") is False

def test_trial_is_valid_invalid_timestamp():
    """Timestamp invalide → False."""
    assert srv.trial_is_valid("trialing", "not-a-date") is False

def test_trial_is_valid_unknown_status():
    """Statut inconnu → False."""
    future = (dt.datetime.utcnow() + dt.timedelta(days=10)).isoformat()
    assert srv.trial_is_valid("unknown_status", future) is False


# ══════════════════════════════════════════════════════════════════
# 3. inscription_facility : trial_is_valid utilisé
# ══════════════════════════════════════════════════════════════════

def test_inscription_facility_uses_trial_is_valid():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    assert 'trial_is_valid' in code or 'is_expired' in code, \
        "inscription_facility doit appeler trial_is_valid ou is_expired"

def test_inscription_facility_status_checked_with_ends_at():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()
    m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    if "trial_is_valid" in code:
        tv_idx = code.find("trial_is_valid(")
        snippet = code[tv_idx:tv_idx+300]
        depth, commas = 0, 0
        for ch in snippet:
            if ch == "(": depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0: break
            elif ch == "," and depth == 1: commas += 1
        assert commas >= 1, f"trial_is_valid doit avoir >= 2 args: {snippet[:100]}"
    else:
        assert "is_expired" in code, "inscription_facility doit appeler trial_is_valid ou is_expired"


def test_inscription_industrial_checks_status_before_trial_exists():
    """Un entitlement canceled avec date future ne doit pas produire trial_exists."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    trial_sp_idx = code.find('TRIAL_SP')
    # trial_is_valid ou is_expired doit être présent avant trial_exists
    tv_idx = code.find('trial_is_valid', trial_sp_idx)
    ex_idx = code.find('is_expired', trial_sp_idx)
    trial_exists_idx = code.find('"trial_exists"')
    check_idx = min(i for i in [tv_idx, ex_idx] if i >= 0)
    assert check_idx < trial_exists_idx, \
        f"Vérification validité ({check_idx}) doit précéder trial_exists ({trial_exists_idx})"

def test_trial_is_valid_covers_industrial_scenario():
    """Scenario exact P0: canceled + date future → False."""
    future = (dt.datetime.utcnow() + dt.timedelta(days=10)).isoformat() + "Z"
    # Ce scénario causait trial_exists avec l'ancien code
    assert srv.trial_is_valid("canceled", future) is False, \
        "canceled + date future doit retourner False"
    assert srv.trial_is_valid("past_due", future) is False, \
        "past_due + date future doit retourner False"
    assert srv.trial_is_valid("expired", future) is False, \
        "expired + date future doit retourner False"


# ══════════════════════════════════════════════════════════════════
# 5. Route inscription-facility accessible (route enregistrée)
# ══════════════════════════════════════════════════════════════════

async def asgi():
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=srv.app),
        base_url="http://test"
    )

def test_inscription_facility_route_no_jwt():
    async def _():
        async with await asgi() as c:
            r = await c.post("/inscription-facility", json={})
            assert r.status_code != 404, "/inscription-facility non enregistrée"
            assert r.json().get("ok") is False
    run(_())
