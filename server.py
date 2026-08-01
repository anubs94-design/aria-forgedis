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



# ══════════════════════════════════════════════════════════════
# ENDPOINTS ARIA KIDS (ajoutes 01/08/2026)
# ══════════════════════════════════════════════════════════════

KIDS_PRICES = {
    "solo":    os.environ.get("STRIPE_PRICE_KIDS_SOLO",    ""),
    "famille": os.environ.get("STRIPE_PRICE_KIDS_FAMILLE", ""),
}

@app.post("/checkout-kids")
async def checkout_kids(body: dict):
    """Session Stripe Checkout pour Aria Kids Solo (9,99) ou Famille (14,99)."""
    email   = body.get("email", "").strip().lower()
    forfait = body.get("forfait", "kids_solo")
    redirect_base = body.get("redirect", "https://forgedis.fr/app-kids.html")
    if not email:
        return {"erreur": "email requis"}
    if not STRIPE_SECRET_KEY:
        return {"erreur": "Stripe non configure"}
    plan = "famille" if forfait == "kids_famille" else "solo"
    price_id = KIDS_PRICES.get(plan, "")
    if not price_id:
        return {"erreur": f"STRIPE_PRICE_KIDS_{plan.upper()} manquant dans les env vars Render."}
    sep = "&" if "?" in redirect_base else "?"
    success_url = redirect_base + sep + "success=1&forfait=" + forfait
    cancel_url  = redirect_base + sep + "cancel=1"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                headers={"Authorization": f"Bearer {STRIPE_SECRET_KEY}"},
                data={
                    "mode": "subscription",
                    "customer_email": email,
                    "subscription_data[trial_period_days]": "14",
                    "subscription_data[metadata][produit]": forfait,
                    "line_items[0][price]": price_id,
                    "line_items[0][quantity]": "1",
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                }
            )
            data = r.json()
            if "url" not in data:
                print(f"[CHECKOUT-KIDS] Erreur Stripe: {data}")
                return {"erreur": "Impossible de creer la session de paiement."}
            return {"checkout_url": data["url"], "session_id": data.get("id", "")}
    except Exception as e:
        print(f"[CHECKOUT-KIDS] Exception: {e}")
        return {"erreur": "Service indisponible."}


@app.post("/inscription-kids")
async def inscription_kids(body: dict):
    """
    Inscription Kids : verifie si client existant puis lance checkout.
    Envoie un email de bienvenue avec lien de paiement.
    """
    email   = body.get("email", "").strip().lower()
    forfait = body.get("forfait", "kids_solo")
    redirect = body.get("redirect", "https://forgedis.fr/app-kids.html")
    if not email:
        return {"erreur": "email requis"}
    # Verifier si client deja connu
    existants = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{SUPABASE_URL}/rest/v1/clients",
                params={"email": f"eq.{email}", "select": "email,actif"},
                headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
            )
            existants = r.json() if isinstance(r.json(), list) else []
    except Exception as e:
        print(f"[INSCRIPTION-KIDS] Supabase lookup: {e}")
    # Dans tous les cas, creer/renvoyer une session checkout
    co = await checkout_kids({"email": email, "forfait": forfait, "redirect": redirect})
    if "erreur" in co:
        return co
    statut = "existant" if existants else "nouveau"
    # Email de bienvenue
    forfait_label = "Famille (14,99 euros/mois)" if forfait == "kids_famille" else "Solo (9,99 euros/mois)"
    await envoyer_email(
        to=email,
        subject="Bienvenue sur Aria Kids !",
        html=(
            f"<div style='font-family:sans-serif;max-width:480px;margin:0 auto'>"
            f"<h2 style='color:#FF7A59'>Aria Kids — votre essai commence !</h2>"
            f"<p>Forfait choisi : <strong>{forfait_label}</strong></p>"
            f"<p>Cliquez ci-dessous pour finaliser votre abonnement (14 jours gratuits) :</p>"
            f"<a href='{co['checkout_url']}' style='display:inline-block;background:#FF7A59;color:#fff;"
            f"padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700'>Activer mon abonnement</a>"
            f"<p style='font-size:12px;color:#888;margin-top:20px'>Questions : contact@forgedis.fr</p>"
            f"</div>"
        )
    )
    return {"statut": statut, "checkout_url": co["checkout_url"]}


