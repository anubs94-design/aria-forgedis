
"""
Tests Charlie 17 — P0 finaux :
- _sync False -> 503 dans les handlers
- invoice statut brut (paused->suspendu, canceled->resilie)
- claim already_owned PATCH pending 500 -> ok=False
- ends_at timezone-aware, parsing invalide = refus
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

def mr(s, d):
    m = MagicMock(); m.status_code = s
    m.json = MagicMock(return_value=d); m.text = json.dumps(d)
    return m

def hc(g=(), p=(), r=()):
    h = MagicMock()
    gq=list(g); pq=list(p); rq=list(r)
    async def _g(*a,**kw): return gq.pop(0) if gq else mr(200,[])
    async def _p(*a,**kw): return rq.pop(0) if rq else mr(204,{})
    async def _o(*a,**kw): return pq.pop(0) if pq else mr(201,{})
    h.get=_g; h.patch=_p; h.post=_o
    return h


# ══════════════════════════════════════════════════════════════════
# 1. _sync False -> _fail + 503 dans les handlers (structurel)
# ══════════════════════════════════════════════════════════════════

def test_sync_fail_blocks_complete_in_all_handlers():
    """Si _sync KO, _complete ne doit jamais être appelé."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    handlers = [
        ('"customer.subscription.created"', '_sync_ok_sc'),
        ('"customer.subscription.updated"', '_sync_ok_su'),
        ('"customer.subscription.deleted"', '_sync_ok_sd'),
        ('"invoice.paid"', '_sync_ok_ip'),
        ('invoice.payment_failed', '_sync_ok_if'),
    ]
    for event_str, sync_var in handlers:
        idx = src.find(event_str)
        idx_end = src.find('\n    elif event_type', idx + 100)
        block = src[idx:idx_end]
        # La vérification sync_ok doit être suivie d'un return 503
        sync_check = block.find(f'if not {sync_var}')
        assert sync_check >= 0, f"{event_str}: bloc if not {sync_var} absent"
        # Le return 503 doit être AVANT _complete
        fail_return = block.find('return JSONResponse(status_code=503', sync_check)
        complete_pos = block.find('await _complete(', sync_check)
        assert fail_return > sync_check, f"{event_str}: return 503 manquant après sync_ok=False"
        assert fail_return < complete_pos, \
            f"{event_str}: return 503 doit précéder _complete (fail_return={fail_return}, complete={complete_pos})"

def test_sync_false_does_not_call_complete():
    """_sync retourne False -> handler doit sortir avant _complete."""
    # Vérification via code source : "if not _sync_ok" doit mener à un return 503
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        if 'if not _sync_ok_' in l:
            ind = len(l) - len(l.lstrip())
            # Les 5 lignes suivantes doivent contenir un return 503 AVANT ok_c = await _complete
            block = ''.join(lines[i:min(i+6, len(lines))])
            has_503 = 'status_code=503' in block
            has_complete_before = 'ok_c = await _complete' in block[:block.find('503')+1] if has_503 else False
            assert has_503, f"L{i+1}: if not _sync_ok doit mener à return 503"
            assert not has_complete_before, f"L{i+1}: _complete ne doit pas précéder le return 503"


# ══════════════════════════════════════════════════════════════════
# 2. Invoice : statut Stripe brut (pas "active"/"past_due" en dur)
# ══════════════════════════════════════════════════════════════════

def test_invoice_paid_uses_stripe_raw_status():
    """invoice.paid _sync doit utiliser _stripe_status_ip (statut brut Stripe)."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"invoice.paid"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    # Doit avoir _stripe_status_ip (variable capturant le statut brut)
    assert '_stripe_status_ip' in block, \
        "invoice.paid doit capturer _stripe_status_ip = rs.json()['status']"
    # Ne doit pas passer "active" en dur à _sync
    sync_call = re.search(r'await _sync_entreprise_statut\([^)]+\)', block)
    assert sync_call, "invoice.paid doit appeler _sync"
    assert '"active"' not in sync_call.group(0) or '_stripe_status_ip' in sync_call.group(0), \
        "invoice.paid ne doit pas passer 'active' en dur si le statut Stripe peut être différent"

def test_invoice_failed_uses_stripe_raw_status():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"invoice.payment_failed"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    assert '_stripe_status_if_raw' in block, \
        "invoice.failed doit capturer _stripe_status_if_raw"

def test_paused_produces_suspendu_in_sync():
    """Stat brut paused -> _sync -> suspendu."""
    async def _():
        calls = []
        h = hc(g=[mr(200, [{"entreprise_id":"ent-p"}])])
        async def track(*a, **kw):
            calls.append(kw.get("json",{}))
            return mr(200, [{"id":"ent-p"}])
        h.patch = track
        ok = await srv._sync_entreprise_statut(h, "sub-p", "paused")
        assert ok is True
        assert calls and calls[-1].get("statut_paiement") == "suspendu"
    run(_())

def test_canceled_produces_resilie_in_sync():
    async def _():
        calls = []
        h = hc(g=[mr(200, [{"entreprise_id":"ent-c"}])])
        async def track(*a, **kw):
            calls.append(kw.get("json",{})); return mr(200, [{"id":"ent-c"}])
        h.patch = track
        ok = await srv._sync_entreprise_statut(h, "sub-c", "canceled")
        assert ok is True
        assert calls and calls[-1].get("statut_paiement") == "resilie"
    run(_())


# ══════════════════════════════════════════════════════════════════
# 3. Claim already_owned : PATCH pending fail -> ok=False
# ══════════════════════════════════════════════════════════════════

def test_claim_already_owned_patch_fail_returns_false():
    """Dans la branche already_owned, si PATCH pending échoue -> ok=False."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    # Capturer le bloc complet including the 2 continue statements
    m = re.search(r'if existing_dir == auth_uid:.*?continue\s*\n', src, re.DOTALL)
    assert m
    # Utiliser le bloc étendu jusqu'à "already_owned"
    idx_start = src.find('if existing_dir == auth_uid:')
    idx_end = src.find('already_owned')
    assert idx_end > idx_start, "already_owned doit exister après existing_dir == auth_uid"
    branch = src[idx_start:idx_end+50]
    # Le code doit : 1) capturer r_claim_idem, 2) vérifier status_code, 3) ok=False si échec
    assert 'r_claim_idem' in branch, "Branche idempotente doit capturer r_claim_idem"
    assert 'status_code' in branch, "Doit vérifier le status_code du PATCH"
    assert '"ok": False' in branch, "Doit retourner ok=False si PATCH échoue"
    # Ordre : vérification échec AVANT already_owned
    fail_pos = branch.find('"ok": False')
    owned_pos = branch.find('already_owned')
    assert fail_pos < owned_pos, \
        f"ok=False ({fail_pos}) doit précéder already_owned ({owned_pos})"


