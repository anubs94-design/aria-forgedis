from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
src = SERVER.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, got {n}")
    return text.replace(old, new, 1)


# 1) Documentation: clients is compatibility/token only, never a product-right fallback.
src = replace_once(
    src,
    "    clients.forfait : fallback migration uniquement si aucun entitlement canonique\n",
    "    clients : compatibilite/token uniquement, jamais source de droits produit\n",
    "verifier_acces doc",
)

# Remove stale unused legacy variable in verifier_acces only.
va_start = src.index("async def verifier_acces")
va_end = src.index("async def verifier_forfait", va_start)
va = src[va_start:va_end]
va = replace_once(
    va,
    '            forfait_legacy = client_data.get("forfait", "gratuit")\n',
    "",
    "verifier_acces forfait_legacy",
)
src = src[:va_start] + va + src[va_end:]

# 2) verifier_forfait: canonical Facility entitlement first; legacy free tier only when no entitlement exists.
vf_start = src.index("async def verifier_forfait")
vf_end = src.index("# --- STRIPE WEBHOOK ---", vf_start)
vf = src[vf_start:vf_end]
pattern = re.compile(
    r'''            client_data = data\[0\]\n\n\n\n.*?            # Incrementer le compteur\n''',
    re.S,
)
replacement = '''            client_data = data[0]\n\n            forfait_legacy = client_data.get("forfait", "gratuit")\n            try:\n                taches = int(client_data.get("taches_ce_mois", 0) or 0)\n            except (TypeError, ValueError):\n                taches = 0\n\n            # Autorite commerciale: product_entitlements Facility.\n            # Le legacy ne peut accorder que le palier gratuit si aucun entitlement n'existe.\n            ok_canon, msg_canon, canon_state = await verifier_acces(token_recu, "facility")\n            if ok_canon:\n                forfait = "facility"\n            elif canon_state == "no_entitlement":\n                if forfait_legacy != "gratuit":\n                    return False, msg_canon or "Abonnement Facility requis.", "inactif"\n                if not client_data.get("actif", False):\n                    return False, "Votre compte gratuit est inactif. Contactez le support.", "inactif"\n                forfait = "gratuit"\n            else:\n                # blocked / unknown / erreur: jamais de repli vers clients.forfait.\n                return False, msg_canon or "Verification d'abonnement impossible.", "inactif"\n\n            mois = client_data.get("mois_en_cours", "")\n\n            import datetime\n            mois_actuel = datetime.datetime.now().strftime("%Y-%m")\n            if mois != mois_actuel:\n                taches = 0\n                mois = mois_actuel\n\n            if forfait == "gratuit":\n                if type_requete == "reflexion":\n                    return False, "Le pilotage PC est reserve a Aria Facility (12,99 euros/mois). Passez a Facility pour debloquer toutes les fonctions.", "gratuit"\n                if taches >= 30:\n                    return False, "Vous avez utilise vos 30 eco-taches du mois. Passez a Aria Facility pour continuer.", "gratuit"\n\n            # Incrementer le compteur\n'''
vf2, n = pattern.subn(replacement, vf, count=1)
if n != 1:
    raise RuntimeError(f"verifier_forfait canonical replacement: got {n}")
src = src[:vf_start] + vf2 + src[vf_end:]

# 3) Kids access response must report canonical authorization, not legacy forfait/actif.
src = replace_once(
    src,
    '                "forfait": cl.get("forfait", forfait),  # forfait depuis Supabase, jamais du client\n                "email": cl.get("email", ""),\n                "actif": cl.get("actif", False),\n',
    '                "forfait": forfait,  # valeur canonique issue de verifier_acces\n                "email": cl.get("email", ""),\n                "actif": True,  # verifier_acces a deja valide le droit Kids\n',
    "verify_kids_access canonical response",
)