@app.get("/devoirs")
async def get_devoirs(token: str = ""):
    """
    Recupere les devoirs envoyes depuis l app mobile (URLs images).
    Stockes dans Supabase colonne kids_devoirs (JSON array).
    Retourne liste vide si colonne absente ou client non trouve.
    """
    if not token:
        return {"devoirs": []}
    if token == PROXY_TOKEN:
        return {"devoirs": []}  # dev : pas de devoirs en base
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{SUPABASE_URL}/rest/v1/clients",
                params={"token": f"eq.{token}", "select": "kids_devoirs,actif"},
                headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
            )
            data = r.json()
            if not data or not data[0].get("actif"):
                return {"devoirs": []}
            devoirs = data[0].get("kids_devoirs") or []
            return {"devoirs": devoirs if isinstance(devoirs, list) else []}
    except Exception as e:
        print(f"[DEVOIRS] Erreur: {e}")
        return {"devoirs": []}


@app.post("/kids/generer-question")
async def kids_generer_question(body: dict):
    """
    Genere dynamiquement une question glisser-deposer via Claude Haiku.
    Fallback cote client si indisponible (banque locale dans app-kids.html).
    """
    token   = body.get("token", "")
    matiere = body.get("matiere", "general")
    niveau  = body.get("niveau", "college")
    nb_el   = min(int(body.get("nb_elements", 6)), 10)

    autorise, msg_err, forfait = await verifier_forfait(token)
    if not autorise:
        return {"erreur": msg_err or "Token invalide."}
    if forfait not in ("kids_solo", "kids_famille", "facility", "forgedis", "tous", "industrial", "dev", "erreur"):
        return {"erreur": "Forfait insuffisant."}

    prompt = (
        f"Genere une question de type glisser-deposer pour un eleve de {niveau} en {matiere}. "
        f"Cree exactement {nb_el} elements a classer dans 2 a 4 zones. "
        "Reponds UNIQUEMENT en JSON valide sans texte avant ni apres : "
        '{"zones":["Zone A","Zone B"],"elements":[{"mot":"exemple","zone":"Zone A"}],'
        '"explication":"Pourquoi ce classement en 1 phrase bienveillante."}'
    )
    try:
        import anthropic as _anthropic
        client_ai = _anthropic.Anthropic(api_key=CLAUDE_KEY)
        resp = client_ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        texte = resp.content[0].text if resp.content else ""
        start = texte.find("{"); end = texte.rfind("}")
        if start != -1 and end != -1:
            import json as _json
            parsed = _json.loads(texte[start:end+1])
            return {"question": parsed}
        return {"erreur": "Reponse IA invalide."}
    except Exception as e:
        print(f"[GENERER-QUESTION] Erreur: {e}")
        return {"erreur": "Service IA indisponible."}



# ══════════════════════════════════════════════════════════════
# ENDPOINTS JUMELAGE (01/08/2026) — 4 niveaux de securite
# ══════════════════════════════════════════════════════════════

AUTORITES_PAR_PAYS = {
    "France":   "PHAROS (https://www.internet-signalement.gouv.fr)",
    "Maroc":    "DGSN (https://www.dgsn.ma)",
    "Algerie":  "DGSN Algerie (https://www.dgsn.dz)",
    "USA":      "NCMEC (https://www.missingkids.org/gethelpnow/cybertipline)",
    "UK":       "CEOP (https://www.ceop.police.uk/Safety-Centre)",
    "Belgique": "Child Focus (https://www.childfocus.be)",
    "Canada":   "Cyberaide (https://www.cybertip.ca)",
}

async def _sb_get(path: str, params: dict = None):
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(
            f"{SUPABASE_URL}/rest/v1/{path}",
            params=params or {},
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
        )
        return r.json()

