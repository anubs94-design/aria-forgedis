from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server.py"
HTML = ROOT / "connexion-industrial.html"
TEST = ROOT / "tests" / "test_charlie20.py"

server = SERVER.read_text(encoding="utf-8-sig")
html = HTML.read_text(encoding="utf-8-sig")

# 1) F821 global helpers used by legacy Industrial routes.
import_anchor = "from datetime import timezone as _tz_utc\n"
if "from datetime import datetime, timedelta\n" not in server:
    if import_anchor not in server:
        raise SystemExit("import anchor not found")
    server = server.replace(
        import_anchor,
        import_anchor + "from datetime import datetime, timedelta\n",
        1,
    )

# 2) verifier_forfait: free tier stays quota-based; every paid Facility access is canonical.
start = server.index("async def verifier_forfait(")
end = server.find("\nasync def ", start + 10)
if end < 0:
    raise SystemExit("verifier_forfait end not found")
vf = server[start:end]
pattern = re.compile(
    r"            # Consulter product_entitlements \(source canonique\).*?"
    r"            mois = client_data\.get\(\"mois_en_cours\", \"\"\)",
    re.DOTALL,
)
replacement = '''            # Les offres payantes sont autorisees uniquement par l'entitlement canonique.\n            # Le forfait gratuit conserve seulement son quota eco historique.\n            if forfait != "gratuit":\n                ok_canon, msg_canon, _ = await verifier_acces(token_recu, "facility")\n                if not ok_canon:\n                    return False, msg_canon or "Abonnement Facility requis.", "inactif"\n\n            mois = client_data.get("mois_en_cours", "")'''
vf, n = pattern.subn(replacement, vf, count=1)
if n != 1:
    raise SystemExit(f"verifier_forfait canonical patch count={n}")
if "ent_status" in vf:
    raise SystemExit("stale ent_status remains in verifier_forfait")
server = server[:start] + vf + server[end:]

# 3) Stripe checkout must return the purchaser to the owner bootstrap, not the marketing page.
old_success = 'body.get("success_url", "https://forgedis.fr/industrial.html?success=1")'
new_success = 'body.get("success_url", "https://forgedis.fr/connexion-industrial.html?owner=1&success=1")'
if old_success in server:
    server = server.replace(old_success, new_success, 1)
elif new_success not in server:
    raise SystemExit("Industrial checkout success_url anchor not found")

