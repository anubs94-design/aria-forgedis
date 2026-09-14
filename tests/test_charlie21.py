"""Charlie 21 — final entitlement/Stripe/Industrial closure regressions."""
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

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


class Resp:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = ""
    def json(self):
        return self._data


class FakeClient:
    def __init__(self, row):
        self.row = row
        self.patches = []
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        return False
    async def get(self, url, **kwargs):
        if url.endswith("/rest/v1/clients"):
            return Resp([self.row])
        raise AssertionError(url)
    async def patch(self, url, **kwargs):
        self.patches.append((url, kwargs))
        return Resp([], 204)


def test_verifier_forfait_canonical_active_ignores_legacy_inactive(monkeypatch):
    fake = FakeClient({"email": "x@example.com", "token": "tok", "forfait": "gratuit",
                       "actif": False, "taches_ce_mois": 4, "mois_en_cours": ""})
    monkeypatch.setattr(srv.httpx, "AsyncClient", lambda *a, **k: fake)
    monkeypatch.setattr(srv, "verifier_acces", AsyncMock(return_value=(True, "", "facility")))
    ok, msg, plan = asyncio.run(srv.verifier_forfait("tok", "reflexion"))
    assert ok is True and plan == "facility"
    assert fake.patches


def test_verifier_forfait_legacy_paid_without_entitlement_denied(monkeypatch):
    fake = FakeClient({"email": "x@example.com", "token": "tok", "forfait": "facility",
                       "actif": True, "taches_ce_mois": 0, "mois_en_cours": ""})
    monkeypatch.setattr(srv.httpx, "AsyncClient", lambda *a, **k: fake)
    monkeypatch.setattr(srv, "verifier_acces", AsyncMock(return_value=(False, "Abonnement introuvable", "no_entitlement")))
    ok, msg, plan = asyncio.run(srv.verifier_forfait("tok", "eco"))
    assert ok is False
    assert plan == "inactif"


def test_stripe_projection_dates_are_utc_aware():
    sub = {
        "status": "active",
        "items": {"data": [{
            "price": {"id": "price_fac"},
            "current_period_start": 1780000000,
            "current_period_end": 1781000000,
        }]},
    }
    status, starts, ends = srv._project_stripe_sub_data(sub, {"price_fac": "facility"}, srv.INDUSTRIAL_BASE_PRICE)
    assert status == "active"
    assert starts.endswith("+00:00") and ends.endswith("+00:00")


def test_raw_stripe_mapping_is_fail_closed():
    assert srv.map_stripe_to_statut_paiement("paused") == "suspendu"
    assert srv.map_stripe_to_statut_paiement("canceled") == "resilie"
    assert srv.map_stripe_to_statut_paiement("suspended") is None
    assert srv.map_stripe_to_statut_paiement("UNKNOWN") is None


def test_checkout_never_maps_projected_status_to_company():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    assert "map_stripe_to_statut_paiement(sub_status_real" not in src
    assert "_mapped_sp = map_stripe_to_statut_paiement(_stripe_status)" in src


def test_existing_industrial_company_owner_path_is_atomic():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    assert "entreprise_preexistante = bool(entreprise_id)" in src
    assert '"dirigeant_id": "is.null"' in src
    assert '"existing_company": True' in src


def test_subscription_deleted_does_not_invent_now_as_end_date():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    a = src.index('elif event_type == "customer.subscription.deleted":')
    b = src.index('elif event_type in ("invoice.paid", "invoice.payment_succeeded"):', a)
    block = src[a:b]
    assert '"ends_at": _dt_m.datetime.utcnow().isoformat()' not in block
    assert '_sd_ends' in block


def test_pending_claim_mark_is_verified():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    a = src.index("async def _claim_pending_entitlements")
    b = src.index('@app.post("/client-token")', a)
    block = src[a:b]
    assert '"status": "eq.pending"' in block
    assert '"Prefer": "return=representation"' in block
    assert "r_mark.status_code" in block


def test_pending_industrial_subscription_unique_migration_present():
    path = ROOT / "supabase" / "migrations" / "20260914013014_phase_k_pending_industrial_subscription_unique.sql"
    assert path.exists()
    sql = path.read_text(encoding="utf-8")
    assert "unique index" in sql.lower()
    assert "stripe_subscription_id" in sql

# CI gate trigger after generated P0 closure commit.