# 4) Kids token compatibility: reuse ensure_legacy_client after canonical entitlement validation.
ctk_start = src.index("async def client_token_kids")
ctk_end = src.index("@app.get(\"/profil-kids\")", ctk_start)
ctk = src[ctk_start:ctk_end]
ctk_pattern = re.compile(
    r'''            # Récupérer ou créer le token client legacy\n.*?            return \{"token": new_tok, "forfait": "kids", "source": "entitlement"\}\n''',
    re.S,
)
ctk_repl = '''            # Token legacy = compatibilite uniquement, apres validation canonique Kids.\n            legacy = await ensure_legacy_client(hx, email, "kids_solo")\n            return {"token": legacy["token"], "forfait": "kids", "source": "entitlement"}\n'''
ctk2, n = ctk_pattern.subn(ctk_repl, ctk, count=1)
if n != 1:
    raise RuntimeError(f"client_token_kids legacy replacement: got {n}")
src = src[:ctk_start] + ctk2 + src[ctk_end:]

# 5) ensure_legacy_client: respect explicit deletion requests; otherwise reactivation is compatibility only.
src = replace_once(
    src,
    '        params={"email": f"eq.{email}", "select": "token,forfait,actif"},\n',
    '        params={"email": f"eq.{email}", "select": "token,forfait,actif,suppression_demandee"},\n',
    "ensure_legacy_client select",
)
src = replace_once(
    src,
    '    if existing:\n        # Réactiver si nécessaire\n        if not existing[0].get("actif"):\n',
    '    if existing:\n        if existing[0].get("suppression_demandee"):\n            raise RuntimeError("Compte en cours de suppression: reactivation automatique interdite")\n        # Réactiver le conteneur legacy si nécessaire; les droits restent canoniques ailleurs.\n        if not existing[0].get("actif"):\n',
    "ensure_legacy_client deletion guard",
)

# 6) Pending user claims: mark claimed only after verified mutation.
src = replace_once(
    src,
    '''            if success:\n\n                await hc.patch(\n\n                    f"{SUPABASE_URL}/rest/v1/pending_entitlement_claims",\n\n                    params={"id": f"eq.{claim['id']}"},\n\n                    headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",\n\n                             "Content-Type": "application/json", "Prefer": "return=minimal"},\n\n                    json={"status": "claimed"}\n\n                )\n\n                print(f"[client-token] claim {claim['id']} consomme pour {email} -> {product_val}/{ent_status}")\n''',
    '''            if success:\n\n                r_mark = await hc.patch(\n\n                    f"{SUPABASE_URL}/rest/v1/pending_entitlement_claims",\n\n                    params={"id": f"eq.{claim['id']}", "status": "eq.pending"},\n\n                    headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",\n\n                             "Content-Type": "application/json", "Prefer": "return=representation"},\n\n                    json={"status": "claimed"}\n\n                )\n\n                if r_mark.status_code not in (200, 201) or not r_mark.json():\n                    print(f"[client-token] WARN claim {claim['id']} entitlement upsert OK mais consommation pending echouee")\n                    continue\n\n                print(f"[client-token] claim {claim['id']} consomme pour {email} -> {product_val}/{ent_status}")\n''',
    "pending claim verified mutation",
)

# 7) Stripe timestamps: store explicit UTC-aware ISO values.
src = replace_once(
    src,
    '        ends_at = _dt_proj.datetime.fromtimestamp(trial_end).isoformat()\n',
    '        ends_at = _dt_proj.datetime.fromtimestamp(trial_end, _dt_proj.timezone.utc).isoformat()\n',
    "stripe trial_end UTC",
)
src = replace_once(
    src,
    '        ends_at = _dt_proj.datetime.fromtimestamp(period_end).isoformat()\n',
    '        ends_at = _dt_proj.datetime.fromtimestamp(period_end, _dt_proj.timezone.utc).isoformat()\n',
    "stripe period_end UTC",
)
src = replace_once(
    src,
    '        starts_at = _dt_proj.datetime.fromtimestamp(period_start).isoformat()\n',
    '        starts_at = _dt_proj.datetime.fromtimestamp(period_start, _dt_proj.timezone.utc).isoformat()\n',
    "stripe period_start UTC",
)

