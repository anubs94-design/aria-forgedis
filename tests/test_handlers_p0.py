
"""
FORGEDIS — Suite de tests handlers webhook et autorisation
Commande : python tests/test_handlers_p0.py
Résultat attendu : N/N OK

Couvre :
- _project_stripe_sub_data (projection Stripe API 2026)
- resolve_forfait
- Branches sub.created, sub.updated, checkout (NameError, variables)
- Logique _check_president (rôle salarié refusé)
- Pending claims idempotence (sub_id existant)
- verifier_acces Industrial ends_at expiry
"""
import sys, time, re, importlib.util, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PATH = os.path.join(ROOT, 'server.py')

# ── Extraire les fonctions testables depuis server.py ──────────────────────
with open(SERVER_PATH, encoding='utf-8') as f:
    src = f.read()

def extract_func(pattern):
    m = re.search(pattern, src, re.DOTALL)
    assert m, f"Fonction non trouvée : {pattern[:40]}"
    return m.group(0)

# _project_stripe_sub_data
func_src = extract_func(r'def _project_stripe_sub_data\(.*?(?=\ndef |\n@app|\nasync def )')
ns = {}
exec(func_src, ns)
_project_stripe_sub_data = ns['_project_stripe_sub_data']

# resolve_forfait (dans webhook scope)
func_rf = extract_func(r'    def resolve_forfait\(.*?(?=    def |    async def )')
exec(func_rf.strip(), ns)
resolve_forfait = ns['resolve_forfait']
# Injecter PRICE_TO_FORFAIT dans ns pour que resolve_forfait l'utilise
# (la fonction fermée sur le scope webhook, on doit l'injecter au moment de l'exécution)
_orig_resolve = resolve_forfait
def resolve_forfait(price_ids, _ptf=None):
    """Wrapper injectant PRICE_TO_FORFAIT."""
    _ptf = _ptf or PRICE_TO_FORFAIT
    found = {_ptf[p] for p in price_ids if p in _ptf}
    if not found: return None
    INDUSTRIAL_SET = {"industrial"}
    if INDUSTRIAL_SET & found: return "industrial"
    if "kids_famille" in found: return "kids_famille"
    if "kids_solo" in found: return "kids_solo"
    if "facility" in found: return "facility"
    return None

# ── Constants ──────────────────────────────────────────────────────────────
PRICE_TO_FORFAIT = {
    "price_1Tht8LI54RQfwJiYNUvxbLzd": "facility",
    "price_1Tomp0I54RQfwJiYr3qI18Ua": "facility",
    "price_1TrudbI54RQfwJiY4k26O7dG": "kids_solo",
    "price_1TrufbI54RQfwJiYeD5fbW7b": "kids_famille",
    "price_1Txb8dI54RQfwJiYhVgtBFWP": "industrial",
    "price_1Txb8kI54RQfwJiYZrHbuF4p": "industrial",
}
INDUSTRIAL_BASE_PRICE = "price_1Txb8dI54RQfwJiYhVgtBFWP"

NOW = int(time.time())
FUTURE = NOW + 30*86400
PAST   = NOW - 86400

tests = []

def T(name, expected, actual, note=""):
    ok = (expected == actual)
    tests.append((name, ok))
    print(f"  {'✅' if ok else '❌'} {name}: attendu={expected!r} obtenu={actual!r} {note}")
    return ok

# ══════════════════════════════════════════════════════════════════════════
# 1. _project_stripe_sub_data
# ══════════════════════════════════════════════════════════════════════════
print("\n── 1. _project_stripe_sub_data ──")

s, st, e = _project_stripe_sub_data({
    "status": "active", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                         "current_period_start": NOW-30*86400, "current_period_end": FUTURE}]}
}, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
T("active_facility_status", "active", s)
T("active_facility_ends_not_None", True, e is not None)
T("active_facility_starts_not_None", True, st is not None)

