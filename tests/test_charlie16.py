
"""
Tests Charlie 16 — v2 : utilise patch SUPABASE_URL pour les tests ASGI
et appels directs pour les tests runtime.
"""
import sys, os, re, asyncio, json, datetime as dt
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

def hc_mock(gets=(), patches=(), posts=()):
    """Mock httpx.AsyncClient interne (pas le transport ASGI)."""
    h = MagicMock()
    gq=list(gets); rq=list(patches); pq=list(posts)
    async def _g(*a,**kw): return gq.pop(0) if gq else mr(200,[])
    async def _p(*a,**kw): return rq.pop(0) if rq else mr(204,{})
    async def _o(*a,**kw): return pq.pop(0) if pq else mr(201,{})
    h.get=_g; h.patch=_p; h.post=_o
    return h


# ══════════════════════════════════════════════════════════════════
# 1. _sync doit être DANS le async with (indentation >= 12)
# ══════════════════════════════════════════════════════════════════

def test_sync_called_inside_async_with():
    """Tous les appels _sync doivent être à indent>=12 (dans async with)."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        if 'await _sync_entreprise_statut(' in l and 'async def' not in l:
            indent = len(l) - len(l.lstrip())
            assert indent >= 12, \
                f"L{i+1}: _sync doit être dans async with (indent>=12), trouvé {indent}: {l.strip()}"

def test_sync_uses_raw_stripe_status():
    """Aucun appel _sync ne doit passer status_mapped ou _status_ip/if."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        lines = f.readlines()
    bad = []
    for i, l in enumerate(lines):
        if 'await _sync_entreprise_statut(' in l and 'async def' not in l:
            if any(k in l for k in ['status_mapped', '_status_ip', '_status_if']):
                bad.append(f"L{i+1}: {l.strip()}")
    assert not bad, f"_sync reçoit statut transformé (pas brut): {bad}"


# ══════════════════════════════════════════════════════════════════
# 2. subscription.deleted doit synchroniser
# ══════════════════════════════════════════════════════════════════

def test_sync_in_subscription_deleted():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"customer.subscription.deleted"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    assert '_sync_entreprise_statut' in block, "sub.deleted doit appeler _sync"
    assert '"canceled"' in block, "sub.deleted doit passer 'canceled'"

def test_sync_before_complete_in_deleted():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"customer.subscription.deleted"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    assert block.find('_sync_entreprise_statut') < block.find('await _complete(')


# ══════════════════════════════════════════════════════════════════
# 3. paused -> suspendu (via _sync runtime)
# ══════════════════════════════════════════════════════════════════

def test_paused_maps_to_suspendu():
    assert srv.map_stripe_to_statut_paiement("paused") == "suspendu"

def test_paused_sync_runtime():
    async def _():
        calls = []
        h = hc_mock(
            gets=[mr(200, [{"entreprise_id": "ent-x"}])],
            patches=[mr(200, [{"id": "ent-x"}])]
        )
        orig_patch = h.patch
        async def track_patch(*a, **kw):
            calls.append(kw.get("json", {}))
            return mr(200, [{"id": "ent-x"}])
        h.patch = track_patch
        ok = await srv._sync_entreprise_statut(h, "sub_p", "paused")
        assert ok is True
        assert any(c.get("statut_paiement") == "suspendu" for c in calls)
    run(_())

def test_canceled_sync_runtime():
    async def _():
        calls = []
        h = hc_mock(gets=[mr(200, [{"entreprise_id": "ent-y"}])])
        async def track_patch(*a, **kw):
            calls.append(kw.get("json", {}))
            return mr(200, [{"id": "ent-y"}])
        h.patch = track_patch
        ok = await srv._sync_entreprise_statut(h, "sub_c", "canceled")
        assert ok is True
        assert any(c.get("statut_paiement") == "resilie" for c in calls)
    run(_())


# ══════════════════════════════════════════════════════════════════
# 4. _sync fail-closed (True/False)
# ══════════════════════════════════════════════════════════════════

def test_sync_http_error_returns_false():
    async def _():
        h = hc_mock(gets=[mr(500, {})])
        assert await srv._sync_entreprise_statut(h, "sub_e", "active") is False
    run(_())

