/**
 * VeilleFamilleService.js — FORGEDIS Aria Facility
 * Surveillance proactive + logs activité + rapport quotidien famille
 * Aria veille même quand le client ne lui parle pas
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Notifications from "expo-notifications";
import * as BackgroundFetch from "expo-background-fetch";
import * as TaskManager from "expo-task-manager";

const RELAY_URL = "https://aria-forgelis.onrender.com";
const EMAIL_KEY = "aria_client_email";
const PROCHE_KEY = "aria_proche_email";
const PROCHE_NOM_KEY = "aria_proche_nom";
const DERNIERE_ACTIVITE_KEY = "aria_derniere_activite";

const TASK_RAPPORT = "aria-rapport-quotidien";
const TASK_VEILLE = "aria-veille-inactivite";

// ── Récupérer l'email du client ──
async function getEmail() {
  try {
    return (await AsyncStorage.getItem(EMAIL_KEY)) || "";
  } catch {
    return "";
  }
}

// ── Récupérer / définir le proche de confiance ──
export async function getProche() {
  try {
    const email = await AsyncStorage.getItem(PROCHE_KEY);
    const nom = await AsyncStorage.getItem(PROCHE_NOM_KEY);
    return { email: email || "", nom: nom || "" };
  } catch {
    return { email: "", nom: "" };
  }
}

export async function setProche(emailFamille, prenomFamille = "") {
  try {
    await AsyncStorage.setItem(PROCHE_KEY, emailFamille);
    await AsyncStorage.setItem(PROCHE_NOM_KEY, prenomFamille);

    // Enregistrer sur le relay aussi
    const emailClient = await getEmail();
    if (emailClient) {
      await fetch(`${RELAY_URL}/famille/enregistrer-contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email_client: emailClient,
          email_famille: emailFamille,
          prenom_famille: prenomFamille,
        }),
      });
    }
    return true;
  } catch (e) {
    console.warn("[VeilleFamille] Erreur setProche:", e);
    return false;
  }
}

// ── Logger une activité (appelé par MainScreen après chaque action) ──
export async function logActivite(type, description = "") {
  // Mettre à jour l'horodatage de dernière activité
  try {
    await AsyncStorage.setItem(DERNIERE_ACTIVITE_KEY, new Date().toISOString());
  } catch {}

  // Envoyer au relay en arrière-plan
  const email = await getEmail();
  if (!email) return;

  try {
    fetch(`${RELAY_URL}/log-activite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, type, description }),
    }).catch(() => {}); // Non bloquant
  } catch {}
}

// ── Envoyer le rapport quotidien manuellement ──
export async function partagerRapport() {
  const email = await getEmail();
  if (!email) {
    return { ok: false, message: "Email client non configuré" };
  }

  try {
    const r = await fetch(`${RELAY_URL}/famille/rapport-quotidien`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_client: email }),
    });
    const data = await r.json();
    return data;
  } catch (e) {
    return { ok: false, message: "Erreur réseau: " + e.message };
  }
}

// ── Vérifier l'inactivité et alerter la famille si besoin ──
async function verifierInactivite() {
  const email = await getEmail();
  if (!email) return;

  try {
    // Vérifier localement d'abord
    const derniereActivite = await AsyncStorage.getItem(DERNIERE_ACTIVITE_KEY);
    if (derniereActivite) {
      const diff = (Date.now() - new Date(derniereActivite).getTime()) / (1000 * 60 * 60);
      if (diff < 20) return; // Moins de 20h — pas d'alerte
    }

    // Demander au relay de vérifier et alerter
    await fetch(`${RELAY_URL}/famille/alerte-inactivite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_client: email, heures: 24 }),
    });
  } catch {}
}

// ── Définir la tâche de fond — rapport quotidien ──
TaskManager.defineTask(TASK_RAPPORT, async () => {
  try {
    const email = await getEmail();
    if (!email) return BackgroundFetch.BackgroundFetchResult.NoData;

    await fetch(`${RELAY_URL}/famille/rapport-quotidien`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_client: email }),
    });
    return BackgroundFetch.BackgroundFetchResult.NewData;
  } catch {
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

// ── Définir la tâche de fond — veille inactivité ──
TaskManager.defineTask(TASK_VEILLE, async () => {
  try {
    await verifierInactivite();
    return BackgroundFetch.BackgroundFetchResult.NewData;
  } catch {
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

// ── Programmer le rapport quotidien et la veille ──
export async function programmerRappelRapport() {
  try {
    // Rapport quotidien — toutes les 24h
    await BackgroundFetch.registerTaskAsync(TASK_RAPPORT, {
      minimumInterval: 24 * 60 * 60, // 24h en secondes
      stopOnTerminate: false,
      startOnBoot: true,
    });

    // Veille inactivité — toutes les 6h
    await BackgroundFetch.registerTaskAsync(TASK_VEILLE, {
      minimumInterval: 6 * 60 * 60, // 6h en secondes
      stopOnTerminate: false,
      startOnBoot: true,
    });

    // Notification locale à 20h comme backup
    await Notifications.scheduleNotificationAsync({
      identifier: "aria-rapport-20h",
      content: {
        title: "📊 Rapport Aria envoyé",
        body: "Le rapport quotidien a été envoyé à votre proche.",
        sound: false,
      },
      trigger: {
        hour: 20,
        minute: 0,
        repeats: true,
      },
    });
  } catch (e) {
    console.warn("[VeilleFamille] Erreur programmation tâches:", e);
  }
}

// ── Initialisation complète ──
export async function initialiserVeilleFamille() {
  await programmerRappelRapport();
  // Logger le démarrage de l'app
  await logActivite("app_ouverte", "Aria démarrée");
}