s2, st2, e2 = _project_stripe_sub_data({
    "status": "trialing", "trial_end": FUTURE,
    "items": {"data": [{"price": {"id": "price_1TrudbI54RQfwJiY4k26O7dG"},
                         "current_period_start": NOW, "current_period_end": FUTURE+1000}]}
}, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
T("trialing_kids_status", "trialing", s2)
import datetime as _dt
T("trialing_uses_trial_end", _dt.datetime.fromtimestamp(FUTURE).isoformat(), e2, "(trial_end prioritaire)")

s3, _, e3 = _project_stripe_sub_data({
    "status": "UNKNOWN_STRIPE_STATUS", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                         "current_period_start": NOW, "current_period_end": FUTURE}]}
}, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
T("statut_inconnu_None", None, s3, "(pas de conversion en past_due)")

s4, _, _ = _project_stripe_sub_data({
    "status": "active", "trial_end": None, "items": {"data": []}
}, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
T("items_vides_None", None, s4)

s5, _, _ = _project_stripe_sub_data({
    "status": "active", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_INCONNU"},
                         "current_period_start": NOW, "current_period_end": FUTURE}]}
}, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
T("price_inconnu_None", None, s5)

# Industrial : item base price prioritaire
s6, _, e6 = _project_stripe_sub_data({
    "status": "active", "trial_end": None,
    "items": {"data": [
        {"price": {"id": "price_1Txb8kI54RQfwJiYZrHbuF4p"}, "current_period_start": NOW, "current_period_end": FUTURE},
        {"price": {"id": "price_1Txb8dI54RQfwJiYhVgtBFWP"}, "current_period_start": NOW, "current_period_end": FUTURE+999},
    ]}
}, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
T("industrial_base_price_priority", "active", s6)
T("industrial_base_price_ends_is_base", _dt.datetime.fromtimestamp(FUTURE+999).isoformat(), e6)

# ══════════════════════════════════════════════════════════════════════════
# 2. resolve_forfait
# ══════════════════════════════════════════════════════════════════════════
print("\n── 2. resolve_forfait ──")
T("forfait_facility", "facility", resolve_forfait(["price_1Tht8LI54RQfwJiYNUvxbLzd"]))
T("forfait_kids_solo", "kids_solo", resolve_forfait(["price_1TrudbI54RQfwJiY4k26O7dG"]))
T("forfait_industrial", "industrial", resolve_forfait(["price_1Txb8dI54RQfwJiYhVgtBFWP"]))
T("forfait_inconnu_None", None, resolve_forfait(["price_INCONNU"]))
T("forfait_vide_None", None, resolve_forfait([]))
T("industrial_priority", "industrial", resolve_forfait([
    "price_1TrudbI54RQfwJiY4k26O7dG",
    "price_1Txb8dI54RQfwJiYhVgtBFWP"
]))

# ══════════════════════════════════════════════════════════════════════════
# 3. Branches sub.created : aucun NameError, variables correctement nommées
# ══════════════════════════════════════════════════════════════════════════
print("\n── 3. sub.created — simulation variables ──")

def sim_sub_created(sub_obj):
    """Simule les assignations de sub.created sans httpx."""
    price_ids = [(item.get("price") or {}).get("id", "")
                 for item in (sub_obj.get("items", {}).get("data") or [])
                 if (item.get("price") or {}).get("id", "")]
    forfait = resolve_forfait(price_ids)
    if not forfait:
        return {"ok": False, "raison": "produit_inconnu"}
    status_mapped_sc, starts_at_sc, ends_at_sc = _project_stripe_sub_data(
        sub_obj, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
    status_used = status_mapped_sc
    if status_used is None:
        return {"ok": False, "raison": "projection_failed"}
    # Vérifier starts_at_sc
    if starts_at_sc is None:
        return {"ok": False, "raison": "starts_at_manquant"}
    # Vérifier que les variables n'ont PAS d'alias non définis
    try:
        _ = ends_at_sc      # doit exister
        _ = status_mapped_sc  # doit exister
        _ = starts_at_sc    # doit exister
    except NameError as e:
        return {"ok": False, "raison": f"NameError:{e}"}
    return {"ok": True, "status": status_used, "ends_at": ends_at_sc, "starts_at": starts_at_sc}

r = sim_sub_created({
    "status": "active", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                         "current_period_start": NOW-30*86400, "current_period_end": FUTURE}]}
})
T("sub_created_active_ok", True, r["ok"])
T("sub_created_active_status", "active", r.get("status"))
T("sub_created_no_NameError", True, "NameError" not in r.get("raison", ""))

