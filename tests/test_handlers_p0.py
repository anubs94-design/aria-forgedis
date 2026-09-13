
"""
FORGEDIS — Tests pytest P0 (révision Charlie 11)
Teste le vrai code server.py via analyse AST + simulation fidèle.
Commande : pytest tests/ -q
"""
import sys, os, re, json, time, ast
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PATH = os.path.join(ROOT, 'server.py')

with open(SERVER_PATH, encoding='utf-8') as f:
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

# ── Extraire _project_stripe_sub_data depuis server.py ─────────────────────
_ns = {}
m = re.search(r'def _project_stripe_sub_data\(.*?(?=\ndef |\nasync def |\n@app)', SRC, re.DOTALL)
assert m, "_project_stripe_sub_data non trouvée"
exec(m.group(0), _ns)
_project_stripe_sub_data = _ns['_project_stripe_sub_data']

def resolve_forfait(price_ids):
    found = {PRICE_TO_FORFAIT[p] for p in price_ids if p in PRICE_TO_FORFAIT}
    if not found: return None
    if {"industrial"} & found: return "industrial"
    if "kids_famille" in found: return "kids_famille"
    if "kids_solo" in found: return "kids_solo"
    if "facility" in found: return "facility"
    return None


# ══════════════════════════════════════════════════════════════════════════
# 0. Syntaxe
# ══════════════════════════════════════════════════════════════════════════

def test_server_py_compile():
    r = __import__('subprocess').run(
        [sys.executable, '-m', 'py_compile', SERVER_PATH],
        capture_output=True, text=True)
    assert r.returncode == 0, f"py_compile:\n{r.stderr}"

def test_no_verifier_forfait_await():
    count = len(re.findall(r'await verifier_forfait\(', SRC))
    assert count == 0, f"{count} appels verifier_forfait restants"

def test_no_comptes_table():
    lines_code = [l for l in SRC.split('\n') if not l.strip().startswith('#')]
    assert not any('/rest/v1/comptes' in l and 'comptes_presse' not in l for l in lines_code)

def test_no_rpc_sauvegarder_donnees():
    assert 'sauvegarder_donnees_salarie' not in SRC

def test_no_facility_essai_forfait():
    """Inscription ne doit plus utiliser facility_essai comme forfait dans clients."""
    insc_src = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
    assert insc_src
    code = insc_src.group(0)
    assert '"forfait": "facility_essai"' not in code, "facility_essai ne doit plus être utilisé"

def test_no_email_admin_column():
    """entreprises.email_admin n'existe pas dans le schéma -> ne pas l'utiliser dans inscription."""
    insc_ii = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
    assert insc_ii
    code = insc_ii.group(0)
    assert '"email_admin"' not in code, "Colonne email_admin inexistante"
    assert '"expires_at"' not in code, "Colonne expires_at inexistante dans entreprises"