# 4) Server-authoritative owner session. It mints/repairs a real salaries row after ownership.
if '@app.post("/industrial/owner-session")' not in server:
    marker = '@app.post("/inscription-facility")'
    if marker not in server:
        raise SystemExit("inscription-facility marker not found")
    endpoint = r'''

@app.post("/industrial/owner-session")
async def industrial_owner_session(body: dict, request: Request):
    """Bootstrap serveur du dirigeant Industrial apres claim ownership.

    Le JWT Supabase prouve l'identite. L'entreprise, l'entitlement et le role
    sont resolus cote serveur. Le token applicatif Industrial reste un salaries.id.
    """
    auth_header = request.headers.get("Authorization", "")
    jwt_tok = auth_header[7:].strip() if auth_header.startswith("Bearer ") else body.get("jwt", "")
    if not jwt_tok:
        return {"ok": False, "erreur": "JWT Supabase requis."}

    auth_uid, email, err_jwt = await _jwt_vers_identite(jwt_tok, request)
    if err_jwt:
        return {"ok": False, "erreur": err_jwt}
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"ok": False, "erreur": "Service indisponible."}

    requested_eid = str(body.get("entreprise_id") or "").strip()
    headers_ro = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as hx:
            ent_params = {
                "dirigeant_id": f"eq.{auth_uid}",
                "select": "id,nom,statut_paiement",
            }
            if requested_eid:
                ent_params["id"] = f"eq.{requested_eid}"
            r_company = await hx.get(
                f"{SUPABASE_URL}/rest/v1/entreprises",
                params=ent_params,
                headers=headers_ro,
            )
            if r_company.status_code != 200:
                return {"ok": False, "erreur": "Erreur lecture entreprise."}
            companies = r_company.json() if isinstance(r_company.json(), list) else []
            if len(companies) != 1:
                return {"ok": False, "erreur": "Entreprise dirigeant introuvable ou ambigue."}
            company = companies[0]
            entreprise_id = company.get("id")
            statut_paiement = (company.get("statut_paiement") or "").lower()
            if statut_paiement not in {"essai", "trialing", "actif"}:
                return {"ok": False, "erreur": f"Acces Industrial bloque (statut: {statut_paiement or 'inconnu'})."}

            r_ent = await hx.get(
                f"{SUPABASE_URL}/rest/v1/product_entitlements",
                params={
                    "entreprise_id": f"eq.{entreprise_id}",
                    "product": "eq.industrial",
                    "select": "id,status,source,ends_at",
                },
                headers=headers_ro,
            )
            if r_ent.status_code != 200:
                return {"ok": False, "erreur": "Erreur lecture entitlement Industrial."}
            entitlements = r_ent.json() if isinstance(r_ent.json(), list) else []
            valid_entitlement = None
            for ent in entitlements:
                status = ent.get("status")
                ends_at = ent.get("ends_at")
                if ent.get("source") == "trial":
                    if trial_is_valid(status, ends_at):
                        valid_entitlement = ent
                        break
                elif status in ("trialing", "active") and not is_expired(ends_at):
                    valid_entitlement = ent
                    break
            if not valid_entitlement:
                return {"ok": False, "erreur": "Entitlement Industrial actif requis."}

            r_profile = await hx.get(
                f"{SUPABASE_URL}/rest/v1/profiles",
                params={"id": f"eq.{auth_uid}", "select": "prenom,email"},
                headers=headers_ro,
            )
            profile_rows = r_profile.json() if r_profile.status_code == 200 and isinstance(r_profile.json(), list) else []
            profile = profile_rows[0] if profile_rows else {}
            nom = (profile.get("prenom") or (email.split("@")[0] if email else "Dirigeant") or "Dirigeant").strip()

            r_salary = await hx.get(
                f"{SUPABASE_URL}/rest/v1/salaries",
                params={
                    "entreprise_id": f"eq.{entreprise_id}",
                    "user_id": f"eq.{auth_uid}",
                    "select": "id,nom,poste,role,actif,terrain,entreprise_id,user_id,email_entreprise",
                },
                headers=headers_ro,
            )
            if r_salary.status_code != 200:
                return {"ok": False, "erreur": "Erreur lecture session dirigeant."}
            salary_rows = r_salary.json() if isinstance(r_salary.json(), list) else []
            if len(salary_rows) > 1:
                return {"ok": False, "erreur": "Plusieurs sessions dirigeant detectees. Contactez le support."}

            write_headers = {
                **headers_ro,
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
            salary_payload = {
                "entreprise_id": entreprise_id,
                "user_id": auth_uid,
                "nom": nom,
                "poste": "Dirigeant",
                "role": "dirigeant",
                "niveau": 5,
                "actif": True,
                "terrain": False,
                "email_entreprise": email,
                "email_bureau": email,
            }
            if salary_rows:
                salary_id = salary_rows[0].get("id")
                r_write = await hx.patch(
                    f"{SUPABASE_URL}/rest/v1/salaries",
                    params={"id": f"eq.{salary_id}", "entreprise_id": f"eq.{entreprise_id}", "user_id": f"eq.{auth_uid}"},
                    headers=write_headers,
                    json=salary_payload,
                )
            else:
                r_write = await hx.post(
                    f"{SUPABASE_URL}/rest/v1/salaries",
                    headers=write_headers,
                    json=salary_payload,
                )
            if r_write.status_code not in (200, 201) or not r_write.json():
                return {"ok": False, "erreur": f"Creation session dirigeant impossible ({r_write.status_code})."}
            salary = r_write.json()[0]

            legacy = await ensure_legacy_client(hx, email, "industrial")
            session = {
                "salarie_id": salary.get("id"),
                "entreprise_id": entreprise_id,
                "role": "dirigeant",
                "poste": "dirigeant",
                "nom": salary.get("nom") or nom,
                "email": email,
                "terrain": False,
            }
            if not session["salarie_id"]:
                return {"ok": False, "erreur": "Session dirigeant incomplete."}
            return {
                "ok": True,
                "session": session,
                "client_token": legacy.get("token"),
                "entitlement_id": valid_entitlement.get("id"),
            }
    except Exception as exc:
        print(f"[industrial-owner-session] {exc}")
        return {"ok": False, "erreur": "Erreur serveur."}

'''
    server = server.replace(marker, endpoint + marker, 1)

