// src/services/ConversationService.js
// Conversation avec Aria quand le PC est eteint (via /ask sur Render).
// Pas de pilotage PC, juste de la discussion, des conseils, de la compagnie.

import { PROXY_TOKEN } from "./DocumentService";

const ASK_URL = "https://aria-forgelis.onrender.com/ask";

const SYSTEM_ARIA_CONVERSATION =
  "Tu es Aria, une assistante vocale chaleureuse pour seniors. " +
  "L'ordinateur de l'utilisateur n'est PAS allume en ce moment, " +
  "donc tu ne peux PAS agir sur le PC (pas d'ouverture d'app, pas de navigation, pas d'email).\n\n" +
  "Ce que tu PEUX faire :\n" +
  "- Discuter, tenir compagnie, ecouter\n" +
  "- Repondre a des questions (culture, meteo, calculs, actualites)\n" +
  "- Donner des conseils (sante, administratif, quotidien)\n" +
  "- Rassurer, encourager\n" +
  "- Rappeler un rendez-vous ou une information\n\n" +
  "Si l'utilisateur demande une action PC, reponds gentiment :\n" +
  "'Je ne peux pas faire ca maintenant car votre ordinateur est eteint. " +
  "Des qu'il sera allume, je pourrai le faire pour vous !'\n\n" +
  "Reponds TOUJOURS dans la langue de l'utilisateur, chaleureux et clair. " +
  "Sois concis (3-5 phrases max).";

export async function parlerSansPc(message, addLog) {
  try {
    if (addLog) addLog("Aria repond (sans PC)...");

    const response = await fetch(ASK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        system: SYSTEM_ARIA_CONVERSATION,
      }),
    });

    const data = await response.json();

    if (data.response) {
      if (addLog) addLog("Aria a repondu (mode conversation).");
      return data.response;
    } else {
      if (addLog) addLog("Reponse vide d'Aria.");
      return null;
    }
  } catch (e) {
    if (addLog) addLog("Erreur conversation: " + e.message);
    return null;
  }
}