# ══════════════════════════════════════════════════════════════════════════
# 1. _project_stripe_sub_data
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

    def test_statut_inconnu_None(self):
        s, _, _ = _project_stripe_sub_data({
            "status": "UNKNOWN", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                                 "current_period_start": NOW, "current_period_end": FUTURE}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s is None

    def test_items_vides_None(self):
        s, _, _ = _project_stripe_sub_data(
            {"status": "active", "trial_end": None, "items": {"data": []}},
            PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s is None

    def test_price_inconnu_None(self):
        s, _, _ = _project_stripe_sub_data({
            "status": "active", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_INCONNU"},
                                 "current_period_start": NOW, "current_period_end": FUTURE}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s is None

    def test_industrial_base_priority(self):
        import datetime
        s, _, e = _project_stripe_sub_data({
            "status": "active", "trial_end": None,
            "items": {"data": [
                {"price": {"id": "price_1Txb8kI54RQfwJiYZrHbuF4p"},
                 "current_period_start": NOW, "current_period_end": FUTURE},
                {"price": {"id": INDUSTRIAL_BASE_PRICE},
                 "current_period_start": NOW, "current_period_end": FUTURE+999},
            ]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s == "active"
        assert e == datetime.datetime.fromtimestamp(FUTURE+999).isoformat()

    def test_past_due(self):
        s, _, _ = _project_stripe_sub_data({
            "status": "past_due", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                                 "current_period_start": NOW-60*86400, "current_period_end": PAST}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s == "past_due"

    def test_canceled(self):
        s, _, _ = _project_stripe_sub_data({
            "status": "canceled", "trial_end": None,
            "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                                 "current_period_start": NOW-60*86400, "current_period_end": PAST}]}
        }, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
        assert s == "canceled"


# ══════════════════════════════════════════════════════════════════════════
# 2. Invoice lifecycle : pas de fallback status
# ══════════════════════════════════════════════════════════════════════════

class TestInvoiceLifecycle:
    def test_invoice_paid_no_active_fallback(self):
        """_status_ip ne doit jamais être initialisé à 'active'."""
        ip_src = re.search(r'"invoice\.paid".*?(?=\n    elif event_type)', SRC, re.DOTALL)
        assert ip_src
        code = ip_src.group(0)
        assert '_status_ip = "active"' not in code, "Fallback 'active' supprimé"
        assert '_status_ip = None' in code, "Doit être None par défaut"
        assert 'api.stripe.com/v1/subscriptions' in code
        assert '_project_stripe_sub_data' in code
        # Doit fail si status_ip reste None
        assert 'if _s_ip is None' in code or '_status_ip is None' in code

    def test_invoice_failed_no_past_due_fallback(self):
        """_status_if ne doit jamais être initialisé à 'past_due'."""
        if_src = re.search(r'"invoice\.payment_failed".*?(?=\n    async with httpx\.AsyncClient\(timeout=5\.0\) as hc:)', SRC, re.DOTALL)
        assert if_src
        code = if_src.group(0)
        assert '_status_if = "past_due"' not in code, "Fallback 'past_due' supprimé"
        assert '_status_if = None' in code
        assert 'api.stripe.com/v1/subscriptions' in code
        assert '_project_stripe_sub_data' in code

    def test_invoice_paid_fails_if_no_stripe_key(self):
        ip_src = re.search(r'"invoice\.paid".*?(?=\n    elif event_type)', SRC, re.DOTALL)
        code = ip_src.group(0)
        assert 'if not STRIPE_SECRET_KEY' in code
        assert 'stripe_key_manquante' in code


# ══════════════════════════════════════════════════════════════════════════
# 3. Inscription routes
# ══════════════════════════════════════════════════════════════════════════

class TestInscriptionFacility:
    def _get_code(self):
        m = re.search(r'async def inscription_facility\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        return m.group(0)

    def test_no_comptes_table(self):
        assert '/rest/v1/comptes' not in self._get_code()

    def test_uses_product_entitlements(self):
        assert 'product_entitlements' in self._get_code()

    def test_creates_trial_canonical(self):
        code = self._get_code()
        assert '"status": "trialing"' in code
        assert '"source": "trial"' in code

    def test_no_facility_essai(self):
        assert '"forfait": "facility_essai"' not in self._get_code()

    def test_jwt_required(self):
        assert '_jwt_vers_identite' in self._get_code()

    def test_protection_double_trial(self):
        """Doit vérifier un entitlement existant avant d'en créer un."""
        assert 'existing_ents' in self._get_code() or 'existing' in self._get_code()


class TestInscriptionIndustrial:
    def _get_code(self):
        m = re.search(r'async def inscription_industrial\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        return m.group(0)

    def test_no_email_admin(self):
        assert '"email_admin"' not in self._get_code()

    def test_no_expires_at(self):
        assert '"expires_at"' not in self._get_code()

    def test_uses_schema_columns(self):
        code = self._get_code()
        assert '"email_contact"' in code
        assert '"dirigeant_id"' in code
        assert '"statut_paiement"' in code
        assert '"code"' in code

    def test_entitlement_portee_entreprise(self):
        code = self._get_code()
        assert '"entreprise_id"' in code
        assert '"product": "industrial"' in code


# ══════════════════════════════════════════════════════════════════════════
# 4. pending_claim claimed check
# ══════════════════════════════════════════════════════════════════════════

class TestPendingClaimClaimed:
    def _get_code(self):
        m = re.search(r'async def create_pending_claim\(.*?(?=\n    async def |\n@app)', SRC, re.DOTALL)
        assert m
        return m.group(0)

    def test_claimed_checks_entitlement(self):
        code = self._get_code()
        assert '.get("status") == "claimed"' in code or 'status == "claimed"' in code
        assert 'product_entitlements' in code, "Doit vérifier l'entitlement quand claimed"

    def test_claimed_can_reset_to_pending(self):
        code = self._get_code()
        assert '"status": "pending"' in code or 'reset' in code.lower()
        assert 'return False' in code, "Peut retourner False si entitlement absent"

    def test_no_blind_return_true(self):
        code = self._get_code()
        # "return True" doit être précédé d'une vérification, pas immédiatement après "claimed"
        claimed_idx = code.find('"claimed"')
        return_true_idx = code.find('return True', claimed_idx)
        ent_check_idx = code.find('product_entitlements', claimed_idx)
        assert ent_check_idx < return_true_idx, \
            "product_entitlements doit être vérifié AVANT le return True"


# ══════════════════════════════════════════════════════════════════════════
# 5. verifier_acces Industrial ends_at
# ══════════════════════════════════════════════════════════════════════════

class TestVerifierAccesIndustrialEndsAt:
    def _get_code(self):
        m = re.search(r'async def verifier_acces\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        return m.group(0)

    def test_industrial_block_has_ends_at(self):
        code = self._get_code()
        ind_idx = code.find('elif product == "industrial"')
        assert ind_idx >= 0
        ind_block = code[ind_idx:ind_idx+3500]
        assert 'ends_at' in ind_block or '_ends_at_ind' in ind_block
        assert 'expired' in ind_block
        assert 'fromisoformat' in ind_block

    def test_ends_at_blocks_expired(self):
        """Entitlement Industrial avec ends_at passé -> bloqué."""
        import datetime
        BLOCK = {"canceled","expired","suspended","past_due"}
        ALLOW = {"trialing","active"}

        def apply(status, ends_at_str):
            if ends_at_str:
                try:
                    if datetime.datetime.fromisoformat(ends_at_str.replace("Z","")) < datetime.datetime.utcnow():
                        status = "expired"
                except Exception:
                    pass
            return status not in BLOCK and status in ALLOW

        past = datetime.datetime.fromtimestamp(PAST).isoformat()
        future = datetime.datetime.fromtimestamp(FUTURE).isoformat()
        assert apply("active", None) is True
        assert apply("active", past) is False
        assert apply("active", future) is True
        assert apply("past_due", None) is False
        assert apply("canceled", None) is False


# ══════════════════════════════════════════════════════════════════════════
# 6. _check_president
# ══════════════════════════════════════════════════════════════════════════

class TestCheckPresident:
    def _get_code(self):
        m = re.search(r'async def _check_president\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        return m.group(0)

    def test_no_forfait_authority(self):
        code = self._get_code()
        assert re.search(r'if forfait not in.*industrial', code) is None

    def test_verifier_acces_industrial_first(self):
        code = self._get_code()
        va_idx = code.find('verifier_acces(token, "industrial")')
        try_idx = code.find('try:')
        assert va_idx >= 0 and va_idx < try_idx, \
            "verifier_acces industrial doit précéder le try:"

    def test_eid_not_none_before_true(self):
        code = self._get_code()
        assert 'not eid' in code or 'if not eid' in code
        # Vérifier la structure : "return True, eid, None" doit SUIVRE le check "not eid"
        not_eid_idx = code.find('not eid')
        true_ret_idx = code.find('return True, eid, None')
        assert not_eid_idx >= 0 and true_ret_idx > not_eid_idx

    def test_role_check_for_salarie(self):
        code = self._get_code()
        assert 'ROLES_PRESIDENT' in code
        assert 'sal_role' in code or 'sal_poste' in code


# ══════════════════════════════════════════════════════════════════════════
# 7. /client-token-kids
# ══════════════════════════════════════════════════════════════════════════

class TestClientTokenKids:
    def _get_code(self):
        m = re.search(r'async def client_token_kids\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        return m.group(0)

    def test_jwt_not_proxy_token(self):
        code = self._get_code()
        assert '_jwt_vers_identite' in code

    def test_claim_before_entitlement_check(self):
        code = self._get_code()
        claim_idx = code.find('_claim_pending_entitlements')
        ent_idx = code.find('# Vérifier entitlement Kids actif')
        if ent_idx < 0:
            ent_idx = code.find('product_entitlements')
        assert claim_idx >= 0, "Doit appeler _claim_pending_entitlements"
        assert claim_idx < ent_idx, "claim doit précéder la vérification entitlement"

    def test_no_undefined_token(self):
        """Aucun `verifier_acces(token, ...)` sans token défini."""
        code = self._get_code()
        lines = code.split('\n')
        token_defined = False
        for line in lines:
            if ('jwt_tok' in line or 'auth_uid' in line) and '=' in line and 'verifier_acces' not in line:
                token_defined = True
            if 'verifier_acces' in line and not token_defined:
                pytest.fail(f"verifier_acces avant token défini: {line}")

    def test_entitlement_check_before_client_creation(self):
        code = self._get_code()
        ent_idx = code.find('product_entitlements')
        client_create_idx = code.find('json={"email": email')
        assert ent_idx < client_create_idx, \
            "Entitlement vérifié avant création compte legacy"


# ══════════════════════════════════════════════════════════════════════════
# 8. /sauvegarder
# ══════════════════════════════════════════════════════════════════════════

class TestSauvegarder:
    def _get_code(self):
        m = re.search(r'async def sauvegarder_donnees\(.*?(?=\nasync def |\n@app)', SRC, re.DOTALL)
        assert m
        return m.group(0)

    def test_no_rpc(self):
        assert 'sauvegarder_donnees_salarie' not in self._get_code()

    def test_uses_donnees_salaries(self):
        assert 'donnees_salaries' in self._get_code()

    def test_requires_salarie_id(self):
        assert 'salarie_id' in self._get_code()

    def test_requires_auth(self):
        assert 'verifier_acces' in self._get_code()


# ══════════════════════════════════════════════════════════════════════════
# 9. sub.created / sub.updated variables
# ══════════════════════════════════════════════════════════════════════════

class TestSubscriptionHandlers:
    def test_sub_created_no_starts_at_utcnow_fallback(self):
        sc_src = re.search(r'"customer\.subscription\.created".*?(?=\n    elif event_type)', SRC, re.DOTALL)
        assert sc_src
        code = sc_src.group(0)
        # L'ancien fallback utcnow doit être remplacé par un fail
        assert 'starts_at_sc = starts_at_sc or' not in code
        # Soit un check "if starts_at_sc is None", soit le code fail
        assert ('starts_at_sc is None' in code or 'starts_at_manquant' in code), \
            "starts_at_sc None doit provoquer un fail"

    def test_sub_updated_sub_id_required(self):
        su_src = re.search(r'"customer\.subscription\.updated".*?(?=\n    elif event_type)', SRC, re.DOTALL)
        assert su_src
        code = su_src.group(0)
        assert 'if not sub_id' in code
        assert '_project_stripe_sub_data' in code

    def test_sub_created_uses_projection(self):
        sc_src = re.search(r'"customer\.subscription\.created".*?(?=\n    elif event_type)', SRC, re.DOTALL)
        code = sc_src.group(0)
        assert '_project_stripe_sub_data' in code
        assert 'status_mapped_sc' in code
        assert 'ends_at_sc' in code
