// src/services/RappelService.js
// Gestion des rappels medicaments/RDV — notifications locales
// Stockage local (AsyncStorage), fonctionne hors ligne et app fermee.

import * as Notifications from "expo-notifications";
import AsyncStorage from "@react-native-async-storage/async-storage";

const STORAGE_KEY = "aria_rappels";

// Configure le comportement des notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Charge tous les rappels depuis le stockage local
export async function chargerRappels() {
  try {
    const data = await AsyncStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch (e) {
    return [];
  }
}

// Sauvegarde la liste des rappels
async function sauverRappels(rappels) {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(rappels));
}

// Demande la permission pour les notifications
export async function demanderPermissionNotifications() {
  const { status } = await Notifications.requestPermissionsAsync();
  return status === "granted";
}

// Cree un rappel et programme la notification
export async function creerRappel(nom, heure, minute, recurrence) {
  const ok = await demanderPermissionNotifications();
  if (!ok) return null;

  // Programme la notification locale
  const trigger = {
    type: "daily",
    hour: heure,
    minute: minute,
  };

  const notifId = await Notifications.scheduleNotificationAsync({
    content: {
      title: "Rappel Aria",
      body: nom,
      sound: true,
    },
    trigger: trigger,
  });

  const rappel = {
    id: notifId,
    nom: nom,
    heure: heure,
    minute: minute,
    recurrence: recurrence || "quotidien",
    actif: true,
    cree: new Date().toISOString(),
  };

  const rappels = await chargerRappels();
  rappels.push(rappel);
  await sauverRappels(rappels);

  return rappel;
}

// Supprime un rappel et annule sa notification
export async function supprimerRappel(id) {
  try {
    await Notifications.cancelScheduledNotificationAsync(id);
  } catch (e) {}
  const rappels = await chargerRappels();
  const filtres = rappels.filter(r => r.id !== id);
  await sauverRappels(filtres);
  return filtres;
}

// Formate l'heure pour l'affichage
export function formaterHeure(h, m) {
  return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0");
}
