// src/services/MicroService.js
// Gere les permissions micro et l'envoi de l'audio enregistre
// vers le proxy Render pour transcription (Google Speech-to-Text).
// La capture elle-meme (useAudioRecorder) reste dans MainScreen.js
// car c'est un hook React, qui ne peut pas vivre dans un service pur.

import * as FileSystem from "expo-file-system";

const TRANSCRIBE_URL = "https://aria-forgelis.onrender.com/transcribe";

export async function lireAudioEnBase64(uri) {
  const base64 = await FileSystem.readAsStringAsync(uri, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return base64;
}

export async function transcrireAudio(uri, langue, proxyToken, onLog) {
  try {
    const base64Audio = await lireAudioEnBase64(uri);

    const response = await fetch(TRANSCRIBE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: proxyToken,
        audio: base64Audio,
        langue: langue,
      }),
    });

    const data = await response.json();

    if (data.erreur) {
      if (onLog) onLog("Erreur transcription: " + data.erreur);
      return null;
    }

    return data.texte || null;
  } catch (e) {
    if (onLog) onLog("Erreur reseau transcription: " + e.message);
    return null;
  }
}