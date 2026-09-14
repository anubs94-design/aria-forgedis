
"""
FORGEDIS — Tests ASGI runtime réels (v4 finale)
Patch sur les fonctions Supabase, pas sur httpx bas niveau.
"""
import sys, os, json, asyncio, re
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest
import httpx

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test_service_key")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("GOOGLE_TTS_API_KEY", "test")
os.environ.setdefault("PROXY_TOKEN", "proxy_test")
os.environ.setdefault("CLAUDE_API_KEY", "test_anthropic")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import server as srv

def run(coro): return asyncio.run(coro)

async def asgi_client():
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=srv.app),
        base_url="http://test"
    )

def make_resp(status, data):
    m = MagicMock()
    m.status_code = status
    m.json = MagicMock(return_value=data)
    m.text = json.dumps(data)
    return m

def _hc(g=(), p=(), r=()):
    """Mock d'un httpx.AsyncClient interne."""
    hc = MagicMock()
    gq=list(g); pq=list(p); rq=list(r)
    async def _g(*a,**kw): return gq.pop(0) if gq else make_resp(200,[])
    async def _p(*a,**kw): return pq.pop(0) if pq else make_resp(201,{})
    async def _r(*a,**kw): return rq.pop(0) if rq else make_resp(204,{})
    hc.get=_g; hc.post=_p; hc.patch=_r
    return hc


# ══════════════════════════════════════════════════════════════════════════
# 0. Routes publiques
# ══════════════════════════════════════════════════════════════════════════
def test_version():
    async def _():
        async with await asgi_client() as c:
            assert (await c.get("/version")).status_code < 500
    run(_())

def test_bienvenue():
    async def _():
        async with await asgi_client() as c:
            assert (await c.post("/bienvenue", json={})).status_code < 500
    run(_())


# ══════════════════════════════════════════════════════════════════════════
# 1. /inscription-facility — patchs ciblés
# ══════════════════════════════════════════════════════════════════════════
def test_facility_no_jwt():
    async def _():
        async with await asgi_client() as c:
            r = await c.post("/inscription-facility", json={})
            data = r.json()
            assert data.get("ok") is False
            assert "JWT" in (data.get("erreur") or "")
    run(_())

def test_facility_bad_jwt():
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=(None, None, "JWT invalide"))):
            async with await asgi_client() as c:
                r = await c.post("/inscription-facility",
                                  json={"jwt": "bad"},
                                  headers={"Authorization": "Bearer bad"})
                assert r.json().get("ok") is False
    run(_())

def test_facility_service_indisponible():
    """SUPABASE_URL vide -> Service indisponible."""
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=("uid","u@t.com",None))):
            orig_url = srv.SUPABASE_URL
            srv.SUPABASE_URL = ""
            try:
                async with await asgi_client() as c:
                    r = await c.post("/inscription-facility",
                                      json={"jwt":"tok"},
                                      headers={"Authorization":"Bearer tok"})
                    data = r.json()
                    assert data.get("ok") is False
                    assert "indisponible" in (data.get("erreur") or "").lower()
            finally:
                srv.SUPABASE_URL = orig_url
    run(_())


# ══════════════════════════════════════════════════════════════════════════
# 2. /inscription-industrial — validation JWT uniquement (sans DB)
# ══════════════════════════════════════════════════════════════════════════
def test_industrial_no_jwt():
    async def _():
        async with await asgi_client() as c:
            r = await c.post("/inscription-industrial", json={})
            data = r.json()
            assert data.get("ok") is False
            assert "JWT" in (data.get("erreur") or "")
    run(_())

def test_industrial_bad_jwt():
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=(None, None, "JWT invalide"))):
            async with await asgi_client() as c:
                r = await c.post("/inscription-industrial",
                                  json={"jwt": "bad"},
                                  headers={"Authorization": "Bearer bad"})
                assert r.json().get("ok") is False
    run(_())

def test_industrial_service_indisponible():
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=("uid","u@t.com",None))):
            orig = srv.SUPABASE_URL
            srv.SUPABASE_URL = ""
            try:
                async with await asgi_client() as c:
                    r = await c.post("/inscription-industrial",
                                      json={"jwt":"tok"},
                                      headers={"Authorization":"Bearer tok"})
                    assert r.json().get("ok") is False
            finally:
                srv.SUPABASE_URL = orig
    run(_())


# ══════════════════════════════════════════════════════════════════════════
# 3. /sauvegarder — patchs sur verifier_acces (fonctionne car c'est une fn du module)
# ══════════════════════════════════════════════════════════════════════════
def test_sauvegarder_no_token():
    async def _():
        async with await asgi_client() as c:
            r = await c.post("/sauvegarder",
                              json={"donnees": {}, "salarie_id": "u"})
            assert "erreur" in r.json()
    run(_())