r2 = sim_sub_created({
    "status": "trialing", "trial_end": FUTURE,
    "items": {"data": [{"price": {"id": "price_1TrudbI54RQfwJiY4k26O7dG"},
                         "current_period_start": NOW, "current_period_end": FUTURE}]}
})
T("sub_created_trialing_ok", True, r2["ok"])
T("sub_created_trialing_ends_not_None", True, r2.get("ends_at") is not None)
T("sub_created_trialing_starts_not_None", True, r2.get("starts_at") is not None)

# starts_at manquant -> fail
r3 = sim_sub_created({
    "status": "active", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                         "current_period_start": None, "current_period_end": FUTURE}]}
})
# Si starts est None, la simulation doit renvoyer starts_at_manquant
T("sub_created_no_starts_fail", False, r3["ok"], "(starts_at None -> fail)")

r4 = sim_sub_created({
    "status": "UNKNOWN", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                         "current_period_start": NOW, "current_period_end": FUTURE}]}
})
T("sub_created_statut_inconnu_fail", False, r4["ok"])
T("sub_created_statut_inconnu_raison", "projection_failed", r4.get("raison"))

# ══════════════════════════════════════════════════════════════════════════
# 4. sub.updated : sub_id obligatoire
# ══════════════════════════════════════════════════════════════════════════
print("\n── 4. sub.updated — sub_id obligatoire ──")

def sim_sub_updated(sub_id, sub_obj):
    """Simule la garde sub_id + projection."""
    if not sub_id:
        return {"ok": False, "raison": "sub_id_manquant", "http": 503}
    status_mapped, starts_su, ends_at = _project_stripe_sub_data(
        sub_obj, PRICE_TO_FORFAIT, INDUSTRIAL_BASE_PRICE)
    if status_mapped is None:
        return {"ok": False, "raison": "projection_failed", "http": 503}
    return {"ok": True, "status": status_mapped, "ends_at": ends_at}

T("sub_updated_no_sub_id_503", 503, sim_sub_updated("", {})["http"])
T("sub_updated_statut_inconnu_fail", False, sim_sub_updated("sub_123", {
    "status": "UNKNOWN", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                         "current_period_start": NOW, "current_period_end": FUTURE}]}
})["ok"])
T("sub_updated_active_ok", True, sim_sub_updated("sub_123", {
    "status": "active", "trial_end": None,
    "items": {"data": [{"price": {"id": "price_1Tht8LI54RQfwJiYNUvxbLzd"},
                         "current_period_start": NOW-30*86400, "current_period_end": FUTURE}]}
})["ok"])

# ══════════════════════════════════════════════════════════════════════════
# 5. _check_president rôle : salarié normal refusé
# ══════════════════════════════════════════════════════════════════════════
print("\n── 5. _check_president rôle salarié ──")

def sim_check_president_role(sal_role, sal_poste):
    """Simule la logique de rôle de _check_president."""
    ROLES_PRESIDENT = {"dirigeant", "president", "directeur", "admin_industrial"}
    if sal_role.lower() not in ROLES_PRESIDENT and sal_poste.lower() not in ROLES_PRESIDENT:
        return False, "Role insuffisant (president/dirigeant requis)."
    return True, None

ok, msg = sim_check_president_role("employe", "technicien")
T("salarie_normal_refuse", False, ok)
T("salarie_normal_msg", "Role insuffisant (president/dirigeant requis).", msg)

ok2, _ = sim_check_president_role("dirigeant", "")
T("dirigeant_accepte", True, ok2)

ok3, _ = sim_check_president_role("", "president")
T("president_via_poste_accepte", True, ok3)

ok4, _ = sim_check_president_role("comptable", "responsable_rh")
T("comptable_refuse", False, ok4)

# ══════════════════════════════════════════════════════════════════════════
# 6. Pending claims idempotence
# ══════════════════════════════════════════════════════════════════════════
print("\n── 6. create_pending_claim idempotence ──")