async def _sb_post(table: str, data: dict):
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json=data
        )
        return r.json()

async def _sb_patch(table: str, filtre: str, data: dict):
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.patch(
            f"{SUPABASE_URL}/rest/v1/{table}?{filtre}",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            json=data
        )
        return r.status_code

async def _sb_delete(table: str, filtre: str):
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.delete(
            f"{SUPABASE_URL}/rest/v1/{table}?{filtre}",
            headers={"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
        )
        return r.status_code


@app.post("/jumelage/attente")
async def jumelage_attente(body: dict):
    """Salle d attente. Tente matching immediat. Si match -> codes email aux parents."""
    token           = body.get("token", "")
    email_parent    = body.get("email_parent", "").strip().lower()
    prenom          = body.get("prenom", "").strip()
    niveau          = body.get("niveau", "")
    langue_cherchee = body.get("langue_cherchee", "").strip()
    langue_native   = body.get("langue_native", "").strip()
    pays            = body.get("pays", "")

    if not all([token, email_parent, prenom, langue_cherchee, langue_native]):
        return {"erreur": "Champs manquants."}

    autorise, msg_err, forfait = await verifier_forfait(token)
    if not autorise:
        return {"erreur": msg_err or "Token invalide."}

    import random as _rnd
    # Nettoyer entrees precedentes de ce token
    await _sb_delete("jumelage_attente", f"token=eq.{token}")

    # Chercher match : quelqu un qui cherche ma langue native et dont la langue native = ma langue cherchee
    candidats = await _sb_get("jumelage_attente", {
        "langue_cherchee": f"eq.{langue_native}",
        "langue_native":   f"eq.{langue_cherchee}",
        "token":           f"neq.{token}",
        "select":          "*",
        "limit":           "5"
    })

    if isinstance(candidats, list) and candidats:
        p = candidats[0]
        code_a = str(_rnd.randint(100000, 999999))
        code_b = str(_rnd.randint(100000, 999999))

        room = await _sb_post("jumelage_rooms", {
            "token_a": token, "email_parent_a": email_parent,
            "prenom_a": prenom, "langue_native_a": langue_native,
            "pays_a": pays, "code_a": code_a, "code_a_valide": False,
            "token_b": p["token"], "email_parent_b": p["email_parent"],
            "prenom_b": p["prenom_enfant"], "langue_native_b": p["langue_native"],
            "pays_b": p["pays"], "code_b": code_b, "code_b_valide": False,
            "langue_echange": f"{langue_native} / {langue_cherchee}",
            "statut": "en_attente_codes",
        })
        room_id = room[0]["id"] if isinstance(room, list) and room else None
        if not room_id:
            return {"erreur": "Erreur creation room."}

        await _sb_delete("jumelage_attente", f"id=eq.{p['id']}")

        def _html_email(prenom_e, prenom_c, pays_c, code, langue):
            return (
                f"<div style='font-family:sans-serif;max-width:500px;margin:0 auto'>"
                f"<h2 style='color:#7C6FFF'>Correspondant trouve !</h2>"
                f"<p><strong>{prenom_e}</strong> a ete mis en contact avec "
                f"<strong>{prenom_c}</strong> ({pays_c}) pour pratiquer le <strong>{langue}</strong>.</p>"
                f"<p>Donnez ce code a {prenom_e} pour debloquer le chat :</p>"
                f"<div style='font-size:36px;font-weight:900;color:#7C6FFF;letter-spacing:8px;"
                f"background:#f0eeff;padding:16px 24px;border-radius:12px;text-align:center;"
                f"margin:20px 0'>{code}</div>"
                f"<p style='font-size:12px;color:#888'>Aria surveille chaque message. "
                f"Vous serez alerte en cas de contenu inapproprie.<br>contact@forgedis.fr</p></div>"
            )

        await envoyer_email(
            email_parent,
            f"Aria Kids — {prenom} a trouve un correspondant !",
            _html_email(prenom, p["prenom_enfant"], p["pays"], code_a, langue_cherchee)
        )
        await envoyer_email(
            p["email_parent"],
            f"Aria Kids — {p['prenom_enfant']} a trouve un correspondant !",
            _html_email(p["prenom_enfant"], prenom, pays, code_b, p["langue_cherchee"])
        )

        return {
            "statut": "match",
            "room_id": room_id,
            "prenom_correspondant": p["prenom_enfant"],
            "pays_correspondant": p["pays"]
        }

    # Pas de match -> inscrire en attente
    await _sb_post("jumelage_attente", {
        "token": token, "email_parent": email_parent,
        "prenom_enfant": prenom, "niveau_enfant": niveau,
        "langue_cherchee": langue_cherchee, "langue_native": langue_native, "pays": pays,
    })
    return {"statut": "attente"}


@app.post("/jumelage/code-valider")
async def jumelage_code_valider(body: dict):
    """Valide le code 6 chiffres recu par email. Ouvre le chat si les deux codes sont valides."""
    token = body.get("token", "")
    code  = body.get("code", "").strip()
    if not token or not code:
        return {"erreur": "Champs manquants."}

    rooms_a = await _sb_get("jumelage_rooms", {"token_a": f"eq.{token}", "statut": f"neq.ferme", "select": "*"})
    rooms_b = await _sb_get("jumelage_rooms", {"token_b": f"eq.{token}", "statut": f"neq.ferme", "select": "*"})

    room = role = None
    if isinstance(rooms_a, list) and rooms_a:
        room = rooms_a[0]; role = "a"
    elif isinstance(rooms_b, list) and rooms_b:
        room = rooms_b[0]; role = "b"

    if not room:
        return {"erreur": "Aucune room trouvee."}
    if code != room.get(f"code_{role}", ""):
        return {"erreur": "Code incorrect."}

    await _sb_patch("jumelage_rooms", f"id=eq.{room['id']}", {f"code_{role}_valide": True})

    autre = "b" if role == "a" else "a"
    autre_valide = room.get(f"code_{autre}_valide", False)
    if autre_valide:
        await _sb_patch("jumelage_rooms", f"id=eq.{room['id']}", {"statut": "actif"})

    return {
        "statut": "ok",
        "room_id": room["id"],
        "prenom_correspondant": room.get(f"prenom_{autre}", ""),
        "pays_correspondant":   room.get(f"pays_{autre}", ""),
        "langue_echange":       room.get("langue_echange", ""),
        "chat_actif":           autre_valide,
    }


@app.post("/jumelage/message")
async def jumelage_message(body: dict):
    """
    Envoie un message avec filtrage 4 niveaux :
    N1 Haiku : insultes / vulgarites
    N2 regex  : donnees perso (tel, email, adresse, reseaux)
    N3 Sonnet : analyse contexte si N1 ou N2 declenche
    N4        : alerte Supabase + email parents + email FORGEDIS
    """
    token   = body.get("token", "")
    room_id = body.get("room_id", "")
    message = body.get("message", "").strip()
    prenom  = body.get("prenom", "")

    if not all([token, room_id, message]):
        return {"erreur": "Champs manquants."}
    if len(message) > 1000:
        return {"erreur": "Message trop long."}

    rooms_a = await _sb_get("jumelage_rooms", {"id": f"eq.{room_id}", "token_a": f"eq.{token}", "statut": "eq.actif", "select": "*"})
    rooms_b = await _sb_get("jumelage_rooms", {"id": f"eq.{room_id}", "token_b": f"eq.{token}", "statut": "eq.actif", "select": "*"})
    room = role = None
    if isinstance(rooms_a, list) and rooms_a:
        room = rooms_a[0]; role = "a"
    elif isinstance(rooms_b, list) and rooms_b:
        room = rooms_b[0]; role = "b"
    if not room:
        return {"erreur": "Room invalide ou chat non actif."}

    import anthropic as _ai, json as _json, re as _re
    client_ai = _ai.Anthropic(api_key=CLAUDE_KEY)

    niveau_alerte  = 0
    raison_blocage = ""

    # ── N1 : Haiku ──
    try:
        r1 = client_ai.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=100,
            messages=[{"role": "user", "content":
                f"Modere ce message d enfant : \"{message}\"\n"
                "JSON uniquement : {\"ok\":true/false,\"raison\":\"\"}\n"
                "ok=false si insulte, vulgarite, violence, haine. Sois bienveillant."}]
        )
        txt = r1.content[0].text.strip()
        p1  = _json.loads(txt[txt.find("{"):txt.rfind("}")+1])
        if not p1.get("ok", True):
            niveau_alerte  = 1
            raison_blocage = p1.get("raison", "Contenu inapproprie")
    except Exception:
        pass

    # ── N2 : regex donnees perso ──
    if niveau_alerte == 0:
        patterns = [
            r"\b\d{10}\b",
            r"\b\d{2}[\s.\-]\d{2}[\s.\-]\d{2}[\s.\-]\d{2}[\s.\-]\d{2}\b",
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            r"\b\d{1,4}[\s,]+(?:rue|avenue|bd|boulevard|impasse|chemin|route)\b",
            r"\bsnap\b|\binsta\b|\btiktok\b|\bdiscord\b|\bwhatsapp\b|\btelegram\b",
        ]
        for pat in patterns:
            if _re.search(pat, message, _re.IGNORECASE):
                niveau_alerte  = 2
                raison_blocage = "Donnee personnelle detectee"
                break

    # ── N3 : Sonnet si alerte ──
    if niveau_alerte > 0:
        try:
            r3 = client_ai.messages.create(
                model="claude-sonnet-4-6", max_tokens=300,
                messages=[{"role": "user", "content":
                    f"Expert protection enfance. Message : \"{message}\"\n"
                    f"Alerte N{niveau_alerte} : {raison_blocage}\n"
                    "JSON : {\"danger_reel\":true/false,\"niveau_final\":1-4,\"explication\":\"...\",\"action\":\"bloquer/alerter_parents/signaler_autorites\"}"}]
            )
            txt3 = r3.content[0].text.strip()
            p3   = _json.loads(txt3[txt3.find("{"):txt3.rfind("}")+1])
        except Exception:
            p3 = {"danger_reel": True, "niveau_final": niveau_alerte, "explication": raison_blocage, "action": "bloquer"}

        niveau_alerte  = p3.get("niveau_final", niveau_alerte)
        explication    = p3.get("explication", raison_blocage)
        autre          = "b" if role == "a" else "a"

        # ── N4 : alerte si danger confirme ──
        if p3.get("danger_reel") or niveau_alerte >= 3:
            pays_e   = room.get(f"pays_{role}", "France")
            autorite = AUTORITES_PAR_PAYS.get(pays_e, "Autorites locales")
            await _sb_post("alertes_jumelage", {
                "enfant_a_prenom": room.get(f"prenom_{role}", ""),
                "enfant_a_pays":   pays_e,
                "enfant_b_prenom": room.get(f"prenom_{autre}", ""),
                "enfant_b_pays":   room.get(f"pays_{autre}", ""),
                "parent_a_email":  room.get(f"email_parent_{role}", ""),
                "parent_b_email":  room.get(f"email_parent_{autre}", ""),
                "type_alerte":     raison_blocage,
                "categorie":       niveau_alerte,
                "message_declencheur": message,
                "claude_analyse":  True,
                "claude_verdict":  explication,
                "statut":          "NOUVEAU",
                "email_forgedis_envoye": False,
            })
            for pe in [room.get("email_parent_a"), room.get("email_parent_b")]:
                if pe:
                    await envoyer_email(pe, "Aria Kids — Alerte securite jumelage",
                        f"<div style='font-family:sans-serif;max-width:500px'>"
                        f"<h2 style='color:#E24B4A'>Message retenu par Aria</h2>"
                        f"<p>Niveau alerte : <strong>{niveau_alerte}/4</strong></p>"
                        f"<p>Raison : {explication}</p>"
                        f"<p>Le message n a pas ete transmis.</p>"
                        f"<p>Signalement si necessaire : <a href='#'>{autorite}</a></p>"
                        f"<p style='font-size:12px;color:#888'>contact@forgedis.fr</p></div>"
                    )
            await envoyer_email(EMAIL_ADMIN, f"[ALERTE N{niveau_alerte}] Jumelage",
                f"<p>Room:{room_id} | Auteur:{prenom} ({room.get(f'pays_{role}')})"
                f"<br>Message:{message}<br>Raison:{explication}</p>")

        await _sb_post("jumelage_messages", {
            "room_id": room_id, "token_auteur": token, "prenom_auteur": prenom,
            "message_original": message, "message_affiche": None,
            "statut": "bloque", "niveau_alerte": niveau_alerte, "raison_blocage": raison_blocage,
        })
        await _sb_patch("jumelage_rooms", f"id=eq.{room_id}", {"derniere_activite": "now()"})
        return {"statut": "bloque", "message_enfant": "Aria a retenu ce message. Essaie autrement !", "niveau": niveau_alerte}

    # ── Message OK ──
    await _sb_post("jumelage_messages", {
        "room_id": room_id, "token_auteur": token, "prenom_auteur": prenom,
        "message_original": message, "message_affiche": message,
        "statut": "ok", "niveau_alerte": 0,
    })
    await _sb_patch("jumelage_rooms", f"id=eq.{room_id}", {"derniere_activite": "now()"})
    return {"statut": "ok", "message_affiche": message}


