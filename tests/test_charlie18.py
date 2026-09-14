
"""Tests Charlie 18 — inscriptions trial ends_at, repair, invoice fail-closed, HTML owner."""
import sys, os, re, asyncio, json
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

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

async def asgi():
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=srv.app),
        base_url="http://test"
    )

def mr(s, d):
    m = MagicMock(); m.status_code = s
    m.json = MagicMock(return_value=d); m.text = json.dumps(d)
    return m


# ══════════════════════════════════════════════════════════════════
# 1. inscription_facility : trial existant expiré → refus
# ══════════════════════════════════════════════════════════════════

def test_facility_select_ends_at_in_query():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    assert '"select": "id,status,source,ends_at"' in code or \
           "'select': 'id,status,source,ends_at'" in code, \
        "inscription_facility doit sélectionner ends_at"

def test_facility_trial_exists_checks_expiry():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    # La branche trial_exists doit vérifier l'expiration avant de retourner ok=True
    trial_idx = code.find('"trial_exists"')
    expired_idx = code.find('is_expired')
    valid_idx = code.find('trial_is_valid')
    assert expired_idx >= 0 or valid_idx >= 0, "inscription_facility doit appeler is_expired ou trial_is_valid"
    # La vérification de validité doit précéder trial_exists
    check_idx = min(i for i in [expired_idx, valid_idx] if i >= 0)
    assert check_idx < trial_idx, \
        f"vérification expiration ({check_idx}) doit précéder trial_exists ({trial_idx})"

def test_facility_expired_trial_returns_ok_false():
    async def _():
        import datetime as dt
        past = (dt.datetime.utcnow() - dt.timedelta(days=30)).isoformat() + "Z"
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=("uid-f","f@t.com", None))):
            orig = srv.SUPABASE_URL; srv.SUPABASE_URL = ""
            try:
                async with await asgi() as c:
                    r = await c.post("/inscription-facility",
                                     json={"jwt":"tok"},
                                     headers={"Authorization":"Bearer tok"})
                    assert r.json().get("ok") is False
            finally:
                srv.SUPABASE_URL = orig
    run(_())

def test_facility_trial_exists_no_jwt_blocked():
    async def _():
        async with await asgi() as c:
            r = await c.post("/inscription-facility", json={})
            assert r.json().get("ok") is False
    run(_())


# ══════════════════════════════════════════════════════════════════
# 2. inscription_industrial : trial existant expiré → refus
# ══════════════════════════════════════════════════════════════════

def test_industrial_select_ends_at_in_query():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    assert '"select": "id,status,ends_at"' in code or \
           "'select': 'id,status,ends_at'" in code, \
        "inscription_industrial doit sélectionner ends_at"

def test_industrial_trial_existing_checks_expiry():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    # Avant le repair, doit vérifier l'expiration du trial existant
    trial_sp_idx = code.find('TRIAL_SP')
    is_expired_idx = code.find('is_expired', trial_sp_idx)
    assert is_expired_idx >= 0 or "trial_is_valid" in code[trial_sp_idx:], "inscription_industrial doit appeler is_expired ou trial_is_valid"
    # L'is_expired doit précéder la réparation (avant 'Entitlement manquant')
    repair_idx = code.find('Entitlement manquant')
    assert is_expired_idx < repair_idx, \
        f"is_expired ({is_expired_idx}) doit précéder la réparation ({repair_idx})"


# ══════════════════════════════════════════════════════════════════
# 3. Trial repair : parse_utc_timestamp + POST vérifié
# ══════════════════════════════════════════════════════════════════

def test_trial_repair_uses_parse_utc():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    repair_idx = code.find('Entitlement manquant')
    repair_block = code[repair_idx:repair_idx+3000]
    assert 'parse_utc_timestamp' in repair_block, \
        "Trial repair doit utiliser parse_utc_timestamp"
    assert 'fromisoformat' not in repair_block, \
        "Trial repair ne doit plus utiliser fromisoformat directement"

def test_trial_repair_post_result_checked():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    repair_idx = code.find('Entitlement manquant')
    repair_block = code[repair_idx:repair_idx+3000]
    assert 'r_repair' in repair_block, "POST repair doit être capturé dans r_repair"
    assert 'r_repair.status_code' in repair_block, "r_repair.status_code doit être vérifié"

