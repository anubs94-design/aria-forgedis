import os
import httpx
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ── Scheduler reset compteurs mensuels ──
async def reset_compteurs_mensuels():
    """Remet taches_ce_mois a 0 pour tous les clients le 1er de chaque mois."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/clients",
                params={"taches_ce_mois": "gt.0"},
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json={"taches_ce_mois": 0}
            )
        print("[SCHEDULER] Compteurs mensuels remis a 0")
    except Exception as e:
        print(f"[SCHEDULER] Erreur reset: {e}")

async def scheduler_loop():
    """Boucle qui verifie chaque heure si on est le 1er du mois a minuit."""
    import datetime
    while True:
        now = datetime.datetime.now()
        # Le 1er de chaque mois entre 00h00 et 00h59
        if now.day == 1 and now.hour == 0:
            await reset_compteurs_mensuels()
            await asyncio.sleep(3600)  # Attendre 1h pour ne pas relancer
        else:
            await asyncio.sleep(1800)  # Vérifier toutes les 30 minutes

@asynccontextmanager
async def lifespan(app):
    # Démarrer le scheduler au lancement du serveur
    task = asyncio.create_task(scheduler_loop())
    print("[STARTUP] Scheduler reset mensuel demarre")
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CLAUDE_KEY = os.environ.get("ARIA_CLAUDE_KEY", "")

SYSTEM_SENIOR = """Tu es Aria, assistante vocale intelligente de Forgedis pour les seniors de 60 ans et plus.

COMPORTEMENT :
- Reponds TOUJOURS en francais, maximum 2-3 phrases courtes
- Tu as acces a toutes les fonctions : rappels, emails, questions, calculs, meteo, actualites
- Pour les RAPPELS : reponds "Rappel enregistre ! Je vous previens a [heure] pour [sujet]."
- Pour les EMAILS : aide a rediger directement
- Pour les QUESTIONS : reponds simplement et clairement
- JAMAIS "je ne peux pas", "dans la version complete", "je comprends"
- Utilise le prenom de l utilisateur quand tu le connais
- Sois chaleureux, patient, encourageant"""

@app.get("/sante")
def sante():
    return {"status": "ok"}

@app.post("/ask")
async def ask(body: dict):
    msg = body.get("message", "")
    token_recu = body.get("token", "")
    system = body.get("system", SYSTEM_SENIOR)
    if token_recu:
        autorise, msg_err, forfait = await verifier_forfait(token_recu, "eco")
        if not autorise:
            return {"response": msg_err}
    if not CLAUDE_KEY:
        return {"response": "Cle API manquante"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300, "system": system, "messages": [{"role": "user", "content": msg}]})
        data = r.json()
        return {"response": data["content"][0]["text"]}

@app.post("/bienvenue")
async def bienvenue(body: dict):
    return {"ok": True}

PROXY_TOKEN = os.environ.get("ARIA_PROXY_TOKEN", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Email via SMTP OVH
SMTP_LOGIN = os.environ.get("SMTP_LOGIN", "contact@forgedis.fr")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_SERVER = "ssl0.ovh.net"
SMTP_PORT = 465
EMAIL_FROM = "Aria FORGEDIS <contact@forgedis.fr>"
EMAIL_ADMIN = "contact@forgedis.fr"

# Stripe Product IDs
STRIPE_PRODUCT_INDUSTRIAL = os.environ.get("STRIPE_PRODUCT_INDUSTRIAL", "")
STRIPE_PRODUCT_KIDS_SOLO = os.environ.get("STRIPE_PRODUCT_KIDS_SOLO", "prod_UrdvcsgXqxJbK2")
STRIPE_PRODUCT_KIDS_FAMILLE = os.environ.get("STRIPE_PRODUCT_KIDS_FAMILLE", "prod_UrdxZxTDPHxJrJ")

async def envoyer_email(to: str, subject: str, html: str):
    """Envoie un email via SMTP OVH."""
    if not SMTP_PASSWORD:
        print(f"[EMAIL] SMTP non configure. To: {to}")
        return False
    try:
        import smtplib, ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(html, "html", "utf-8"))
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.sendmail(SMTP_LOGIN, [to], msg.as_bytes())
        print(f"[EMAIL] Envoye a {to}")
        return True
    except Exception as e:
        print(f"[EMAIL] Erreur SMTP: {e}")
        return False

# --- Verification forfait client via Supabase ---
async def verifier_forfait(token_recu, type_requete="eco"):
    """Verifie le forfait du client. Retourne (autorise, message, forfait).
    type_requete: 'eco' (conversation Haiku) ou 'reflexion' (vision Sonnet)
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return True, "", "dev"  # Pas de Supabase configure = mode dev, tout passe

    # Si c'est le token de dev de Victor, toujours autoriser
    if token_recu == PROXY_TOKEN:
        return True, "", "dev"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Chercher le client par token
            r = await client.get(
                f"{SUPABASE_URL}/rest/v1/clients",
                params={"token": f"eq.{token_recu}", "select": "*"},
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                },
            )
            data = r.json()

            if not data:
                return False, "Token inconnu.", "aucun"

            client_data = data[0]

            if not client_data.get("actif", False):
                return False, "Votre abonnement est inactif. Contactez le support.", "inactif"

            forfait = client_data.get("forfait", "gratuit")
            taches = client_data.get("taches_ce_mois", 0)
            mois = client_data.get("mois_en_cours", "")

            # Reset compteur si nouveau mois
            import datetime
            mois_actuel = datetime.datetime.now().strftime("%Y-%m")
            if mois != mois_actuel:
                taches = 0
                mois = mois_actuel

            # Verifier les plafonds
            if forfait == "gratuit":
                if type_requete == "reflexion":
                    return False, "Le pilotage PC est reserve a Aria Facility (12,99 euros/mois). Passez a Facility pour debloquer toutes les fonctions.", "gratuit"
                if taches >= 30:
                    return False, "Vous avez utilise vos 30 eco-taches du mois. Passez a Aria Facility pour continuer.", "gratuit"

            # Incrementer le compteur
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/clients",
                params={"token": f"eq.{token_recu}"},
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json={"taches_ce_mois": taches + 1, "mois_en_cours": mois},
            )

            return True, "", forfait

    except Exception as e:
        # En cas d'erreur Supabase, on laisse passer (pas de blocage client pour un bug serveur)
        return True, f"Erreur verification: {e}", "erreur"

