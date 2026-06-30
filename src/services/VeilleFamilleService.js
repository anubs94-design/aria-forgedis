// src/services/VeilleFamilleService.js
// Veille famille : log d'activite Aria + rapport partageable avec un proche.
// Tout reste local (AsyncStorage). Zero stockage tiers.

import AsyncStorage from "@react-native-async-storage/async-storage";
import { Share } from "react-native";

const STORAGE_PROCHE = "aria_proche";
const STORAGE_ACTIVITE = "aria_activite_log";
const MAX_LOGS = 100;

// --- Proche designe ---
export async function getProche() {
  try {
    const data = await AsyncStorage.getItem(STORAGE_PROCHE);
    return data ? JSON.parse(data) : null;
  } catch (e) { return null; }
}

export async function setProche(nom, telephone) {
  await AsyncStorage.setItem(STORAGE_PROCHE, JSON.stringify({ nom, telephone }));
}

// --- Log d'activite ---
export async function logActivite(action) {
  try {
    const data = await AsyncStorage.getItem(STORAGE_ACTIVITE);
    const logs = data ? JSON.parse(data) : [];
    logs.push({
      action: action,
      date: new Date().toISOString(),
    });
    // Garde les 100 derniers
    const trimmed = logs.slice(-MAX_LOGS);
    await AsyncStorage.setItem(STORAGE_ACTIVITE, JSON.stringify(trimmed));
  } catch (e) {}
}

export async function getActivites() {
  try {
    const data = await AsyncStorage.getItem(STORAGE_ACTIVITE);
    return data ? JSON.parse(data) : [];
  } catch (e) { return []; }
}

// --- Rapport ---
export async function genererRapport() {
  const logs = await getActivites();
  const proche = await getProche();
  const aujourdhui = new Date().toLocaleDateString("fr-FR", {
    weekday: "long", year: "numeric", month: "long", day: "numeric"
  });

  let rapport = "Rapport Aria - " + aujourdhui + "\n\n";

  if (logs.length === 0) {
    rapport += "Aucune activite enregistree recemment.\n";
  } else {
    const recents = logs.slice(-20);
    for (const log of recents) {
      const d = new Date(log.date);
      const heure = d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
      rapport += heure + " - " + log.action + "\n";
    }
  }

  rapport += "\n-- Envoye par Aria (FORGEDIS)";
  return rapport;
}

// Programme une notification quotidienne a 20h pour rappeler d'envoyer le rapport
export async function programmerRappelRapport() {
  try {
    const Notifications = require("expo-notifications");
    // Annule l'ancien rappel rapport s'il existe
    await Notifications.cancelAllScheduledNotificationsAsync();
    // Reprogramme (on reprogramme aussi les rappels medicaments via RappelService)
    await Notifications.scheduleNotificationAsync({
      content: {
        title: "Rapport Aria du jour",
        body: "Voulez-vous envoyer le rapport d'activite a votre proche ?",
        sound: true,
      },
      trigger: {
        type: "daily",
        hour: 20,
        minute: 0,
      },
    });
    return true;
  } catch (e) {
    return false;
  }
}

export async function partagerRapport() {
  const rapport = await genererRapport();
  try {
    await Share.share({
      message: rapport,
      title: "Rapport Aria",
    });
    return true;
  } catch (e) {
    return false;
  }
}