# 8) Checkout Industrial: map entreprises status from RAW Stripe status, never projected status.
src = replace_once(
    src,
    '''                    _dirigeant_id = _prof_co[0]["id"] if len(_prof_co) == 1 else None\n                    _ent_payload = {"email_contact": email, "nom": _nom,\n''',
    '''                    _dirigeant_id = _prof_co[0]["id"] if len(_prof_co) == 1 else None\n                    _mapped_sp = map_stripe_to_statut_paiement(_stripe_status)\n                    if _mapped_sp is None:\n                        await _fail(client, f"industrial_unknown_stripe_status:{_stripe_status}")\n                        return JSONResponse(status_code=503, content={"erreur": "stripe_status_inconnu"})\n                    _ent_payload = {"email_contact": email, "nom": _nom,\n''',
    "checkout raw status pre-map",
)
src = replace_once(
    src,
    '                                       "statut_paiement": map_stripe_to_statut_paiement(sub_status_real or "trialing"),\n',
    '                                       "statut_paiement": _mapped_sp,\n',
    "checkout raw status mapping",
)

# Track whether the company existed before this checkout.
src = replace_once(
    src,
    '''                entreprise_id = await get_entreprise_id(client, email)\n\n                if not entreprise_id:\n''',
    '''                entreprise_id = await get_entreprise_id(client, email)\n                entreprise_preexistante = bool(entreprise_id)\n\n                if not entreprise_id:\n''',
    "checkout existing company flag",
)

# Existing company with no owner: attach matching authenticated profile atomically, or create pending ownership.
marker = '''                            print(f"[checkout] pending_industrial_ownership créé pour {email}")\n                if not entreprise_id:\n'''
insert = '''                            print(f"[checkout] pending_industrial_ownership créé pour {email}")\n\n                if entreprise_preexistante and entreprise_id:\n                    _r_existing_company = await client.get(\n                        f"{SUPABASE_URL}/rest/v1/entreprises",\n                        params={"id": f"eq.{entreprise_id}", "select": "id,dirigeant_id"},\n                        headers={"apikey": SUPABASE_SERVICE_KEY,\n                                 "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}\n                    )\n                    _existing_company_rows = _r_existing_company.json() if _r_existing_company.status_code == 200 else []\n                    if len(_existing_company_rows) != 1:\n                        await _fail(client, "existing_industrial_company_unresolvable")\n                        return JSONResponse(status_code=503, content={"erreur": "entreprise_existante_invalide"})\n                    _existing_owner = _existing_company_rows[0].get("dirigeant_id")\n                    _r_prof_existing = await client.get(\n                        f"{SUPABASE_URL}/rest/v1/profiles",\n                        params={"email": f"eq.{email.lower().strip()}", "select": "id"},\n                        headers={"apikey": SUPABASE_SERVICE_KEY,\n                                 "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}\n                    )\n                    _prof_existing = _r_prof_existing.json() if _r_prof_existing.status_code == 200 else []\n                    _existing_uid = _prof_existing[0].get("id") if len(_prof_existing) == 1 else None\n                    if not _existing_owner and _existing_uid:\n                        _r_claim_existing = await client.patch(\n                            f"{SUPABASE_URL}/rest/v1/entreprises",\n                            params={"id": f"eq.{entreprise_id}", "dirigeant_id": "is.null"},\n                            headers={"apikey": SUPABASE_SERVICE_KEY,\n                                     "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",\n                                     "Content-Type": "application/json",\n                                     "Prefer": "return=representation"},\n                            json={"dirigeant_id": _existing_uid}\n                        )\n                        if _r_claim_existing.status_code not in (200, 201) or not _r_claim_existing.json():\n                            # Race: accept only if the winner is the same authenticated profile.\n                            _r_owner_recheck = await client.get(\n                                f"{SUPABASE_URL}/rest/v1/entreprises",\n                                params={"id": f"eq.{entreprise_id}", "select": "dirigeant_id"},\n                                headers={"apikey": SUPABASE_SERVICE_KEY,\n                                         "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}\n                            )\n                            _owner_recheck_rows = _r_owner_recheck.json() if _r_owner_recheck.status_code == 200 else []\n                            _owner_recheck = _owner_recheck_rows[0].get("dirigeant_id") if len(_owner_recheck_rows) == 1 else None\n                            if _owner_recheck != _existing_uid:\n                                await _fail(client, "existing_industrial_owner_race")\n                                return JSONResponse(status_code=503, content={"erreur": "ownership_conflict"})\n                    elif not _existing_owner and not _existing_uid:\n                        _r_pio_existing = await client.post(\n                            f"{SUPABASE_URL}/rest/v1/pending_industrial_ownership",\n                            params={"on_conflict": "email,entreprise_id"},\n                            headers={"apikey": SUPABASE_SERVICE_KEY,\n                                     "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",\n                                     "Content-Type": "application/json",\n                                     "Prefer": "resolution=merge-duplicates,return=representation"},\n                            json={"email": email, "entreprise_id": entreprise_id,\n                                  "stripe_subscription_id": sub_id or None,\n                                  "stripe_customer_id": cust_id or None,\n                                  "status": "pending",\n                                  "metadata": {"nom": nom_entreprise or email.split("@")[0],\n                                               "forfait": "industrial", "existing_company": True}}\n                        )\n                        if _r_pio_existing.status_code not in (200, 201) or not _r_pio_existing.json():\n                            await _fail(client, f"pending_existing_ownership_failed:{_r_pio_existing.status_code}")\n                            return JSONResponse(status_code=503, content={"erreur": "pending_ownership_failed"})\n\n                if not entreprise_id:\n'''
src = replace_once(src, marker, insert, "checkout existing company ownership")