# --- STRIPE WEBHOOK ---
from fastapi import Request
import secrets as secrets_mod

@app.post("/client-token")
async def client_token(body: dict):
    """Le PC ou l'app envoie l'email du client, on renvoie son token."""
    email = body.get("email", "").strip().lower()
    if not email:
        return {"erreur": "Email manquant."}
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"erreur": "Service indisponible."}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{SUPABASE_URL}/rest/v1/clients",
                params={"email": f"eq.{email}", "select": "token,forfait,actif"},
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                },
            )
            data = r.json()
            if not data:
                # Aucun compte : creation automatique d'un compte gratuit
                # (offre Decouverte, sans carte, sans passer par Stripe)
                nouveau_token = "aria_" + secrets_mod.token_hex(32)
                r_create = await client.post(
                    f"{SUPABASE_URL}/rest/v1/clients",
                    headers={
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    },
                    json={"email": email, "token": nouveau_token, "forfait": "gratuit", "actif": True},
                )
                if r_create.status_code not in (200, 201):
                    return {"erreur": "Impossible de creer le compte."}
                nouveau = r_create.json()
                if not nouveau:
                    return {"erreur": "Impossible de creer le compte."}
                return {"token": nouveau[0]["token"], "forfait": nouveau[0]["forfait"], "nouveau_compte": True}
            client_data = data[0]
            if not client_data.get("actif", False):
                return {"erreur": "Votre abonnement est inactif."}
            # Recuperer le poste du salarie dans la table salaries
            poste = "dirigeant"
            try:
                r_sal = await client.get(
                    f"{SUPABASE_URL}/rest/v1/salaries",
                    params={"email": f"eq.{email}", "select": "poste"},
                    headers={
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    },
                )
                sal_data = r_sal.json()
                if sal_data and sal_data[0].get("poste"):
                    poste = sal_data[0]["poste"]
            except Exception:
                pass
            return {"token": client_data["token"], "forfait": client_data["forfait"], "poste": poste}
    except Exception as e:
        return {"erreur": str(e)}

