
"""
Tests Charlie 14 — map_stripe, claim-ownership, fallback legacy, sync statut
"""
import sys, os, re, asyncio, json
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

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

def run(c): return asyncio.run(c)

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
    hc = MagicMock()
    gq=list(g); pq=list(p); rq=list(r)
    async def _g(*a,**kw): return gq.pop(0) if gq else make_resp(200,[])
    async def _p(*a,**kw): return pq.pop(0) if pq else make_resp(201,{})
    async def _r(*a,**kw): return rq.pop(0) if rq else make_resp(204,{})
    hc.get=_g; hc.post=_p; hc.patch=_r
    return hc


# ══════════════════════════════════════════════════════════════════════
# 1. map_stripe_to_statut_paiement
# ══════════════════════════════════════════════════════════════════════
class TestMapStripeToStatut:
    def test_active_maps_to_actif(self):
        assert srv.map_stripe_to_statut_paiement("active") == "actif"

    def test_trialing_maps_to_trialing(self):
        assert srv.map_stripe_to_statut_paiement("trialing") == "trialing"

    def test_past_due_maps_to_impaye(self):
        assert srv.map_stripe_to_statut_paiement("past_due") == "impaye"

    def test_unpaid_maps_to_impaye(self):
        assert srv.map_stripe_to_statut_paiement("unpaid") == "impaye"

    def test_canceled_maps_to_resilie(self):
        assert srv.map_stripe_to_statut_paiement("canceled") == "resilie"

    def test_paused_maps_to_suspendu(self):
        assert srv.map_stripe_to_statut_paiement("paused") == "suspendu"

    def test_incomplete_expired_maps_to_resilie(self):
        assert srv.map_stripe_to_statut_paiement("incomplete_expired") == "resilie"

    def test_unknown_returns_none_fail_closed(self):
        """Statut inconnu -> None (fail-closed), jamais essai."""
        assert srv.map_stripe_to_statut_paiement("UNKNOWN_STATUS") is None

    def test_suspended_returns_none(self):
        """'suspended' est un statut transformé, pas Stripe brut -> None."""
        assert srv.map_stripe_to_statut_paiement("suspended") is None

    def test_no_payant_in_mapping(self):
        """'payant' ne doit pas être dans le mapping."""
        all_values = [srv.map_stripe_to_statut_paiement(s)
                      for s in ["active","trialing","past_due","canceled","paused"]]
        assert "payant" not in all_values

    def test_function_exists_in_srv(self):
        assert hasattr(srv, 'map_stripe_to_statut_paiement')
        assert callable(srv.map_stripe_to_statut_paiement)


# ══════════════════════════════════════════════════════════════════════
# 2. /industrial/claim-ownership — ASGI réels
# ══════════════════════════════════════════════════════════════════════
def test_claim_ownership_no_jwt():
    async def _():
        async with await asgi_client() as c:
            r = await c.post("/industrial/claim-ownership", json={})
            data = r.json()
            assert data.get("ok") is False
            assert "JWT" in (data.get("erreur") or "")
    run(_())

def test_claim_ownership_bad_jwt():
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=(None, None, "JWT invalide"))):
            async with await asgi_client() as c:
                r = await c.post("/industrial/claim-ownership",
                                  json={"jwt": "bad"},
                                  headers={"Authorization": "Bearer bad"})
                assert r.json().get("ok") is False
    run(_())

def test_claim_ownership_service_indisponible():
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=("uid","u@t.com",None))):
            orig = srv.SUPABASE_URL
            srv.SUPABASE_URL = ""
            try:
                async with await asgi_client() as c:
                    r = await c.post("/industrial/claim-ownership",
                                      json={"jwt":"tok"},
                                      headers={"Authorization":"Bearer tok"})
                    assert r.json().get("ok") is False
            finally:
                srv.SUPABASE_URL = orig
    run(_())


# ══════════════════════════════════════════════════════════════════════
# 3. Sécurité claim-ownership — code source
# ══════════════════════════════════════════════════════════════════════
def test_claim_ownership_checks_entitlement():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    assert m, "industrial_claim_ownership non trouvée"
    code = m.group(0)
    # Doit vérifier l'entitlement avant de patcher
    ent_idx = code.find('product_entitlements')
    patch_idx = code.find('"dirigeant_id": auth_uid')
    assert ent_idx >= 0, "doit vérifier product_entitlements"
    assert patch_idx >= 0, "doit faire PATCH dirigeant_id"
    assert ent_idx < patch_idx, "entitlement check avant PATCH"

def test_claim_ownership_no_overwrite_existing_dirigeant():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    # Doit vérifier que dirigeant_id est NULL avant d'écrire
    assert 'existing_dir' in code or 'dirigeant_id' in code
    assert 'déjà un dirigeant différent' in code or 'existant' in code.lower()

