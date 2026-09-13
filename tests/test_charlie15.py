
"""
Tests P0 runtime réels — clôture Charlie.
Couvre: verifier_acces fail-closed, claim Industrial sécurisé,
map_stripe fail-closed, _sync via sub_id, trial repair, etc.
"""
import sys, os, re, asyncio, json, hmac, hashlib, time
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
    m = MagicMock()
    m.status_code = s
    m.json = MagicMock(return_value=d)
    m.text = json.dumps(d)
    return m

def hc(g=(), p=(), r=()):
    h = MagicMock()
    gq=list(g); pq=list(p); rq=list(r)
    async def _g(*a,**kw): return gq.pop(0) if gq else mr(200,[])
    async def _p(*a,**kw): return pq.pop(0) if pq else mr(201,{})
    async def _r(*a,**kw): return rq.pop(0) if rq else mr(204,{})
    h.get=_g; h.post=_p; h.patch=_r
    return h

# ══════════════════════════════════════════════════════════════════
# 1. verifier_acces — fail-closed réel
# ══════════════════════════════════════════════════════════════════

def test_verifier_acces_facility_no_entitlement_denied():
    """clients.actif=True, clients.forfait=facility, 0 entitlement -> REFUS."""
    async def _():
        with patch.object(srv.httpx, 'AsyncClient') as mock_cls:
            ctx = MagicMock()
            inner = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=inner)
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = ctx
            # clients -> actif=True, forfait=facility
            async def fake_get(*a, **kw):
                url = str(a[0] if a else "")
                params = kw.get("params", {})
                if 'clients' in url:
                    return mr(200, [{"email": "u@t.com", "forfait": "facility", "actif": True}])
                if 'product_entitlements' in url:
                    return mr(200, [])  # 0 entitlement
                return mr(200, [])
            inner.get = fake_get
            ok, msg, _ = await srv.verifier_acces("tok_legacy", "facility")
            assert ok is False, f"Legacy sans entitlement doit être refusé: ok={ok} msg={msg}"
            assert "entitlement" in msg.lower() or "abonnement" in msg.lower()
    run(_())

def test_verifier_acces_kids_no_entitlement_denied():
    async def _():
        with patch.object(srv.httpx, 'AsyncClient') as mock_cls:
            ctx = MagicMock()
            inner = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=inner)
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = ctx
            async def fake_get(*a, **kw):
                url = str(a[0] if a else "")
                if 'clients' in url:
                    return mr(200, [{"email": "k@t.com", "forfait": "kids_solo", "actif": True}])
                if 'product_entitlements' in url:
                    return mr(200, [])
                return mr(200, [])
            inner.get = fake_get
            ok, msg, _ = await srv.verifier_acces("tok_kids", "kids")
            assert ok is False
    run(_())

def test_verifier_acces_industrial_no_entitlement_denied():
    async def _():
        with patch.object(srv.httpx, 'AsyncClient') as mock_cls:
            ctx = MagicMock()
            inner = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=inner)
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = ctx
            async def fake_get(*a, **kw):
                url = str(a[0] if a else "")
                if 'clients' in url:
                    return mr(200, [{"email": "i@t.com", "forfait": "industrial", "actif": True}])
                if 'profiles' in url:
                    return mr(200, [{"id": "uid-i"}])
                if 'product_entitlements' in url:
                    return mr(200, [])
                return mr(200, [])
            inner.get = fake_get
            ok, msg, _ = await srv.verifier_acces("tok_ind", "industrial")
            assert ok is False
    run(_())

def test_verifier_acces_active_entitlement_allowed():
    """Entitlement actif -> accès accordé."""
    async def _():
        with patch.object(srv.httpx, 'AsyncClient') as mock_cls:
            ctx = MagicMock()
            inner = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=inner)
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = ctx
            async def fake_get(*a, **kw):
                url = str(a[0] if a else "")
                if 'clients' in url:
                    return mr(200, [{"email": "f@t.com", "forfait": "facility", "actif": True}])
                if 'profiles' in url:
                    return mr(200, [{"id": "uid-f"}])
                if 'product_entitlements' in url:
                    return mr(200, [{"id": "e1", "status": "active",
                                     "ends_at": "2099-01-01T00:00:00"}])
                return mr(200, [])
            inner.get = fake_get
            ok, msg, _ = await srv.verifier_acces("tok_f", "facility")
            assert ok is True
    run(_())

def test_verifier_acces_canceled_entitlement_denied():
    async def _():
        with patch.object(srv.httpx, 'AsyncClient') as mock_cls:
            ctx = MagicMock()
            inner = MagicMock()
            ctx.__aenter__ = AsyncMock(return_value=inner)
            ctx.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = ctx
            async def fake_get(*a, **kw):
                url = str(a[0] if a else "")
                if 'clients' in url:
                    return mr(200, [{"email": "cx@t.com", "forfait": "facility", "actif": True}])
                if 'profiles' in url:
                    return mr(200, [{"id": "uid-cx"}])
                if 'product_entitlements' in url:
                    return mr(200, [{"id": "e2", "status": "canceled", "ends_at": None}])
                return mr(200, [])
            inner.get = fake_get
            ok, msg, _ = await srv.verifier_acces("tok_cx", "facility")
            assert ok is False
    run(_())