@app.get("/jumelage/messages")
async def jumelage_get_messages(room_id: str = "", token: str = "", since: str = ""):
    """Polling messages OK depuis un timestamp. Verifie appartenance a la room."""
    if not room_id or not token:
        return {"messages": []}
    ra = await _sb_get("jumelage_rooms", {"id": f"eq.{room_id}", "token_a": f"eq.{token}", "select": "id"})
    rb = await _sb_get("jumelage_rooms", {"id": f"eq.{room_id}", "token_b": f"eq.{token}", "select": "id"})
    if not (isinstance(ra, list) and ra) and not (isinstance(rb, list) and rb):
        return {"messages": []}
    params = {"room_id": f"eq.{room_id}", "statut": "eq.ok",
              "select": "prenom_auteur,message_affiche,created_at,token_auteur",
              "order": "created_at.asc", "limit": "50"}
    if since:
        params["created_at"] = f"gt.{since}"
    msgs = await _sb_get("jumelage_messages", params)
    return {"messages": msgs if isinstance(msgs, list) else []}


@app.post("/jumelage/statut")
async def jumelage_statut(body: dict):
    """Statut room du token (aucun / attente / en_attente_codes / actif / ferme)."""
    token = body.get("token", "")
    if not token:
        return {"statut": "inconnu"}
    ra = await _sb_get("jumelage_rooms", {"token_a": f"eq.{token}", "statut": "neq.ferme", "select": "*", "order": "created_at.desc", "limit": "1"})
    rb = await _sb_get("jumelage_rooms", {"token_b": f"eq.{token}", "statut": "neq.ferme", "select": "*", "order": "created_at.desc", "limit": "1"})
    room = role = None
    if isinstance(ra, list) and ra:
        room = ra[0]; role = "a"
    elif isinstance(rb, list) and rb:
        room = rb[0]; role = "b"
    if not room:
        att = await _sb_get("jumelage_attente", {"token": f"eq.{token}", "select": "langue_cherchee,created_at"})
        if isinstance(att, list) and att:
            return {"statut": "attente", "langue_cherchee": att[0].get("langue_cherchee", "")}
        return {"statut": "aucun"}
    autre = "b" if role == "a" else "a"
    return {
        "statut":                room.get("statut", "inconnu"),
        "room_id":               room.get("id", ""),
        "prenom_correspondant":  room.get(f"prenom_{autre}", ""),
        "pays_correspondant":    room.get(f"pays_{autre}", ""),
        "langue_echange":        room.get("langue_echange", ""),
        "code_valide":           room.get(f"code_{role}_valide", False),
        "chat_actif":            room.get("statut") == "actif",
    }

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