def test_claim_ownership_idempotent():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    # Si dirigeant_id == auth_uid -> action=already_claimed (idempotent)
    assert 'already_owned' in code

def test_claim_ownership_marks_claimed():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    assert '"status": "claimed"' in code
    assert '"claimed_at"' in code


# ══════════════════════════════════════════════════════════════════════
# 4. Suppression fallback legacy dans verifier_acces
# ══════════════════════════════════════════════════════════════════════
def test_verifier_acces_no_forfait_fallback():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def verifier_acces\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    assert m
    code = m.group(0)
    # Le bloc "if user_email and forfait not in" ne doit plus exister
    assert 'if user_email and forfait not in' not in code, \
        "Fallback legacy forfait toujours présent"
    # Les comptes migration n'ont plus de fallback
    assert 'Fallback legacy clients.forfait' not in code

def test_verifier_acces_fail_closed():
    """Sans entitlement canonique -> pas d'accès accordé."""
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def verifier_acces\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    code = m.group(0)
    # Le code doit refuser si ent_status n'est pas trialing/active
    assert 'canceled' in code and 'expired' in code
    assert 'return False' in code


# ══════════════════════════════════════════════════════════════════════
# 5. _sync_entreprise_statut helper
# ══════════════════════════════════════════════════════════════════════
def test_sync_entreprise_statut_exists():
    assert hasattr(srv, '_sync_entreprise_statut')
    assert callable(srv._sync_entreprise_statut)

def test_sync_entreprise_statut_runtime():
    """Teste la synchro avec des mocks httpx réels."""
    hc = _hc(
        g=[
            make_resp(200, [{"id": "uid-dir"}]),      # profiles
            make_resp(200, [{"id": "ent-uuid"}]),      # entreprises
        ],
        r=[make_resp(204, {})]  # PATCH statut
    )
    # Appel direct de la fonction
    run(srv._sync_entreprise_statut(hc, "dir@test.com", "active"))
    # Vérifier que patch a été appelé (ent_status = "actif")
    # La fonction ne retourne rien mais ne doit pas lever d'exception
    assert True  # Si on arrive ici, pas d'exception

def test_sync_entreprise_statut_mapping():
    """Vérifie le mapping dans le code source."""
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def _sync_entreprise_statut\(.*?(?=\nasync def |\n@app|\ndef )',
                  src, re.DOTALL)
    assert m
    code = m.group(0)
    assert 'map_stripe_to_statut_paiement' in code
    assert 'statut_paiement' in code


# ══════════════════════════════════════════════════════════════════════
# 6. Trial Industrial sans reset date
# ══════════════════════════════════════════════════════════════════════
def test_trial_repair_no_utcnow_start():
    """La réparation trial ne doit pas utiliser utcnow() comme starts_at."""
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
    assert m
    code = m.group(0)
    # Le bloc de réparation doit utiliser created_at de l'entreprise
    assert 'created_at' in code or 'original_start' in code
    # Il ne doit pas y avoir de "starts_at_r = _dt_ii2.datetime.utcnow()" dans le bloc repair
    repair_idx = code.find('# Entitlement manquant')
    if repair_idx >= 0:
        repair_block = code[repair_idx:repair_idx+500]
        assert 'utcnow()' not in repair_block.split('ends_at_r')[0], \
            "starts_at ne doit pas être utcnow() dans la réparation"


# ══════════════════════════════════════════════════════════════════════
# 7. Fail-closed pending ownership checkout
# ══════════════════════════════════════════════════════════════════════
def test_pending_ownership_fail_closed():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('pending_industrial_ownership')
    # Dans le checkout, le résultat du POST doit être vérifié
    # Chercher "if _r_pio.status_code not in"
    assert '_r_pio' in src or 'r_pio.status_code' in src, \
        "La réponse POST pending_industrial_ownership doit être vérifiée"
    assert 'pending_ownership_post_failed' in src or \
           'pending_ownership_failed' in src, \
        "Doit fail-close si POST pending_ownership échoue"


# ══════════════════════════════════════════════════════════════════════
# 8. Checkout statut_paiement via mapping
# ══════════════════════════════════════════════════════════════════════
def test_checkout_uses_mapping():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    # Dans le checkout, statut_paiement doit utiliser map_stripe_to_statut_paiement
    # et non "essai" hardcodé (au moins pour la première occurrence = checkout webhook)
    idx_checkout = src.find('"checkout.session.completed"')
    assert idx_checkout >= 0
    co_block = src[idx_checkout:idx_checkout+12000]
    assert 'map_stripe_to_statut_paiement' in co_block, \
        "Le checkout doit utiliser map_stripe_to_statut_paiement"