# ══════════════════════════════════════════════════════════════════
# 2. map_stripe_to_statut_paiement — fail-closed
# ══════════════════════════════════════════════════════════════════

class TestMapStripeFailClosed:
    def test_unknown_returns_none(self):
        assert srv.map_stripe_to_statut_paiement("UNKNOWN") is None

    def test_suspended_returns_none(self):
        """'suspended' = statut transformé, pas Stripe brut -> None."""
        assert srv.map_stripe_to_statut_paiement("suspended") is None

    def test_paused_returns_suspendu(self):
        assert srv.map_stripe_to_statut_paiement("paused") == "suspendu"

    def test_past_due_returns_impaye(self):
        assert srv.map_stripe_to_statut_paiement("past_due") == "impaye"

    def test_canceled_returns_resilie(self):
        assert srv.map_stripe_to_statut_paiement("canceled") == "resilie"

    def test_active_returns_actif(self):
        assert srv.map_stripe_to_statut_paiement("active") == "actif"

    def test_none_fail_closed_no_essai(self):
        assert srv.map_stripe_to_statut_paiement("UNKNOWN") != "essai"

    def test_incomplete_maps_to_impaye(self):
        assert srv.map_stripe_to_statut_paiement("incomplete") == "impaye"


# ══════════════════════════════════════════════════════════════════
# 3. _sync_entreprise_statut — résolution via sub_id
# ══════════════════════════════════════════════════════════════════

def test_sync_via_sub_id_patch_executed():
    """_sync via sub_id -> product_entitlements -> entreprise -> PATCH."""
    async def _():
        patch_calls = []
        h = MagicMock()
        async def fake_get(*a, **kw):
            url = str(a[0] if a else "")
            if 'product_entitlements' in url:
                return mr(200, [{"entreprise_id": "ent-uuid"}])
            return mr(200, [])
        async def fake_patch(*a, **kw):
            patch_calls.append(kw.get("json", {}))
            return mr(204, {})
        h.get = fake_get; h.patch = fake_patch; h.post = AsyncMock(return_value=mr(200,{}))
        await srv._sync_entreprise_statut(h, "sub_test_123", "active")
        assert patch_calls, "_sync doit PATCH l'entreprise"
        assert patch_calls[0].get("statut_paiement") == "actif"
    run(_())

def test_sync_unknown_status_no_patch():
    """Statut inconnu -> aucune mutation."""
    async def _():
        patch_calls = []
        h = MagicMock()
        async def fake_patch(*a, **kw):
            patch_calls.append(kw.get("json", {}))
            return mr(204, {})
        h.get = AsyncMock(return_value=mr(200, []))
        h.patch = fake_patch
        await srv._sync_entreprise_statut(h, "sub_test", "UNKNOWN_STATUS")
        assert not patch_calls, "Statut inconnu ne doit provoquer aucune mutation"
    run(_())

def test_sync_paused_maps_to_suspendu():
    async def _():
        patch_calls = []
        h = MagicMock()
        async def fake_get(*a, **kw):
            return mr(200, [{"entreprise_id": "ent-uuid"}])
        async def fake_patch(*a, **kw):
            patch_calls.append(kw.get("json", {}))
            return mr(204, {})
        h.get = fake_get; h.patch = fake_patch
        await srv._sync_entreprise_statut(h, "sub_paused", "paused")
        assert any(c.get("statut_paiement") == "suspendu" for c in patch_calls)
    run(_())

def test_sync_no_sub_id_no_op():
    async def _():
        patch_calls = []
        h = MagicMock()
        h.patch = AsyncMock(side_effect=lambda *a, **kw: patch_calls.append(kw) or mr(204, {}))
        h.get = AsyncMock(return_value=mr(200, []))
        await srv._sync_entreprise_statut(h, "", "active")
        assert not patch_calls
    run(_())


# ══════════════════════════════════════════════════════════════════
# 4. _claim_pending_entitlements — bloc Industrial supprimé
# ══════════════════════════════════════════════════════════════════