@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    """Recoit les evenements Stripe (paiement, annulation).
    Cree le token client dans Supabase si nouveau, ou desactive si annulation."""
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")

    # Verification signature (basique, sans lib stripe)
    # En production, on pourrait utiliser la lib stripe pour verifier
    # Pour l'instant, on verifie juste que le secret est present
    if not STRIPE_WEBHOOK_SECRET:
        return {"erreur": "webhook non configure"}

    try:
        import json as json_mod
        event = json_mod.loads(body)
    except Exception:
        return {"erreur": "body invalide"}

    event_type = event.get("type", "")
    data_obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        email = data_obj.get("customer_email", "") or data_obj.get("customer_details", {}).get("email", "")
        if not email:
            return {"status": "ignore", "raison": "pas d'email"}

        # Detecter le produit via metadata ou line_items
        metadata = data_obj.get("metadata", {})
        produit = metadata.get("produit", "")
        nom_entreprise = metadata.get("nom_entreprise", "")
        nb_employes = metadata.get("nb_employes", "0")
        montant = data_obj.get("amount_total", 0)

        # Determiner le forfait selon le produit
        if produit == "industrial" or "industrial" in str(data_obj.get("description", "")).lower():
            forfait = "industrial"
        elif produit == "kids_famille":
            forfait = "kids_famille"
        elif produit == "kids_solo":
            forfait = "kids_solo"
        else:
            forfait = "facility"

        token = "aria_" + secrets_mod.token_hex(32)
        import datetime
        date_fin_essai = (datetime.datetime.now() + datetime.timedelta(days=14)).isoformat()

        if SUPABASE_URL and SUPABASE_SERVICE_KEY:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Verifier si client existe
                r = await client.get(
                    f"{SUPABASE_URL}/rest/v1/clients",
                    params={"email": f"eq.{email}", "select": "token,forfait,actif"},
                    headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
                )
                existant = r.json()

                if existant:
                    await client.patch(
                        f"{SUPABASE_URL}/rest/v1/clients",
                        params={"email": f"eq.{email}"},
                        headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"},
                        json={"forfait": forfait, "actif": True},
                    )
                    action = "client reactive"
                else:
                    await client.post(
                        f"{SUPABASE_URL}/rest/v1/clients",
                        headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"},
                        json={"email": email, "token": token, "forfait": forfait, "taches_ce_mois": 0, "actif": True, "date_fin_essai": date_fin_essai},
                    )
                    action = "client cree"

                # Onboarding Industrial : creer l'entreprise
                if forfait == "industrial":
                    await client.post(
                        f"{SUPABASE_URL}/rest/v1/entreprises",
                        headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"},
                        json={
                            "email_contact": email,
                            "nom_entreprise": nom_entreprise or email.split("@")[0],
                            "nombre_employes": int(nb_employes) if nb_employes.isdigit() else 0,
                            "montant_mensuel": montant / 100 if montant else 0,
                            "statut_paiement": "essai",
                            "postes_actifs": ["dirigeant"],
                            "option_cloud": False,
                            "date_renouvellement": date_fin_essai,
                        },
                    )

                    # Email au client Industrial
                    lien_connexion = "https://forgedis.fr/connexion-industrial.html"
                    html_client = f"""
                    <div style="font-family:Inter,sans-serif;background:#070B18;color:#F0F3FB;padding:40px;max-width:600px;margin:0 auto;border-radius:16px;">
                      <h1 style="color:#E8873A;font-size:24px;">Bienvenue sur Aria Industrial !</h1>
                      <p>Bonjour,</p>
                      <p>Votre espace entreprise FORGEDIS est pret. Voici comment acceder a votre tableau de bord :</p>
                      <div style="background:#111934;border-radius:12px;padding:20px;margin:20px 0;">
                        <p><strong>Email :</strong> {email}</p>
                        <p><strong>Lien de connexion :</strong> <a href="{lien_connexion}" style="color:#E8873A;">{lien_connexion}</a></p>
                        <p style="color:#A6B0CC;font-size:13px;">Votre mot de passe vous sera communique par votre administrateur FORGEDIS.</p>
                      </div>
                      <p>Votre essai gratuit de 14 jours a commence. Profitez-en pour decouvrir tous les postes disponibles.</p>
                      <p style="color:#6D7799;font-size:12px;margin-top:30px;font-style:italic;">L'IA francaise qui n'oublie personne. — FORGEDIS</p>
                    </div>"""
                    await envoyer_email(email, "Bienvenue sur Aria Industrial — votre espace est pret", html_client)

                    # Email a Victor
                    html_admin = f"""
                    <div style="font-family:Inter,sans-serif;padding:20px;">
                      <h2>Nouvelle souscription Industrial</h2>
                      <p><strong>Email :</strong> {email}</p>
                      <p><strong>Entreprise :</strong> {nom_entreprise}</p>
                      <p><strong>Employes :</strong> {nb_employes}</p>
                      <p><strong>Montant :</strong> {montant/100 if montant else 0} EUR/mois</p>
                      <p><strong>Action requise :</strong> Definir le mot de passe dirigeant depuis admin.html</p>
                    </div>"""
                    await envoyer_email(EMAIL_ADMIN, f"Nouveau client Industrial : {email}", html_admin)

                elif forfait in ("facility", "kids_solo", "kids_famille"):
                    # Email client Facility/Kids
                    produit_label = {"facility": "Aria Facility", "kids_solo": "Aria Kids Solo", "kids_famille": "Aria Kids Famille", "industrial": "Aria Industrial"}.get(forfait, "Aria")
                    lien = "https://forgedis.fr/connexion.html"
                    html_client = f"""
                    <div style="font-family:Inter,sans-serif;background:#070B18;color:#F0F3FB;padding:40px;max-width:600px;margin:0 auto;border-radius:16px;">
                      <h1 style="color:#FF7A59;font-size:24px;">Bienvenue sur {produit_label} !</h1>
                      <p>Votre abonnement est actif. Connectez-vous avec votre email :</p>
                      <div style="background:#111934;border-radius:12px;padding:20px;margin:20px 0;">
                        <p><strong>Email :</strong> {email}</p>
                        <p><a href="{lien}" style="color:#FF7A59;font-size:16px;">Acces a mon espace →</a></p>
                      </div>
                      <p style="color:#6D7799;font-size:12px;margin-top:30px;font-style:italic;">L'IA francaise qui n'oublie personne. — FORGEDIS</p>
                    </div>"""
                    await envoyer_email(email, f"Bienvenue sur {produit_label} — votre acces est actif", html_client)
                    await envoyer_email(EMAIL_ADMIN, f"Nouveau client {forfait}: {email}", f"<p>Nouveau client: {email} — forfait: {forfait}</p>")

                return {"status": "ok", "action": action, "email": email, "forfait": forfait}

    elif event_type == "invoice.payment_succeeded":
        # Paiement mensuel reussi ? garder actif
        email = data_obj.get("customer_email", "")
        if email and SUPABASE_URL and SUPABASE_SERVICE_KEY:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.patch(
                    f"{SUPABASE_URL}/rest/v1/clients",
                    params={"email": f"eq.{email}"},
                    headers={
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    json={"actif": True},
                )
        return {"status": "ok", "action": "paiement confirme"}

    elif event_type == "customer.subscription.deleted":
        # Annulation ? desactiver le client (pas supprimer)
        email = data_obj.get("customer_email", "")
        if not email:
            # Essayer via customer
            customer_id = data_obj.get("customer", "")
            email = customer_id  # fallback, on utilisera le customer_id
        if email and SUPABASE_URL and SUPABASE_SERVICE_KEY:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.patch(
                    f"{SUPABASE_URL}/rest/v1/clients",
                    params={"email": f"eq.{email}"},
                    headers={
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    json={"actif": False},
                )
        return {"status": "ok", "action": "client desactive"}

    return {"status": "ignore", "type": event_type}

SYSTEM_INDUSTRIAL = """Tu es Aria, assistante IA integree dans les postes de travail Aria Industrial (FORGEDIS).
Tu aides les salaries et dirigeants de PME sur :
- Droit du travail (Code du travail, CCN, obligations legales)
- Gestion RH (contrats, absences, heures supplementaires)
- Comptabilite et fiscalite PME
- Achats et gestion fournisseurs
- Logistique et operations
- Consulting strategique pour dirigeants
REGLES :
- Reponds en francais, de facon concise et actionnable (5-8 phrases max)
- Cite toujours les textes legaux quand tu reponds sur le droit (ex: art. L3121-18 CT)
- Si tu n'es pas certain, dis-le clairement et recommande un professionnel
- Jamais de reponse vague : donne des chiffres, des delais, des references precises
- Triple verification mentale avant tout calcul financier"""


@app.post("/ask-kids")
async def ask_kids(body: dict):
    message    = body.get("message", "")
    token      = body.get("token", "")
    max_tokens = int(body.get("max_tokens", 1200))
    model_req  = body.get("model", "")

    if not message:
        return {"erreur": "Message vide."}

    autorise, msg_err, forfait = await verifier_forfait(token)
    if not autorise:
        return {"erreur": msg_err or "Token invalide ou forfait inactif."}
    if forfait not in ("kids_solo", "kids_famille", "facility", "forgedis", "tous", "industrial", "dev", "erreur"):
        return {"erreur": "Forfait insuffisant pour Aria Kids."}

    model_a_utiliser = "claude-sonnet-4-6" if model_req == "sonnet" else "claude-haiku-4-5-20251001"

    SYSTEM_KIDS = (
        "Tu es Aria, assistante pedagogique de FORGEDIS. "
        "Tu generes des lecons, quiz et examens alignes sur le programme de l'Education Nationale francaise (CP a BTS). "
        "Tu reponds UNIQUEMENT en JSON valide quand on te le demande. "
        "Tes explications sont claires, bienveillantes et adaptees au niveau de l'eleve. "
        "Tu ne parles jamais de politique, religion ou sujets sensibles."
    )

    try:
        import anthropic as _anthropic
        client_ai = _anthropic.Anthropic(api_key=CLAUDE_KEY)
        resp = client_ai.messages.create(
            model=model_a_utiliser,
            max_tokens=min(max_tokens, 4096),
            system=SYSTEM_KIDS,
            messages=[{"role": "user", "content": message}],
        )
        texte = resp.content[0].text if resp.content else ""
        return {"response": texte}
    except Exception as e:
        print(f"[ASK-KIDS] Erreur: {e}")
        return {"erreur": "Service IA temporairement indisponible."}


@app.post("/client-token-kids")
async def client_token_kids(body: dict):
    email = body.get("email", "").strip().lower()
    if not email:
        return {"erreur": "Email manquant."}
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"erreur": "Configuration serveur manquante."}
    import httpx as _httpx
    async with _httpx.AsyncClient(timeout=10.0) as hx:
        r = await hx.get(
            f"{SUPABASE_URL}/rest/v1/clients",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
            params={"email": f"eq.{email}", "select": "token,forfait,actif,kids_profils"}
        )
        rows = r.json()
    if not rows:
        return {"erreur": "Compte introuvable."}
    row = rows[0]
    if not row.get("actif"):
        return {"erreur": "Abonnement inactif."}
    if row.get("forfait") not in ("kids_solo", "kids_famille", "facility", "forgedis", "tous"):
        return {"erreur": "Forfait insuffisant pour Aria Kids."}
    return {"token": row["token"], "forfait": row["forfait"], "kids_profils": row.get("kids_profils") or []}

@app.get("/profil-kids")
async def get_profil_kids(token: str = ""):
    if not token:
        return {"erreur": "Token manquant."}
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"erreur": "Configuration serveur manquante."}
    import httpx as _httpx
    async with _httpx.AsyncClient(timeout=10.0) as hx:
        r = await hx.get(
            f"{SUPABASE_URL}/rest/v1/clients",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"},
            params={"token": f"eq.{token}", "select": "kids_profils"}
        )
        rows = r.json()
    if not rows:
        return {"kids_profils": []}
    return {"kids_profils": rows[0].get("kids_profils") or []}