# 9) subscription.deleted: status is authoritative; never invent ends_at=now.
sd_start = src.index('elif event_type == "customer.subscription.deleted":')
sd_end = src.index('elif event_type in ("invoice.paid", "invoice.payment_succeeded"):', sd_start)
sd = src[sd_start:sd_end]
sd = replace_once(
    sd,
    '''        async with httpx.AsyncClient(timeout=10.0) as client:\n\n            rows = []\n''',
    '''        # L'evenement deleted est autoritaire pour le statut. La date de fin n'est\n        # remplacee que si Stripe fournit une periode exploitable.\n        _sd_status, _sd_starts, _sd_ends = _project_stripe_sub_data(\n            data_obj, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)\n\n        async with httpx.AsyncClient(timeout=10.0) as client:\n\n            rows = []\n''',
    "sub.deleted projection",
)
sd = replace_once(
    sd,
    '''                    json={"status": "canceled", "ends_at": _dt_m.datetime.utcnow().isoformat(),\n                           "metadata": {"event_id": event_id}}\n''',
    '''                    json={**{"status": "canceled",\n                              "metadata": {"event_id": event_id, "stripe_status": data_obj.get("status", "canceled")}},\n                          **({"ends_at": _sd_ends} if _sd_ends else {})}\n''',
    "sub.deleted no invented end",
)
src = src[:sd_start] + sd + src[sd_end:]

SERVER.write_text(src, encoding="utf-8")

# 10) Regression tests for the newly closed P0/P1 cases.
test_path = ROOT / "tests" / "test_charlie21.py"
test_path.write_text(r'''"""Charlie 21 — final entitlement/Stripe/Industrial closure regressions."""
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
    path = ROOT / "supabase" / "migrations" / "20260914010000_phase_k_pending_industrial_subscription_unique.sql"
    assert path.exists()
    sql = path.read_text(encoding="utf-8")
    assert "unique index" in sql.lower()
    assert "stripe_subscription_id" in sql
''', encoding="utf-8")

# 11) Repo migration matching the live DB hardening.
migration = ROOT / "supabase" / "migrations" / "20260914010000_phase_k_pending_industrial_subscription_unique.sql"
migration.write_text('''-- P0/P1 hardening: one Industrial ownership claim per Stripe subscription.\nCREATE UNIQUE INDEX IF NOT EXISTS uq_pending_industrial_ownership_stripe_subscription\nON public.pending_industrial_ownership (stripe_subscription_id)\nWHERE stripe_subscription_id IS NOT NULL;\n''', encoding="utf-8")

print("Charlie P0 closure patch applied")