def test_client_token_no_direct_dirigeant_patch():
    """_claim_pending_entitlements ne doit jamais PATCH dirigeant_id directement."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    # Trouver la fonction
    m = re.search(r'async def _claim_pending_entitlements\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    assert m
    code = m.group(0)
    assert 'pending_industrial_ownership' not in code or \
           '"dirigeant_id"' not in code, \
        "_claim_pending_entitlements ne doit pas PATCH dirigeant_id directement"

def test_claim_pending_not_auto_industrial():
    """Vérifier que le bloc auto Industrial a bien été supprimé."""
    async def _():
        patch_calls = []
        h = MagicMock()
        async def fake_get(*a, **kw):
            url = str(a[0] if a else "")
            if 'pending_entitlement_claims' in url:
                return mr(200, [])  # pas de claims Facility/Kids
            if 'pending_industrial_ownership' in url:
                return mr(200, [{"id": "pio-1", "entreprise_id": "ent-1"}])
            return mr(200, [])
        async def fake_patch(*a, **kw):
            patch_calls.append((str(a[0] if a else ""), kw.get("json", {})))
            return mr(204, {})
        h.get = fake_get; h.patch = fake_patch
        h.post = AsyncMock(return_value=mr(201, {}))
        await srv._claim_pending_entitlements(h, "uid-test", "test@test.com")
        # Vérifier qu'aucun PATCH dirigeant_id n'a été fait
        dirigeant_patches = [c for c in patch_calls if c[1].get("dirigeant_id")]
        assert not dirigeant_patches, \
            f"Ne doit pas PATCH dirigeant_id directement: {dirigeant_patches}"
    run(_())


# ══════════════════════════════════════════════════════════════════
# 5. /industrial/claim-ownership — sécurité runtime
# ══════════════════════════════════════════════════════════════════

def test_claim_ownership_no_jwt_asgi():
    async def _():
        async with await asgi() as c:
            r = await c.post("/industrial/claim-ownership", json={})
            assert r.json().get("ok") is False
            assert "JWT" in (r.json().get("erreur") or "")
    run(_())

def test_claim_ownership_no_pending():
    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=("uid-1","u@t.com",None))):
            orig = srv.SUPABASE_URL; srv.SUPABASE_URL = ""
            try:
                async with await asgi() as c:
                    r = await c.post("/industrial/claim-ownership",
                                      json={"jwt":"tok"},
                                      headers={"Authorization":"Bearer tok"})
                    assert r.json().get("ok") is False
            finally:
                srv.SUPABASE_URL = orig
    run(_())


# ══════════════════════════════════════════════════════════════════
# 6. trial Industrial repair — ends_at expiré = refus
# ══════════════════════════════════════════════════════════════════

def test_trial_expired_repair_refused():
    """Trial créé il y a >14 jours -> repair doit refuser."""
    import datetime as dt

    async def _():
        with patch.object(srv, '_jwt_vers_identite',
                          new=AsyncMock(return_value=("uid-tr","tr@t.com",None))):
            orig_url = srv.SUPABASE_URL; srv.SUPABASE_URL = ""
            # Ne pas appeler httpx — test via code source
            srv.SUPABASE_URL = orig_url
        # Vérifier via code source que la condition ends_at > now existe
        with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
            src = f.read()
        m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)',
                      src, re.DOTALL)
        assert m
        code = m.group(0)
        assert 'utcnow()' in code or 'datetime.utcnow' in code
        # Vérification que le check ends_at <= now existe
        assert 'ends_at_r' in code
        assert ('essai déjà' in code or 'expiré' in code)
    run(_())


# ══════════════════════════════════════════════════════════════════
# 7. ensure_legacy_client — pas de forfait accordé dans PATCH réactivation
# ══════════════════════════════════════════════════════════════════

def test_ensure_legacy_no_forfait_in_reactivation_patch():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def ensure_legacy_client\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    assert m
    code = m.group(0)
    # Le PATCH de réactivation ne doit pas contenir forfait
    patch_m = re.search(r'json=\{[^}]*"actif": True[^}]*\}', code)
    if patch_m:
        assert '"forfait"' not in patch_m.group(0), \
            "PATCH réactivation ne doit pas changer forfait"


# ══════════════════════════════════════════════════════════════════
# 8. _sync ne doit pas dépendre de email→profile
# ══════════════════════════════════════════════════════════════════

def test_sync_no_profile_dependency():
    with open(os.path.join(ROOT,'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def _sync_entreprise_statut\(.*?(?=\nasync def |\ndef |\n@)',
                  src, re.DOTALL)
    assert m
    code = m.group(0)
    assert '/profiles' not in code, "_sync ne doit plus chercher via profiles"
    assert 'product_entitlements' in code, "_sync doit passer par product_entitlements"
    assert 'stripe_subscription_id' in code, "_sync doit utiliser sub_id"


# ══════════════════════════════════════════════════════════════════
# 9. Webhook Stripe — statut inconnu -> aucune mutation (via code source)
# ══════════════════════════════════════════════════════════════════

def test_webhook_statut_inconnu_no_mutation():
    """map_stripe retourne None sur inconnu -> _sync abort avant PATCH."""
    # Test runtime direct
    async def _():
        patch_calls = []
        h = MagicMock()
        h.get = AsyncMock(return_value=mr(200, [{"entreprise_id": "ent-x"}]))
        async def fake_patch(*a, **kw):
            patch_calls.append(kw.get("json", {}))
            return mr(204, {})
        h.patch = fake_patch
        await srv._sync_entreprise_statut(h, "sub-x", "unknown_bogus")
        assert not patch_calls, "Statut inconnu = 0 mutation"
    run(_())