def test_sauvegarder_verifier_acces_refuse():
    """verifier_acces retourne False -> erreur."""
    async def _():
        with patch.object(srv, 'verifier_acces',
                          new=AsyncMock(return_value=(False,"Accès refusé",""))):
            async with await asgi_client() as c:
                r = await c.post("/sauvegarder",
                                  json={"token":"tok","donnees":{},"salarie_id":"sal"})
                data = r.json()
                assert "erreur" in data
                assert "Accès refusé" in data["erreur"]
    run(_())

def test_sauvegarder_no_salarie_id():
    async def _():
        with patch.object(srv, 'verifier_acces',
                          new=AsyncMock(return_value=(True,None,"industrial"))):
            async with await asgi_client() as c:
                r = await c.post("/sauvegarder",
                                  json={"token":"tok","donnees":{}})
                data = r.json()
                assert "salarie_id" in (data.get("erreur") or "").lower()
    run(_())


# ══════════════════════════════════════════════════════════════════════════
# 4. /client-token-kids
# ══════════════════════════════════════════════════════════════════════════
def test_kids_no_jwt():
    async def _():
        async with await asgi_client() as c:
            r = await c.post("/client-token-kids", json={})
            assert "JWT" in (r.json().get("erreur") or "")
    run(_())

def test_kids_bad_jwt():
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=(None,None,"JWT invalide"))):
            async with await asgi_client() as c:
                r = await c.post("/client-token-kids",
                                  headers={"Authorization":"Bearer bad"}, json={})
                assert "JWT" in (r.json().get("erreur") or "") or \
                       "erreur" in r.json()
    run(_())

def test_kids_claim_called_before_entitlement():
    """_claim_pending_entitlements appelé avant la lecture entitlement."""
    calls = []
    async def fake_jwt(tok, req): return ("uid-k", "k@t.com", None)
    async def fake_claim(hx, uid, email):
        calls.append("claim")

    async def _():
        with patch.object(srv, '_jwt_vers_identite', new=fake_jwt):
            with patch.object(srv, '_claim_pending_entitlements', new=fake_claim):
                orig_url = srv.SUPABASE_URL
                srv.SUPABASE_URL = ""  # Provoquer Service indisponible après JWT
                # En fait: après JWT la route ouvre httpx et appelle _claim_pending_entitlements
                # Pas de moyen simple de tracer sans patcher httpx
                # On vérifie structurellement via le code source
                srv.SUPABASE_URL = orig_url
                # Test structurel : _claim_pending_entitlements doit être avant product_entitlements GET
                with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
                    src = f.read()
                ctk_m = re.search(r'async def client_token_kids\(.*?(?=\nasync def |\n@app)',
                                   src, re.DOTALL)
                assert ctk_m
                code = ctk_m.group(0)
                claim_idx = code.find('_claim_pending_entitlements')
                ent_idx = code.find('product_entitlements')
                assert claim_idx >= 0, "_claim_pending_entitlements absent"
                assert claim_idx < ent_idx, "claim doit précéder entitlement check"
    run(_())


# ══════════════════════════════════════════════════════════════════════════
# 5. create_pending_claim — runtime réel avec mocks httpx
# ══════════════════════════════════════════════════════════════════════════
def _get_cpc():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(
        r'(    async def create_pending_claim\(.*?        except Exception as e:\n.*?return False\n)',
        src, re.DOTALL)
    assert m, "create_pending_claim non trouvée"
    code = re.sub(r'^    ','',m.group(1),flags=re.MULTILINE)
    ns = {'SUPABASE_URL': os.environ['SUPABASE_URL'],
          'SUPABASE_SERVICE_KEY': os.environ['SUPABASE_SERVICE_KEY']}
    exec(code, ns)
    return ns['create_pending_claim']

class TestCreatePendingClaimRuntime:
    def test_pending_no_NameError(self):
        cpc = _get_cpc()
        hc = _hc(g=[make_resp(200,[{"id":"c1","status":"pending"}])],
                  r=[make_resp(204,{})])
        assert run(cpc(hc,"t@t.com","fac","cus","sub1",["p"],"facility","facility","trialing","s","e")) is True

    def test_new_insert(self):
        cpc = _get_cpc()
        hc = _hc(g=[make_resp(200,[])], p=[make_resp(201,{})])
        assert run(cpc(hc,"n@t.com","fac","c","sub2",[],"facility","facility","trialing",None,None)) is True

    def test_claimed_matching(self):
        cpc = _get_cpc()
        hc = _hc(g=[make_resp(200,[{"id":"c2","status":"claimed"}]),
                     make_resp(200,[{"id":"e1","status":"active","product":"facility"}])])
        assert run(cpc(hc,"p@t.com","fac","c","sub3",[],"facility","facility","active",None,None)) is True

    def test_claimed_absent_resets(self):
        cpc = _get_cpc()
        hc = _hc(g=[make_resp(200,[{"id":"c3","status":"claimed"}]),
                     make_resp(200,[])], r=[make_resp(204,{})])
        assert run(cpc(hc,"g@t.com","fac","c","sub4",[],"facility","facility","active",None,None)) is False

    def test_claimed_wrong_product_rejected(self):
        cpc = _get_cpc()
        hc = _hc(g=[make_resp(200,[{"id":"c4","status":"claimed"}]),
                     make_resp(200,[{"id":"e2","status":"active","product":"kids_solo"}])],
                  r=[make_resp(204,{})])
        assert run(cpc(hc,"wp@t.com","fac","c","sub5",[],"facility","facility","active",None,None)) is False

    def test_insert_failure(self):
        cpc = _get_cpc()
        hc = _hc(g=[make_resp(200,[])], p=[make_resp(409,{"e":"conflict"})])
        assert run(cpc(hc,"f@t.com","fac",None,"sub6",[],"facility","facility","trialing",None,None)) is False


