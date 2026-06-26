// src/services/MicroService.js
// Helper pour la reconnaissance vocale native (expo-speech-recognition).
// La reconnaissance se fait directement sur le telephone (moteur natif
// Android/iOS) : pas d'envoi de fichier audio, pas de proxy, pas de
// quota cloud. On recupere directement du texte via les evenements,
// qui sont ecoutes dans MainScreen.js (hooks React).
//
// Ce fichier ne contient que les fonctions non-hook : demander les
// permissions et demarrer/arreter l'ecoute avec la bonne config.

import { ExpoSpeechRecognitionModule } from "expo-speech-recognition";

export async function demanderPermissionMicro(onLog) {
  try {
    const result = await ExpoSpeechRecognitionModule.requestPermissionsAsync();
    if (!result.granted) {
      if (onLog) onLog("Permission micro/reconnaissance refusee.");
      return false;
    }
    return true;
  } catch (e) {
    if (onLog) onLog("Erreur permission micro: " + e.message);
    return false;
  }
}

export function demarrerEcoute(langue) {
  ExpoSpeechRecognitionModule.start({
    lang: langue,
    interimResults: false,
    continuous: false,
    maxAlternatives: 1,
  });
}

export function arreterEcoute() {
  ExpoSpeechRecognitionModule.stop();
}