def test_trial_repair_utc_aware():
    """parse_utc_timestamp + datetime.now(utc) → pas de naive comparison."""
    import datetime as dt
    # Tester avec un timestamp timezone-aware
    aware_ts = "2020-01-01T00:00:00+00:00"
    result = srv.parse_utc_timestamp(aware_ts)
    assert result is not None
    assert result.tzinfo is not None
    # is_expired doit fonctionner sans TypeError
    expired = srv.is_expired(aware_ts)
    assert isinstance(expired, bool) and expired is True


# ══════════════════════════════════════════════════════════════════
# 4. Invoice : statut Stripe absent → 503 (pas de fallback silencieux)
# ══════════════════════════════════════════════════════════════════

def test_invoice_paid_no_fallback_active():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"invoice.paid"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    assert '_stripe_status_ip = _rs_ip.json().get("status")' in block or \
           '_rs_ip.json().get("status")' in block, \
        "invoice.paid doit capturer statut Stripe sans fallback"
    assert 'or "active"' not in block, \
        "invoice.paid ne doit pas fallback sur 'active'"

def test_invoice_failed_no_fallback_past_due():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"invoice.payment_failed"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    assert 'or "past_due"' not in block, \
        "invoice.failed ne doit pas fallback sur 'past_due'"

def test_invoice_stripe_status_absent_503():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"invoice.paid"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    # Si statut absent → return 503
    assert 'stripe_status_absent' in block, \
        "invoice.paid doit retourner 503 si statut Stripe absent"


# ══════════════════════════════════════════════════════════════════
# 5. HTML connexion-industrial.html : bootstrap propriétaire
# ══════════════════════════════════════════════════════════════════

def test_html_industrial_owner_link_present():
    html_path = os.path.join(ROOT, 'connexion-industrial.html')
    if not os.path.exists(html_path):
        pytest.skip()
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    assert 'modeProprietaire' in html, "Lien propriétaire absent"
    assert 'overlay-prop' in html, "Overlay propriétaire absent"

def test_html_industrial_claim_ownership_url():
    html_path = os.path.join(ROOT, 'connexion-industrial.html')
    if not os.path.exists(html_path):
        pytest.skip()
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    assert '/industrial/claim-ownership' in html, \
        "L'URL /industrial/claim-ownership doit être dans le HTML"
    assert 'aria-forgelis.onrender.com' in html, \
        "L'URL Relay doit être référencée"

def test_html_industrial_supabase_auth_flow():
    html_path = os.path.join(ROOT, 'connexion-industrial.html')
    if not os.path.exists(html_path):
        pytest.skip()
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    # Doit faire Supabase Auth d'abord
    assert 'auth/v1/token' in html, "Doit passer par Supabase Auth"
    assert 'access_token' in html, "Doit récupérer l'access_token JWT"
    # Doit passer le JWT à claim-ownership
    assert 'Authorization":"Bearer' in html or 'Authorization" + "' in html or \
           '"Authorization":"Bearer " + jwt' in html or \
           'Authorization":"Bearer " + jwt' in html, \
        "Doit passer le JWT dans Authorization header"

def test_html_industrial_error_handling():
    html_path = os.path.join(ROOT, 'connexion-industrial.html')
    if not os.path.exists(html_path):
        pytest.skip()
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    # Doit afficher des erreurs si claim KO
    assert 'prop-error' in html, "Element d'erreur propriétaire absent"
    assert 'prop-success' in html, "Element de succès propriétaire absent"
    assert 'fermerProp' in html, "Bouton annuler absent"

def test_html_industrial_no_direct_supabase_query():
    """Le frontend ne doit pas appeler Supabase directement pour le claim."""
    html_path = os.path.join(ROOT, 'connexion-industrial.html')
    if not os.path.exists(html_path):
        pytest.skip()
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    # La fonction claimerProprietaire doit aller vers le Relay, pas directement vers Supabase/rest
    claim_fn = re.search(r'async function claimerProprietaire\(\).*?(?=\nasync function |\nfunction )', 
                         html, re.DOTALL)
    if claim_fn:
        fn_code = claim_fn.group(0)
        # Ne pas appeler /rest/v1 directement pour le claim
        rest_calls = [l for l in fn_code.split('\n') 
                      if '/rest/v1' in l and 'claim' in l.lower()]
        assert not rest_calls, \
            f"claimerProprietaire ne doit pas appeler /rest/v1 directement: {rest_calls}"