# 5) Frontend consumes the server-authoritative Industrial session.
finish_pattern = re.compile(
    r"async function _finish\(jwt,c\)\{.*?\n\}\nasync function claimerProprietaire",
    re.DOTALL,
)
finish_replacement = r'''async function _finish(jwt,c){
  var ok=(c.results||[]).filter(function(r){return r.ok;});
  if(!ok.length){_propErr((c.results||[]).map(function(r){return r.raison||"";}).join(", ")||c.erreur||"Claim echoue.");return;}
  var eid=ok[0].entreprise_id||"";
  try{
    var sr=await fetch(RELAY_URL+"/industrial/owner-session",{
      method:"POST",
      headers:{"Content-Type":"application/json","Authorization":"Bearer "+jwt},
      body:JSON.stringify({jwt:jwt,entreprise_id:eid})
    });
    var sd=await sr.json();
    if(!sr.ok||!sd.ok||!sd.session||!sd.session.salarie_id){
      _propErr(sd.erreur||"Session dirigeant impossible.");return;
    }
    var s=sd.session;
    localStorage.setItem("aria_industrial_owner_jwt",jwt);
    localStorage.setItem("aria_industrial_email",s.email||"");
    localStorage.setItem("aria_industrial_poste","dirigeant");
    localStorage.setItem("aria_industrial_nom",s.nom||"");
    localStorage.setItem("aria_session_active","dirigeant");
    localStorage.setItem("aria_industrial_token",s.salarie_id);
    localStorage.setItem("aria_industrial_entreprise_id",s.entreprise_id);
    localStorage.setItem("aria_industrial_role","dirigeant");
    localStorage.setItem("aria_industrial_session",JSON.stringify(s));
    if(sd.client_token){localStorage.setItem("aria_industrial_client_token",sd.client_token);}
    _propOk("Propriete verifiee. Ouverture de votre espace dirigeant...");
    setTimeout(function(){window.location="/poste-dirigeant.html";},900);
  }catch(e){_propErr("Erreur session dirigeant: "+(e.message||e));}
}
async function claimerProprietaire'''
html, n = finish_pattern.subn(finish_replacement, html, count=1)
if n != 1:
    raise SystemExit(f"owner frontend _finish patch count={n}")

if "URLSearchParams(window.location.search)" not in html:
    auto_open = r'''
document.addEventListener("DOMContentLoaded",function(){
  try{
    var q=new URLSearchParams(window.location.search);
    if(q.get("owner")==="1"||q.get("success")==="1"){modeProprietaire();}
  }catch(e){}
});
'''
    idx = html.rfind("</script>")
    if idx < 0:
        raise SystemExit("bootstrap closing script not found")
    html = html[:idx] + auto_open + html[idx:]

# 6) Regression contract written by Charlie, not by the implementation patch.
test_source = r'''"""Charlie 20 — owner session contract + final canonical wiring."""
import asyncio
import os
import re
import sys
from pathlib import Path
import httpx

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


def _run(coro):
    return asyncio.run(coro)


def test_owner_session_route_registered_and_requires_jwt():
    async def _case():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=srv.app), base_url="http://test") as c:
            r = await c.post("/industrial/owner-session", json={})
            assert r.status_code != 404
            data = r.json()
            assert data.get("ok") is False
            assert "JWT" in (data.get("erreur") or "")
    _run(_case())


def test_owner_session_is_server_authoritative():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    m = re.search(r'async def industrial_owner_session\(.*?(?=\n@app)', src, re.DOTALL)
    assert m, "owner-session endpoint missing"
    code = m.group(0)
    for required in ["dirigeant_id", "product_entitlements", "eq.industrial", "salaries", "role", "dirigeant", "user_id"]:
        assert required in code
    assert "trial_is_valid" in code
    assert "ensure_legacy_client" in code


def test_owner_frontend_gets_real_server_session():
    html = (ROOT / "connexion-industrial.html").read_text(encoding="utf-8")
    assert "/industrial/owner-session" in html
    assert "aria_industrial_session" in html
    assert "aria_industrial_token" in html
    assert "salarie_id" in html
    assert 'window.location="/poste-dirigeant.html"' in html or "window.location = \"/poste-dirigeant.html\"" in html


def test_industrial_entry_redirect_exists():
    redirects = (ROOT / "_redirects").read_text(encoding="utf-8")
    assert "/industrial /connexion-industrial.html" in " ".join(redirects.split())
    assert "aria_industrial_v1.html" not in redirects


def test_checkout_returns_to_owner_bootstrap():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    assert "https://forgedis.fr/connexion-industrial.html?owner=1&success=1" in src


def test_verifier_forfait_has_no_stale_ent_status():
    src = (ROOT / "server.py").read_text(encoding="utf-8")
    start = src.index("async def verifier_forfait(")
    end = src.find("\nasync def ", start + 10)
    code = src[start:end]
    assert "ent_status" not in code
    assert 'verifier_acces(token_recu, "facility")' in code


def test_owner_bootstrap_auto_opens_after_checkout():
    html = (ROOT / "connexion-industrial.html").read_text(encoding="utf-8")
    assert "URLSearchParams" in html
    assert 'q.get("owner")' in html
    assert 'q.get("success")' in html
'''

SERVER.write_text(server, encoding="utf-8")
HTML.write_text(html, encoding="utf-8")
TEST.write_text(test_source, encoding="utf-8")
print("Charlie patch applied: server.py, connexion-industrial.html, tests/test_charlie20.py")