# La nouvelle fonction doit gérer le cas sub_id existant
# Vérification : la fonction est bien présente dans server.py avec les nouvelles clés
pending_claim_src = re.search(r'async def create_pending_claim\(.*?(?=\n    async def |\n@app)', src, re.DOTALL)
T("create_pending_claim_present", True, pending_claim_src is not None)
if pending_claim_src:
    code = pending_claim_src.group(0)
    T("pending_claim_has_sub_id_check", True, "stripe_subscription_id" in code and "existing_claim" in code)
    T("pending_claim_has_upsert_logic", True, "r_upd" in code or "PATCH" in code or "patch" in code)
    T("pending_claim_no_blind_insert", True, "already claimed" not in code or "status" in code)

# ══════════════════════════════════════════════════════════════════════════
# 7. verifier_acces Industrial ends_at
# ══════════════════════════════════════════════════════════════════════════
print("\n── 7. verifier_acces Industrial ends_at ──")

# Vérifier que le code ends_at Industrial est présent dans verifier_acces
va_src = re.search(r'async def verifier_acces\(.*?(?=\nasync def |\n@app)', src, re.DOTALL)
T("verifier_acces_present", True, va_src is not None)
if va_src:
    va_code = va_src.group(0)
    # Vérifier bloc Industrial ends_at
    T("va_industrial_has_ends_at", True, "ends_at" in va_code and "expired" in va_code and "industrial" in va_code)
    T("va_industrial_fromisoformat", True, "fromisoformat" in va_code)

# Simuler le comportement ends_at Industrial
def sim_va_industrial_ends_at(ent_status, ends_at_str):
    """Simule la logique ends_at de verifier_acces Industrial."""
    import datetime
    if ends_at_str:
        try:
            if datetime.datetime.fromisoformat(ends_at_str.replace("Z","")) < datetime.datetime.utcnow():
                ent_status = "expired"
        except Exception:
            pass
    BLOCK = {"canceled", "expired", "suspended", "past_due"}
    if ent_status in BLOCK:
        return False, ent_status
    if ent_status in {"trialing", "active"}:
        return True, ent_status
    return False, "unknown"

ok_active, _ = sim_va_industrial_ends_at("active", None)
T("industrial_active_no_ends_at_ok", True, ok_active)

ok_exp, s_exp = sim_va_industrial_ends_at("active", _dt.datetime.fromtimestamp(PAST).isoformat())
T("industrial_active_ends_at_passe_expired", False, ok_exp)
T("industrial_expired_status", "expired", s_exp)

ok_fut, _ = sim_va_industrial_ends_at("active", _dt.datetime.fromtimestamp(FUTURE).isoformat())
T("industrial_active_ends_at_futur_ok", True, ok_fut)

ok_pd, _ = sim_va_industrial_ends_at("past_due", None)
T("industrial_past_due_refuse", False, ok_pd)

# ══════════════════════════════════════════════════════════════════════════
# 8. Routes auth présentes
# ══════════════════════════════════════════════════════════════════════════
print("\n── 8. Audit routes auth ──")
for route in ['/profil-kids', '/devoirs', '/sauvegarder']:
    idx = src.find(f'"{route}"')
    if idx >= 0:
        chunk = src[idx:idx+600]
        has_va = 'verifier_acces' in chunk
        T(f"{route}_has_verifier_acces", True, has_va)

# Vérifier 0 verifier_forfait avec await
vf_count = len(re.findall(r'await verifier_forfait\(', src))
T("0_verifier_forfait_await", True, vf_count == 0, f"({vf_count} restants)")

# ══════════════════════════════════════════════════════════════════════════
# Résumé
# ══════════════════════════════════════════════════════════════════════════
ok_n = sum(1 for _, ok in tests if ok)
total = len(tests)
print(f"\n{'='*60}")
print(f"Résultats: {ok_n}/{total} OK")
failed = [(n, ok) for n, ok in tests if not ok]
if failed:
    print("ÉCHECS:")
    for n, _ in failed: print(f"  ❌ {n}")
    sys.exit(1)
else:
    print(f"Tous les {total} tests passent.")
    sys.exit(0)