@app.post("/profil-kids")
async def post_profil_kids(body: dict):
    token = body.get("token", "")
    profils = body.get("profils", [])
    if not token:
        return {"erreur": "Token manquant."}
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"erreur": "Configuration serveur manquante."}
    import httpx as _httpx
    async with _httpx.AsyncClient(timeout=10.0) as hx:
        import json as _json
        r = await hx.patch(
            f"{SUPABASE_URL}/rest/v1/clients",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            params={"token": f"eq.{token}"},
            content=_json.dumps({"kids_profils": profils}).encode()
        )
    return {"ok": True}

@app.post("/ask-industrial")
async def ask_industrial(body: dict):
    msg = body.get("message", "")
    token_recu = body.get("token", "")
    max_tokens = min(int(body.get("max_tokens", 500)), 800)
    system_custom = body.get("system", SYSTEM_INDUSTRIAL)
    if not msg:
        return {"response": "Message vide."}
    if not CLAUDE_KEY:
        return {"response": "Cle API manquante."}
    if token_recu and token_recu != PROXY_TOKEN and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        autorise, msg_err, forfait = await verifier_forfait(token_recu, "eco")
        if not autorise:
            return {"response": msg_err}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": CLAUDE_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": max_tokens, "system": system_custom, "messages": [{"role": "user", "content": msg}]},
            )
            data = r.json()
            if "content" not in data:
                return {"response": "Service temporairement indisponible."}
            return {"response": data["content"][0]["text"]}
    except Exception as e:
        print(f"[ASK-INDUSTRIAL] Erreur: {e}")
        return {"response": "Service indisponible. Reessayez."}