# ══════════════════════════════════════════════════════════════════
# 4. parse_utc_timestamp + is_expired helpers
# ══════════════════════════════════════════════════════════════════

def test_parse_utc_timestamp_z():
    result = srv.parse_utc_timestamp("2099-01-01T00:00:00Z")
    assert result is not None
    assert result.tzinfo is not None

def test_parse_utc_timestamp_offset():
    result = srv.parse_utc_timestamp("2099-01-01T00:00:00+00:00")
    assert result is not None

def test_parse_utc_timestamp_invalid_returns_none():
    assert srv.parse_utc_timestamp("not-a-date") is None
    assert srv.parse_utc_timestamp("") is None
    assert srv.parse_utc_timestamp(None) is None

def test_is_expired_past():
    past = "2020-01-01T00:00:00Z"
    assert srv.is_expired(past) is True

def test_is_expired_future():
    future = "2099-01-01T00:00:00Z"
    assert srv.is_expired(future) is False

def test_is_expired_future_with_offset():
    future = "2099-01-01T00:00:00+00:00"
    assert srv.is_expired(future) is False

def test_is_expired_invalid_returns_true():
    """Parsing invalide = expiré (fail-closed)."""
    assert srv.is_expired("garbage") is True

def test_is_expired_none_returns_false():
    """None = pas de date = non expiré."""
    assert srv.is_expired(None) is False
    assert srv.is_expired("") is False

def test_ends_at_aware_naive_comparison_safe():
    """Pas de TypeError entre aware et naive."""
    # Ce test aurait échoué avec l'ancien code sur un timestamptz "+00:00"
    aware_str = "2020-01-01T00:00:00+00:00"
    # is_expired doit gérer ça sans exception
    result = srv.is_expired(aware_str)
    assert isinstance(result, bool)

def test_no_except_pass_on_expiry():
    """Aucun 'except Exception: pass' sur une décision d'expiration."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    # Chercher les blocs try/except pass qui entourent is_expired ou fromisoformat
    # Ces blocs ne doivent plus exister dans les contextes d'expiration
    bad_patterns = re.findall(
        r'try:\s+if is_expired\([^)]+\):[^}]+except Exception:\s+pass',
        src, re.DOTALL
    )
    assert not bad_patterns, \
        f"try/except pass autour de is_expired encore présent: {bad_patterns}"


# ══════════════════════════════════════════════════════════════════
# 5. _rs_ip et _rs_if accessibles dans le contexte invoice
# ══════════════════════════════════════════════════════════════════

def test_stripe_status_ip_extracted_from_rs():
    """_stripe_status_ip doit venir de _rs_ip.json(), pas être hardcodé."""
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"invoice.paid"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    # _stripe_status_ip = _rs_ip.json().get("status") doit exister
    assert '_rs_ip' in block and '_stripe_status_ip' in block, \
        "_stripe_status_ip doit être extrait de _rs_ip"
    # La variable doit être définie avant l'appel _sync
    status_def = block.find('_stripe_status_ip')
    sync_call = block.find('_sync_ok_ip')
    assert status_def < sync_call, "_stripe_status_ip doit être défini avant _sync"

def test_stripe_status_if_extracted_from_rs():
    with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
        src = f.read()
    idx = src.find('"invoice.payment_failed"')
    idx_end = src.find('\n    elif event_type', idx + 100)
    block = src[idx:idx_end]
    assert '_rs_if' in block and '_stripe_status_if_raw' in block
    status_def = block.find('_stripe_status_if_raw')
    sync_call = block.find('_sync_ok_if')
    assert status_def < sync_call
