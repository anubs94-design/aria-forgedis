
"""
FORGEDIS — Tests runtime P0 (Charlie 12)
Import réel de server.py. Echoue si l'import échoue.
Commande : pytest tests/ -q
"""
import sys, os, re, json, time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import asyncio

# ── Variables d'environnement requises ────────────────────────────────────
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test_service_key")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("GOOGLE_TTS_API_KEY", "test")
os.environ.setdefault("PROXY_TOKEN", "proxy_test")
os.environ.setdefault("CLAUDE_API_KEY", "test_anthropic")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ── Import RÉEL de server — pytest FAIL si l'import échoue ──────────────
import server as srv   # <— si ce crash, tout le module fail

with open(os.path.join(ROOT, 'server.py'), encoding='utf-8') as f:
    SRC = f.read()

NOW = int(time.time())
FUTURE = NOW + 30*86400
PAST   = NOW - 86400

PRICE_TO_FORFAIT = {
    "price_1Tht8LI54RQfwJiYNUvxbLzd": "facility",
    "price_1Tomp0I54RQfwJiYr3qI18Ua": "facility",
    "price_1TrudbI54RQfwJiY4k26O7dG": "kids_solo",
    "price_1TrufbI54RQfwJiYeD5fbW7b": "kids_famille",
    "price_1Txb8dI54RQfwJiYhVgtBFWP": "industrial",
    "price_1Txb8kI54RQfwJiYZrHbuF4p": "industrial",
}
INDUSTRIAL_BASE_PRICE = "price_1Txb8dI54RQfwJiYhVgtBFWP"

# Extraire _project_stripe_sub_data depuis server (vraie fonction, pas une copie)
_project_stripe_sub_data = srv._project_stripe_sub_data

def run(coro):
    return asyncio.run(coro)


# ══════════════════════════════════════════════════════════════════════════
# 0. Import et syntaxe
# ══════════════════════════════════════════════════════════════════════════

def test_server_import_ok():
    """server.py doit être importable — si ce test échoue, srv est None."""
    assert srv is not None
    assert hasattr(srv, 'app'), "srv.app doit exister"

