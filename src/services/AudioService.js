// src/services/AudioService.js
// Joue l'audio TTS (voix d'Aria) recu en base64 depuis le PC.
// File d'attente : un seul audio a la fois, les suivants attendent.

import { Audio } from "expo-av";

let fileAudio = [];
let estEntrain = false;

async function jouerProchain(onLog) {
  if (estEntrain || fileAudio.length === 0) return;
  estEntrain = true;
  const base64Audio = fileAudio.shift();
  try {
    const { sound } = await Audio.Sound.createAsync(
      { uri: "data:audio/mp3;base64," + base64Audio }
    );
    await new Promise((resolve) => {
      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.didJustFinish) {
          sound.unloadAsync();
          resolve();
        }
      });
      sound.playAsync();
    });
  } catch (e) {
    if (onLog) onLog("Erreur lecture audio: " + e.message);
  } finally {
    estEntrain = false;
    jouerProchain(onLog);
  }
}

export async function jouerAudio(base64Audio, onLog) {
  fileAudio.push(base64Audio);
  jouerProchain(onLog);
}