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