INDUSTRIAL_PRICES = {
    "base":       "price_1Txb8dI54RQfwJiYhVgtBFWP",
    "sal_t1":     "price_1Txb8kI54RQfwJiYZrHbuF4p",
    "sal_t2":     "price_1Txb8tI54RQfwJiYoPExEr7M",
    "sal_t3":     "price_1Txb91I54RQfwJiYkdgk1zZg",
    "sal_t4":     "price_1Txb9AI54RQfwJiYZwFEzbnU",
    "site":       "price_1Txb9II54RQfwJiY87wN2go3",
    "cloud":      "price_1Txb9QI54RQfwJiYjTzdob0k",
    "sur_mesure": "price_1Txb9YI54RQfwJiYyv4JmYJL",
}

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

@app.post("/checkout-industrial")
async def checkout_industrial(body: dict):
    """Cree une session Stripe Checkout pour Aria Industrial.
    Compose automatiquement les line_items selon le nombre de salaries,
    sites additionnels, option cloud et postes sur mesure."""
    email        = body.get("email", "").strip().lower()
    nb_sal       = int(body.get("nb_salaries", 1))
    nb_sites     = int(body.get("nb_sites_additionnels", 0))
    cloud        = bool(body.get("cloud", False))
    nb_custom    = int(body.get("nb_postes_sur_mesure", 0))
    nom_entreprise = body.get("nom_entreprise", "")
    success_url  = body.get("success_url", "https://forgedis.fr/industrial.html?success=1")
    cancel_url   = body.get("cancel_url", "https://forgedis.fr/industrial.html?cancel=1")

    if not email:
        return {"erreur": "email requis"}
    if not STRIPE_SECRET_KEY:
        return {"erreur": "Stripe non configure"}
    if nb_sal < 1 or nb_sal > 49:
        return {"erreur": "Nombre de salaries invalide (1-49). Pour 50+, utilisez /devis-industrial."}

    # Determiner la tranche salaries
    if nb_sal <= 5:
        price_sal = INDUSTRIAL_PRICES["sal_t1"]
    elif nb_sal <= 15:
        price_sal = INDUSTRIAL_PRICES["sal_t2"]
    else:
        price_sal = INDUSTRIAL_PRICES["sal_t3"]

    # Composer les line_items
    line_items = [
        {"price": INDUSTRIAL_PRICES["base"], "quantity": 1},
        {"price": price_sal, "quantity": nb_sal},
    ]
    if nb_sites > 0:
        line_items.append({"price": INDUSTRIAL_PRICES["site"], "quantity": nb_sites})
    if cloud:
        line_items.append({"price": INDUSTRIAL_PRICES["cloud"], "quantity": 1})
    if nb_custom > 0:
        line_items.append({"price": INDUSTRIAL_PRICES["sur_mesure"], "quantity": nb_custom})

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
                data={
                    "mode": "subscription",
                    "customer_email": email,
                    "subscription_data[trial_period_days]": "14",
                    "subscription_data[metadata][produit]": "industrial",
                    "subscription_data[metadata][nom_entreprise]": nom_entreprise,
                    "subscription_data[metadata][nb_employes]": str(nb_sal),
                    "subscription_data[metadata][nb_sites]": str(nb_sites),
                    "subscription_data[metadata][cloud]": "oui" if cloud else "non",
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    **{f"line_items[{i}][price]": item["price"] for i, item in enumerate(line_items)},
                    **{f"line_items[{i}][quantity]": str(item["quantity"]) for i, item in enumerate(line_items)},
                }
            )
            data = r.json()
            if "url" not in data:
                print(f"[CHECKOUT-INDUSTRIAL] Erreur Stripe: {data}")
                return {"erreur": "Impossible de creer la session de paiement."}
            return {"url": data["url"], "session_id": data.get("id", "")}
    except Exception as e:
        print(f"[CHECKOUT-INDUSTRIAL] Exception: {e}")
        return {"erreur": "Service indisponible."}