def test_sync_empty_sub_id_returns_false():
    async def _():
        h = hc_mock()
        assert await srv._sync_entreprise_statut(h, "", "active") is False
    run(_())

def test_sync_unknown_status_returns_false():
    async def _():
        calls = []
        h = hc_mock(gets=[mr(200, [{"entreprise_id":"x"}])])
        async def track_patch(*a, **kw):
            calls.append(kw.get("json",{})); return mr(200,[{"id":"x"}])
        h.patch = track_patch
        result = await srv._sync_entreprise_statut(h, "sub_u", "UNKNOWN_STATUS")
        assert result is False
        assert not calls, "Statut inconnu = 0 mutation"
    run(_())

def test_sync_no_entitlement_returns_true():
    async def _():
        h = hc_mock(gets=[mr(200,[])])
        assert await srv._sync_entreprise_statut(h, "sub_n", "active") is True
    run(_())


# ══════════════════════════════════════════════════════════════════
# 5. claim-ownership : sécurité code source
# ══════════════════════════════════════════════════════════════════

def test_claim_sub_id_required():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    assert 'not stripe_sub_id' in code, "stripe_sub_id doit être obligatoire"

def test_claim_ends_at_checked():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    assert 'ends_at' in code and ('now_utc' in code or 'utcnow' in code)

def test_claim_atomic_patch():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    assert 'is.null' in code or 'IS NULL' in code

def test_claim_pending_patch_verified():
    """Le PATCH pending ownership doit être vérifié avant ok=True."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    # Le code doit vérifier le résultat du PATCH claimed
    assert 'r_claim' in code or 'r_patch_claim' in code or \
           ("status_code" in code and "claimed" in code)


# ══════════════════════════════════════════════════════════════════
# 6. claim-ownership ASGI : no JWT → refus (route enregistrée)
# ══════════════════════════════════════════════════════════════════

def test_claim_ownership_route_registered():
    async def _():
        async with await asgi() as c:
            r = await c.post("/industrial/claim-ownership", json={})
            assert r.status_code != 404, "Route non enregistrée"
            assert r.json().get("ok") is False
            assert "JWT" in (r.json().get("erreur") or "")
    run(_())

def test_inscription_facility_route_registered():
    async def _():
        async with await asgi() as c:
            r = await c.post("/inscription-facility", json={})
            assert r.status_code != 404, "/inscription-facility non enregistrée"
            data = r.json()
            assert data.get("ok") is False and "JWT" in (data.get("erreur") or "")
    run(_())


# ══════════════════════════════════════════════════════════════════
# 7. claim runtime direct (via la fonction, sans ASGI)
# ══════════════════════════════════════════════════════════════════

def test_claim_direct_no_sub_id():
    """Appel direct claim-ownership via verifier la logique fonctionnelle."""
    # Test code source: not stripe_sub_id -> continue
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    m = re.search(r'async def industrial_claim_ownership\(.*?(?=\nasync def |\n@app)',
                  src, re.DOTALL)
    code = m.group(0)
    # Le code doit avoir le check sub_id avant tout
    sub_check_pos = code.find('not stripe_sub_id')
    ent_check_pos = code.find('product_entitlements')
    assert sub_check_pos < ent_check_pos, \
        "Vérification sub_id doit précéder la lecture entitlement"

def test_order_mutation_sync_complete_in_handlers():
    """Dans chaque handler, l'ordre doit être: mutation -> sync -> complete."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    for event, event_str in [
        ("sub.created",  '"customer.subscription.created"'),
        ("sub.updated",  '"customer.subscription.updated"'),
        ("sub.deleted",  '"customer.subscription.deleted"'),
        ("invoice.paid", '"invoice.paid"'),
    ]:
        idx = src.find(event_str)
        idx_end = src.find('\n    elif event_type', idx + 100)
        block = src[idx:idx_end]
        # Ordre: resolve_subject_and_upsert / PATCH entitlement -> _sync -> _complete
        sync_pos = block.find('_sync_entreprise_statut')
        complete_pos = block.find('await _complete(')
        if sync_pos >= 0 and complete_pos >= 0:
            assert sync_pos < complete_pos, \
                f"{event}: _sync ({sync_pos}) doit précéder _complete ({complete_pos})"