def test_server_py_compile():
    import subprocess
    r = subprocess.run([sys.executable, '-m', 'py_compile', os.path.join(ROOT, 'server.py')],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"py_compile:\n{r.stderr}"

def test_no_verifier_forfait_await():
    assert len(re.findall(r'await verifier_forfait\(', SRC)) == 0

def test_no_comptes_table():
    lines = [l for l in SRC.split('\n') if not l.strip().startswith('#')]
    assert not any('/rest/v1/comptes' in l and 'comptes_presse' not in l for l in lines)

def test_no_rpc_sauvegarder():
    assert 'sauvegarder_donnees_salarie' not in SRC

def test_no_facility_essai():
    insc = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
    assert insc
    assert '"forfait": "facility_essai"' not in insc.group(0)

def test_no_email_admin():
    insc = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
    assert insc
    assert '"email_admin"' not in insc.group(0)


# ══════════════════════════════════════════════════════════════════════════
# 1. _project_stripe_sub_data (vraie fonction depuis srv)
# ══════════════════════════════════════════════════════════════════════════

class TestProjectStripeSubData:
    def test_active_facility(self):
        s, st, e = _project_stripe_sub_data({
            "status": "active", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                                 "current_period_start": NOW-30*86400,
                                 "current_period_end": FUTURE}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s == "active"
        assert e is not None and st is not None

    def test_trialing_uses_trial_end(self):
        import datetime
        s, _, e = _project_stripe_sub_data({
            "status": "trialing", "trial_end": FUTURE,
            "items": {"data": [{"price": {"id": "price_1TrudbI54RQfwJiY4k26O7dG"},
                                 "current_period_start": NOW, "current_period_end": FUTURE+1000}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s == "trialing"
        assert e == datetime.datetime.fromtimestamp(FUTURE).isoformat()

    def test_unknown_status_None(self):
        s, _, _ = _project_stripe_sub_data({
            "status": "UNKNOWN", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                                 "current_period_start": NOW, "current_period_end": FUTURE}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s is None, "Statut inconnu ne doit pas être propagé"

    def test_empty_items_None(self):
        s, _, _ = _project_stripe_sub_data(
            {"status": "active", "trial_end": None, "items": {"data": []}},
            PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s is None

    def test_unknown_price_None(self):
        s, _, _ = _project_stripe_sub_data({
            "status": "active", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_INCONNU"},
                                 "current_period_start": NOW, "current_period_end": FUTURE}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s is None

    def test_past_due(self):
        s, _, _ = _project_stripe_sub_data({
            "status": "past_due", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                                 "current_period_start": NOW-60*86400, "current_period_end": PAST}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s == "past_due"


# ══════════════════════════════════════════════════════════════════════════
# 2. create_pending_claim — tests runtime réels via mocks httpx
# ══════════════════════════════════════════════════════════════════════════

def make_mock_response(status_code, json_data=None):
    """Crée un mock de réponse httpx."""
    m = MagicMock()
    m.status_code = status_code
    m.json = MagicMock(return_value=json_data if json_data is not None else [])
    m.text = json.dumps(json_data or {})
    return m

def make_mock_hc(get_responses=None, patch_responses=None, post_responses=None):
    """Crée un mock httpx.AsyncClient."""
    hc = MagicMock()
    get_q = list(get_responses or [])
    patch_q = list(patch_responses or [])
    post_q = list(post_responses or [])

    async def mock_get(*a, **kw):
        return get_q.pop(0) if get_q else make_mock_response(200, [])
    async def mock_patch(*a, **kw):
        return patch_q.pop(0) if patch_q else make_mock_response(200, {})
    async def mock_post(*a, **kw):
        return post_q.pop(0) if post_q else make_mock_response(201, {})

    hc.get = mock_get
    hc.patch = mock_patch
    hc.post = mock_post
    return hc


class TestCreatePendingClaimRuntime:
    """Appelle la vraie create_pending_claim via l'exécution dans le scope webhook."""

    def _get_func(self):
        """Extraire create_pending_claim depuis le scope du webhook Stripe."""
        # La fonction est définie localement dans stripe_webhook — on doit l'extraire
        # via exec du code source
        m = re.search(
            r'(    async def create_pending_claim\(.*?        except Exception as e:\n.*?return False\n)',
            SRC, re.DOTALL)
        assert m, "create_pending_claim non trouvée"
        func_code = re.sub(r'^    ', '', m.group(1), flags=re.MULTILINE)
        ns = {
            'SUPABASE_URL': os.environ['SUPABASE_URL'],
            'SUPABASE_SERVICE_KEY': os.environ['SUPABASE_SERVICE_KEY'],
        }
        exec(func_code, ns)
        return ns['create_pending_claim']

    def test_no_NameError_pending_status(self):
        """Claim existant avec status='pending' ne doit pas lever NameError (r_upd)."""
        create_pending_claim = self._get_func()

        # Simuler un claim existant avec status='pending'
        existing_claim_resp = make_mock_response(200, [{"id": "claim-uuid-1", "status": "pending"}])
        patch_resp = make_mock_response(204, {})
        hc = make_mock_hc(
            get_responses=[existing_claim_resp],
            patch_responses=[patch_resp]
        )

        result = run(create_pending_claim(
            hc, "test@example.com", "facility", "cus_test", "sub_test_123",
            ["price_1Tht8LI54RQfwJiYNUvxbLzd"], "facility", "facility",
            "trialing", "2026-01-01T00:00:00", "2026-01-15T00:00:00"
        ))
        assert result is True, "PATCH existant pending doit retourner True"

    def test_new_claim_insert(self):
        """Aucun claim existant -> INSERT -> True."""
        create_pending_claim = self._get_func()

        hc = make_mock_hc(
            get_responses=[make_mock_response(200, [])],  # aucun existant
            post_responses=[make_mock_response(201, {})]
        )

        result = run(create_pending_claim(
            hc, "new@example.com", "facility", "cus_new", "sub_new_456",
            ["price_1Tht8LI54RQfwJiYNUvxbLzd"], "facility", "facility",
            "trialing", "2026-01-01T00:00:00", "2026-01-15T00:00:00"
        ))
        assert result is True

    def test_claimed_with_entitlement_returns_True(self):
        """Claim claimed + entitlement présent -> True."""
        create_pending_claim = self._get_func()

        # GET pending_claims -> claimed
        # GET product_entitlements -> entitlement présent
        hc = make_mock_hc(
            get_responses=[
                make_mock_response(200, [{"id": "claim-1", "status": "claimed"}]),
                make_mock_response(200, [{"id": "ent-1", "status": "active", "product": "facility"}]),
            ]
        )

        result = run(create_pending_claim(
            hc, "paid@example.com", "facility", "cus_paid", "sub_paid_789",
            ["price_1Tht8LI54RQfwJiYNUvxbLzd"], "facility", "facility",
            "active", "2026-01-01T00:00:00", "2026-02-01T00:00:00"
        ))
        assert result is True

    def test_claimed_without_entitlement_returns_False(self):
        """Claim claimed + entitlement absent -> reset + False."""
        create_pending_claim = self._get_func()

        hc = make_mock_hc(
            get_responses=[
                make_mock_response(200, [{"id": "claim-2", "status": "claimed"}]),
                make_mock_response(200, []),  # entitlement absent
            ],
            patch_responses=[make_mock_response(204, {})]
        )

        result = run(create_pending_claim(
            hc, "ghost@example.com", "facility", "cus_ghost", "sub_ghost_000",
            ["price_1Tht8LI54RQfwJiYNUvxbLzd"], "facility", "facility",
            "active", "2026-01-01T00:00:00", "2026-02-01T00:00:00"
        ))
        assert result is False, "Entitlement absent après claimed -> False"

    def test_insert_failure_returns_False(self):
        """INSERT échoue -> False sans exception."""
        create_pending_claim = self._get_func()

        hc = make_mock_hc(
            get_responses=[make_mock_response(200, [])],
            post_responses=[make_mock_response(409, {"error": "conflict"})]
        )

        result = run(create_pending_claim(
            hc, "fail@example.com", "facility", None, "sub_fail",
            [], "facility", "facility", "trialing", None, None
        ))
        assert result is False


# ══════════════════════════════════════════════════════════════════════════
# 3. /sauvegarder : faille cross-tenant
# ══════════════════════════════════════════════════════════════════════════

class TestSauvegarderCrossTenant:
    """Teste que /sauvegarder refuse un salarie_id hors périmètre."""

    def test_tenant_isolation_structure(self):
        """Le code doit vérifier que salarie.entreprise_id == entreprise_autorisee."""
        sauv = re.search(r'async def sauvegarder_donnees\(.*?(?=\nasync def |\n@app)',
                         SRC, re.DOTALL)
        assert sauv
        code = sauv.group(0)
        # Vérifier les 3 conditions de la query de vérification
        assert 'salarie_id' in code
        assert 'entreprise_autorisee' in code or 'entreprise_id' in code
        assert 'actif' in code
        # Vérifier le refus si 0 ligne
        assert '403' in code or 'hors périmètre' in code or 'Salarié non trouvé' in code
        # Vérifier que l'upsert n'arrive QU'APRÈS la vérification
        check_idx = code.find('sal_check')
        upsert_idx = code.find('donnees_salaries')
        assert check_idx < upsert_idx, "Vérification tenant doit précéder l'upsert"

    def test_uses_donnees_salaries(self):
        sauv = re.search(r'async def sauvegarder_donnees\(.*?(?=\nasync def |\n@app)',
                         SRC, re.DOTALL)
        assert 'donnees_salaries' in sauv.group(0)

    def test_requires_salarie_id_uuid(self):
        sauv = re.search(r'async def sauvegarder_donnees\(.*?(?=\nasync def |\n@app)',
                         SRC, re.DOTALL)
        code = sauv.group(0)
        assert 'salarie_id' in code
        assert 'if not salarie_id' in code


# ══════════════════════════════════════════════════════════════════════════
# 4. Invoice lifecycle (code réel)
# ══════════════════════════════════════════════════════════════════════════

class TestInvoiceLifecycle:
    def test_no_active_fallback(self):
        ip = re.search(r'"invoice\.paid".*?(?=\n    elif event_type)', SRC, re.DOTALL)
        assert ip
        code = ip.group(0)
        assert '_status_ip = "active"' not in code
        assert '_status_ip = None' in code
        assert 'if not STRIPE_SECRET_KEY' in code
        assert 'stripe_sub_get_failed' in code

    def test_no_past_due_fallback(self):
        if_src = re.search(
            r'"invoice\.payment_failed".*?(?=\n    async with httpx\.AsyncClient\(timeout=5\.0\) as hc:)',
            SRC, re.DOTALL)
        assert if_src
        code = if_src.group(0)
        assert '_status_if = "past_due"' not in code
        assert '_status_if = None' in code


# ══════════════════════════════════════════════════════════════════════════
# 5. Inscriptions
# ══════════════════════════════════════════════════════════════════════════

class TestInscriptions:
    def test_facility_no_comptes(self):
        m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        assert '/rest/v1/comptes' not in m.group(0)

    def test_facility_trial_canonical(self):
        m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        code = m.group(0)
        assert '"status": "trialing"' in code
        assert '"source": "trial"' in code
        assert '_jwt_vers_identite' in code

    def test_facility_idempotent(self):
        m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        code = m.group(0)
        # Doit avoir : retry si trial_exists
        assert 'trial_exists' in code or 'ensure_legacy_client' in code

    def test_industrial_real_schema(self):
        m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        code = m.group(0)
        assert '"email_admin"' not in code
        assert '"expires_at"' not in code
        assert '"email_contact"' in code
        assert '"dirigeant_id"' in code
        assert '"statut_paiement"' in code

    def test_industrial_entitlement_by_entreprise(self):
        m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        code = m.group(0)
        assert '"entreprise_id"' in code
        assert '"product": "industrial"' in code

    def test_html_facility_no_body_token(self):
        """Le fetch Relay de inscription-facility.html ne doit pas envoyer body.token."""
        path = os.path.join(ROOT, 'inscription-facility.html')
        if not os.path.exists(path):
            pytest.skip("inscription-facility.html non trouvé")
        with open(path, encoding='utf-8') as f:
            html = f.read()
        fetches = list(re.finditer(r'fetch\(RELAY\+ENDPOINT', html))
        assert fetches, "Fetch RELAY non trouvé"
        relay_block = html[fetches[0].start():fetches[0].start()+600]
        assert 'Authorization' in relay_block, "Doit envoyer Authorization: Bearer"
        assert 'jwt:' in relay_block or "'jwt'" in relay_block, "Doit envoyer jwt"
        assert 'token:token' not in relay_block, "Ne doit plus envoyer body.token legacy"

    def test_html_facility_no_catch_onboarding(self):
        """Le .catch() de inscription-facility.html ne doit pas appeler showOnboarding."""
        path = os.path.join(ROOT, 'inscription-facility.html')
        if not os.path.exists(path):
            pytest.skip()
        with open(path, encoding='utf-8') as f:
            html = f.read()
        catch_m = re.search(r'\.catch\(function\(\).*?\}\);', html, re.DOTALL)
        if catch_m:
            catch_block = catch_m.group(0)
            assert 'showOnboarding' not in catch_block, \
                "showOnboarding interdit dans .catch()"

    def test_html_industrial_no_catch_onboarding(self):
        """Le .catch() de inscription-industrial.html ne doit pas appeler showOnboarding."""
        path = os.path.join(ROOT, 'inscription-industrial.html')
        if not os.path.exists(path):
            pytest.skip()
        with open(path, encoding='utf-8') as f:
            html = f.read()
        catch_m = re.search(r'\.catch\(function\(err\).*?\}\);', html, re.DOTALL)
        if catch_m:
            catch_block = catch_m.group(0)
            assert 'showOnboarding' not in catch_block

    def test_html_facility_checks_data_ok(self):
        """Le .then() de inscription-facility.html doit vérifier data.ok."""
        path = os.path.join(ROOT, 'inscription-facility.html')
        if not os.path.exists(path):
            pytest.skip()
        with open(path, encoding='utf-8') as f:
            html = f.read()
        fetches = list(re.finditer(r'fetch\(RELAY\+ENDPOINT', html))
        relay_block = html[fetches[0].start():fetches[0].start()+800]
        assert 'res.d.ok' in relay_block or '!res.ok' in relay_block, \
            "Doit vérifier response.ok ou data.ok"


# ══════════════════════════════════════════════════════════════════════════
# 6. ensure_legacy_client présent
# ══════════════════════════════════════════════════════════════════════════

class TestEnsureLegacyClient:
    def test_function_exists(self):
        assert 'async def ensure_legacy_client(' in SRC

    def test_no_double_insert(self):
        m = re.search(r'async def ensure_legacy_client\(.*?(?=\nasync def |\n@app)',
                      SRC, re.DOTALL)
        assert m
        code = m.group(0)
        # Doit vérifier l'existant avant d'insérer
        get_idx = code.find('r_get = await hx.get')
        ins_idx = code.find('r_ins = await hx.post')
        assert get_idx < ins_idx, "GET doit précéder INSERT"


# ══════════════════════════════════════════════════════════════════════════
# 7. _check_president et verifier_acces Industrial
# ══════════════════════════════════════════════════════════════════════════

class TestCheckPresidentRuntime:
    def test_structure_code(self):
        m = re.search(r'async def _check_president\(.*?(?=\nasync def |\n@app)',
                      SRC, re.DOTALL)
        assert m
        code = m.group(0)
        assert 'verifier_acces(token, "industrial")' in code
        assert 'ROLES_PRESIDENT' in code
        assert 'not eid' in code
        assert 'return True, eid, None' in code
        # Pas de fallback forfait
        assert re.search(r'if forfait not in.*industrial', code) is None

class TestVerifierAccesIndustrial:
    def test_ends_at_in_industrial_block(self):
        m = re.search(r'async def verifier_acces\(.*?(?=\nasync def |\n@app)',
                      SRC, re.DOTALL)
        assert m
        code = m.group(0)
        ind_idx = code.find('elif product == "industrial"')
        assert ind_idx >= 0
        ind_block = code[ind_idx:ind_idx+3500]
        assert '_ends_at_ind' in ind_block or 'ends_at' in ind_block
        assert 'expired' in ind_block
        assert 'fromisoformat' in ind_block


# ══════════════════════════════════════════════════════════════════════════
# 8. Migration canonique
# ══════════════════════════════════════════════════════════════════════════

def test_migration_canonical_timestamp():
    """Le fichier de migration doit avoir le timestamp Supabase live."""
    mig_dir = os.path.join(ROOT, 'supabase', 'migrations')
    if not os.path.exists(mig_dir):
        pytest.skip("Répertoire migrations non trouvé")
    files = os.listdir(mig_dir)
    donnees_files = [f for f in files if 'donnees_salaries' in f]
    assert donnees_files, "Migration donnees_salaries non trouvée"
    # Le timestamp Supabase live est 20260913205308
    assert any('20260913205308' in f for f in donnees_files), \
        f"Timestamp canonique 20260913205308 attendu, trouvé: {donnees_files}"