INDUSTRIAL_PRICES = {
    "base":       "price_1Txb8dI54RQfwJiYhVgtBFWP",
    "sal_t1":     "price_1Txb8kI54RQfwJiYZrHbuF4p",
    "sal_t2":     "price_1Txb8tI54RQfwJiYoPExEr7M",
    "sal_t3":     "price_1Txb91I54RQfwJiYkdgk1zZg",
    "sal_t4":     "price_1Txb9AI54RQfwJiYZwFEzbnU",
    "site":       "price_1Txb9II54RQfwJiY87wN2go3",
    "cloud":      "price_1Txb9QI54RQfwJiYjTzdob0k",
    "sur_mesure": "price_1Txb9YI54RQfwJiYyv4JmYJL",
}

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

@app.post("/devis-industrial")
async def devis_industrial(body: dict):
    """Recoit une demande de devis pour 50+ salaries et notifie FORGEDIS."""
    nom        = body.get("nom", "")
    email      = body.get("email", "")
    nb_employes = body.get("nb_employes", 0)
    message    = body.get("message", "")
    if not email:
        return {"erreur": "email requis"}
    html = f"""
    <div style="font-family:Inter,sans-serif;padding:20px;">
      <h2>Demande de devis Industrial 50+ salaries</h2>
      <p><strong>Nom :</strong> {nom}</p>
      <p><strong>Email :</strong> {email}</p>
      <p><strong>Nombre de salaries :</strong> {nb_employes}</p>
      <p><strong>Message :</strong> {message}</p>
      <p style="color:#E8873A;font-weight:bold;">Action requise : repondre sous 24h avec un devis personnalise.</p>
    </div>"""
    await envoyer_email(EMAIL_ADMIN, f"Demande devis Industrial 50+ : {nom} ({email})", html)
    return {"ok": True}

