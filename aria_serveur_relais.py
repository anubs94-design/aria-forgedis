import os
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
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
            return {"token": client_data["token"], "forfait": client_data["forfait"]}
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
        # Nouveau client a paye — creer son token
        email = data_obj.get("customer_email", "") or data_obj.get("customer_details", {}).get("email", "")
        if not email:
            return {"status": "ignore", "raison": "pas d'email"}

        token = "aria_" + secrets_mod.token_hex(32)

        if SUPABASE_URL and SUPABASE_SERVICE_KEY:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Verifier si le client existe deja
                r = await client.get(
                    f"{SUPABASE_URL}/rest/v1/clients",
                    params={"email": f"eq.{email}", "select": "token,forfait"},
                    headers={
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    },
                )
                existant = r.json()

                if existant:
                    # Client existe deja — reactiver et passer en facility
                    await client.patch(
                        f"{SUPABASE_URL}/rest/v1/clients",
                        params={"email": f"eq.{email}"},
                        headers={
                            "apikey": SUPABASE_SERVICE_KEY,
                            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal",
                        },
                        json={"forfait": "facility", "actif": True},
                    )
                    return {"status": "ok", "action": "client reactive"}
                else:
                    # Nouveau client — creer
                    await client.post(
                        f"{SUPABASE_URL}/rest/v1/clients",
                        headers={
                            "apikey": SUPABASE_SERVICE_KEY,
                            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal",
                        },
                        json={
                            "email": email,
                            "token": token,
                            "forfait": "facility",
                            "taches_ce_mois": 0,
                            "actif": True,
                        },
                    )
                    return {"status": "ok", "action": "client cree", "email": email}

    elif event_type == "invoice.payment_succeeded":
        # Paiement mensuel reussi — garder actif
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
                    json={"actif": True, "forfait": "facility"},
                )
        return {"status": "ok", "action": "paiement confirme"}

    elif event_type == "customer.subscription.deleted":
        # Annulation — desactiver le client (pas supprimer)
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

    if not PROXY_TOKEN or token != PROXY_TOKEN:
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
