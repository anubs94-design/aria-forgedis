/**
 * RappelService.js — FORGEDIS Aria Facility
 * Gestion des rappels médicaments via relay Render + FCM
 * Fonctionne app fermée grâce aux notifications push FCM
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Notifications from "expo-notifications";

const RELAY_URL = "https://aria-forgelis.onrender.com";
const STORAGE_KEY = "aria_rappels_local";
const EMAIL_KEY = "aria_client_email";

// ── Configuration notifications locales (fallback si FCM indisponible) ──
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// ── Récupérer l'email du client ──
async function getEmail() {
  try {
    return await AsyncStorage.getItem(EMAIL_KEY) || "";
  } catch {
    return "";
  }
}

// ── Enregistrer le token FCM sur le relay ──
export async function enregistrerTokenFCM() {
  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== "granted") {
      console.warn("[RappelService] Permission notifications refusee");
      return false;
    }

    const tokenData = await Notifications.getExpoPushTokenAsync();
    const token = tokenData.data;
    const email = await getEmail();

    if (!email || !token) return false;

    const r = await fetch(`${RELAY_URL}/enregistrer-token-fcm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, token_fcm: token, plateforme: "android" }),
    });
    const data = await r.json();
    return data.ok === true;
  } catch (e) {
    console.warn("[RappelService] Erreur enregistrement FCM:", e);
    return false;
  }
}

// ── Charger les rappels depuis le relay (avec fallback local) ──
export async function chargerRappels() {
  const email = await getEmail();

  // Essayer le relay d'abord
  if (email) {
    try {
      const r = await fetch(`${RELAY_URL}/rappels/liste?email=${encodeURIComponent(email)}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      const data = await r.json();
      if (data.rappels) {
        // Mettre en cache local
        await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(data.rappels));
        return data.rappels;
      }
    } catch {
      // Fallback sur cache local si réseau indisponible
    }
  }

  // Fallback local
  try {
    const local = await AsyncStorage.getItem(STORAGE_KEY);
    return local ? JSON.parse(local) : [];
  } catch {
    return [];
  }
}

// ── Créer un rappel ──
export async function creerRappel(nom, heure, minute, jours = "quotidien") {
  const email = await getEmail();

  // Convertir "quotidien" en tableau de jours
  const joursArray = jours === "quotidien"
    ? ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    : Array.isArray(jours) ? jours : [jours];

  const heureStr = `${String(heure).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;

  try {
    // Créer sur le relay
    if (email) {
      const r = await fetch(`${RELAY_URL}/rappels/ajouter`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          nom,
          heure: heureStr,
          jours: joursArray,
        }),
      });
      const data = await r.json();
      if (data.ok) {
        // Programmer aussi une notification locale en backup
        await _programmerNotificationLocale(data.rappel?.id || nom, nom, heure, minute);
        return data.rappel;
      }
    }
  } catch (e) {
    console.warn("[RappelService] Relay indisponible, rappel local uniquement:", e);
  }

  // Fallback : notification locale uniquement
  const rappelLocal = {
    id: `local_${Date.now()}`,
    nom,
    heure: heureStr,
    jours: joursArray,
    actif: true,
  };
  await _programmerNotificationLocale(rappelLocal.id, nom, heure, minute);

  // Sauvegarder en local
  const existants = await chargerRappels();
  existants.push(rappelLocal);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(existants));
  return rappelLocal;
}

// ── Programmer une notification locale (backup si FCM indisponible) ──
async function _programmerNotificationLocale(id, nom, heure, minute) {
  try {
    await Notifications.scheduleNotificationAsync({
      identifier: String(id),
      content: {
        title: "⏰ Rappel Aria",
        body: `Il est l'heure de prendre ${nom}`,
        sound: true,
        data: { type: "rappel", nom },
      },
      trigger: {
        hour: parseInt(heure, 10),
        minute: parseInt(minute, 10),
        repeats: true,
      },
    });
  } catch (e) {
    console.warn("[RappelService] Erreur notification locale:", e);
  }
}

// ── Supprimer un rappel ──
export async function supprimerRappel(id) {
  const email = await getEmail();

  // Annuler la notification locale
  try {
    await Notifications.cancelScheduledNotificationAsync(String(id));
  } catch {}

  // Supprimer sur le relay
  if (email) {
    try {
      await fetch(`${RELAY_URL}/rappels/supprimer`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, id }),
      });
    } catch {}
  }

  // Mettre à jour le cache local
  const rappels = await chargerRappels();
  const restants = rappels.filter((r) => r.id !== id);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(restants));
  return restants;
}

// ── Confirmer la prise d'un médicament ──
export async function confirmerPrise(rappelId, confirme = true) {
  const email = await getEmail();
  if (!email) return;

  try {
    await fetch(`${RELAY_URL}/rappels/confirmer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, rappel_id: rappelId, confirme }),
    });
  } catch (e) {
    console.warn("[RappelService] Erreur confirmation:", e);
  }
}

// ── Formater l'heure pour l'affichage ──
export function formaterHeure(heure, minute) {
  return `${String(heure).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

// ── Initialisation au démarrage de l'app ──
export async function initialiserRappels() {
  await enregistrerTokenFCM();
}