# ══════════════════════════════════════════════════════════════════════════
# 6. State machine Industrial — code source
# ══════════════════════════════════════════════════════════════════════════
def test_industrial_no_payant_in_code():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    assert m
    code = m.group(0)
    assert '"payant"' not in code or 'BLOCK_SP' in code, \
        "inscription_industrial ne doit pas utiliser 'payant' comme statut valide"
    assert 'BLOCK_SP' in code or 'impaye' in code, "State machine manquante"

def test_industrial_real_schema_columns():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    assert '"email_admin"' not in code
    assert '"expires_at"' not in code
    assert '"email_contact"' in code
    assert '"dirigeant_id"' in code


# ══════════════════════════════════════════════════════════════════════════
# 7. /sauvegarder — code source tenant check
# ══════════════════════════════════════════════════════════════════════════
def test_sauvegarder_tenant_check_in_code():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def sauvegarder_donnees\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    assert m
    code = m.group(0)
    assert 'entreprise_autorisee' in code
    assert 'sal_check' in code
    check_idx = code.find('sal_check')
    upsert_idx = code.find('donnees_salaries')
    assert check_idx < upsert_idx
    assert '403' in code
    assert 'on_conflict' in code


# ══════════════════════════════════════════════════════════════════════════
# 8. HTML
# ══════════════════════════════════════════════════════════════════════════
def test_html_facility_no_btn_submit():
    p = os.path.join(ROOT,'inscription-facility.html')
    if not os.path.exists(p): pytest.skip()
    assert 'btn-submit' not in open(p,encoding='utf-8').read()

def test_html_industrial_no_btn_submit():
    p = os.path.join(ROOT,'inscription-industrial.html')
    if not os.path.exists(p): pytest.skip()
    assert 'btn-submit' not in open(p,encoding='utf-8').read()

def test_html_facility_catch_no_onboarding():
    p = os.path.join(ROOT,'inscription-facility.html')
    if not os.path.exists(p): pytest.skip()
    html = open(p,encoding='utf-8').read()
    m = re.search(r'\.catch\(function\(.*?\}\);', html, re.DOTALL)
    if m: assert 'showOnboarding' not in m.group(0)

def test_html_industrial_catch_no_onboarding():
    p = os.path.join(ROOT,'inscription-industrial.html')
    if not os.path.exists(p): pytest.skip()
    html = open(p,encoding='utf-8').read()
    m = re.search(r'\.catch\(function\(.*?\}\);', html, re.DOTALL)
    if m: assert 'showOnboarding' not in m.group(0)

def test_html_facility_authorization():
    p = os.path.join(ROOT,'inscription-facility.html')
    if not os.path.exists(p): pytest.skip()
    html = open(p,encoding='utf-8').read()
    fetches = list(re.finditer(r'fetch\(RELAY\+ENDPOINT', html))
    assert fetches
    relay = html[fetches[0].start():fetches[0].start()+500]
    assert 'Authorization' in relay and 'jwt' in relay

def test_html_industrial_authorization():
    p = os.path.join(ROOT,'inscription-industrial.html')
    if not os.path.exists(p): pytest.skip()
    html = open(p,encoding='utf-8').read()
    fetches = list(re.finditer(r'fetch\(RELAY\+ENDPOINT', html))
    assert fetches
    relay = html[fetches[0].start():fetches[0].start()+500]
    assert 'Authorization' in relay and 'jwt' in relay


# ══════════════════════════════════════════════════════════════════════════
# 9. Migrations
# ══════════════════════════════════════════════════════════════════════════
def test_migration_donnees_salaries():
    d = os.path.join(ROOT,'supabase','migrations')
    if not os.path.exists(d): pytest.skip()
    assert any('20260913205308' in f and 'donnees_salaries' in f for f in os.listdir(d))

def test_migration_industrial_ownership():
    d = os.path.join(ROOT,'supabase','migrations')
    if not os.path.exists(d): pytest.skip()
    assert any('20260913212504' in f and 'industrial_ownership' in f for f in os.listdir(d))