@app.post("/sauvegarder")
async def sauvegarder_donnees(body: dict):
    """Sauvegarde les donnees d'un salarie Industrial dans Supabase (option cloud)."""
    email_entreprise = body.get("email_entreprise", "")
    nom_salarie = body.get("nom_salarie", "")
    donnees = body.get("donnees", {})
    if not email_entreprise or not nom_salarie:
        return {"erreur": "email_entreprise et nom_salarie requis"}
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return {"erreur": "service indisponible"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{SUPABASE_URL}/rest/v1/rpc/sauvegarder_donnees_salarie",
                headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "Content-Type": "application/json"},
                json={"p_email_entreprise": email_entreprise, "p_nom_salarie": nom_salarie, "p_donnees": donnees}
            )
            return r.json()
    except Exception as e:
        return {"erreur": str(e)}

@app.post("/vision")
async def vision(body: dict):
    token_recu = body.get("token", "")
    if not PROXY_TOKEN or token_recu != PROXY_TOKEN:
        # Verifier dans Supabase si c'est un token client
        autorise, msg, forfait = await verifier_forfait(token_recu, "reflexion")
        if not autorise:
            return {"erreur": msg}
    if not CLAUDE_KEY:
        return {"erreur": "cle_manquante"}
    payload = body.get("payload", {})
    if not payload:
        return {"erreur": "payload_vide"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
    return r.json()

GOOGLE_SPEECH_KEY = os.environ.get("ARIA_GOOGLE_SPEECH_KEY", "")

@app.post("/transcribe")
async def transcribe(body: dict):
    token_recu = body.get("token", "")
    if not PROXY_TOKEN or token_recu != PROXY_TOKEN:
        return {"erreur": "token_invalide"}
    if not GOOGLE_SPEECH_KEY:
        return {"erreur": "cle_google_manquante"}

    audio_b64 = body.get("audio", "")
    langue = body.get("langue", "fr-FR")
    if not audio_b64:
        return {"erreur": "audio_vide"}

    payload = {
        "config": {
            "languageCode": langue,
        },
        "audio": {
            "content": audio_b64,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://speech.googleapis.com/v1/speech:recognize?key=" + GOOGLE_SPEECH_KEY,
            json=payload,
        )

    data = r.json()

    if "error" in data:
        return {"erreur": data["error"].get("message", "erreur_google")}

    resultats = data.get("results", [])
    if not resultats:
        return {"texte": ""}

    texte = resultats[0]["alternatives"][0]["transcript"]
    return {"texte": texte}


# ===================================================================
# RELAIS WEBSOCKET (Aria disponible partout, pas que sur le wifi local)
# ===================================================================
# Le PC (agent.py) et le telephone se connectent tous les deux a cette
# route avec le MEME token (ARIA_PROXY_TOKEN) et un role different.
# Render ne fait que transmettre les messages de l'un a l'autre, sans
# aucune logique metier (zero stockage, relais transparent comme /vision).

relais_connexions = {}

@app.websocket("/relais")
async def relais(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    role = websocket.query_params.get("role", "")

    # Validation token
    import httpx
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
    _PROXY_TOKEN = os.environ.get("ARIA_PROXY_TOKEN", "")

    # Le PROXY_TOKEN de dev est toujours valide (pas dans Supabase)
    if _PROXY_TOKEN and token == _PROXY_TOKEN:
        token_valide = True
    else:
        token_valide = False
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    SUPABASE_URL + "/rest/v1/clients",
                    headers={"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY},
                    params={"token": "eq." + token, "actif": "eq.true", "select": "token"}
                )
                data = r.json()
                token_valide = isinstance(data, list) and len(data) > 0
        except Exception:
            token_valide = False
    if not token_valide:
        await websocket.close(code=4001)
        return
    if role not in ("agent", "phone"):
        await websocket.close(code=4002)
        return

    await websocket.accept()

    if token not in relais_connexions:
        relais_connexions[token] = {"agent": None, "phone": None}
    relais_connexions[token][role] = websocket

    autre_role = "phone" if role == "agent" else "agent"

    try:
        while True:
            message = await websocket.receive_text()
            peer = relais_connexions.get(token, {}).get(autre_role)
            if peer is not None:
                try:
                    await peer.send_text(message)
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        if token in relais_connexions and relais_connexions[token].get(role) is websocket:
            relais_connexions[token][role] = None
