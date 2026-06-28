// src/services/DocumentService.js
// Capture et prepare une photo de document (courrier, formulaire...) pour
// que l'Assistant Document puisse la faire lire/expliquer par Aria.
//
// BRIQUE 1 : capture + compression uniquement. L'envoi vers le proxy
// vision sera ajoute dans une brique suivante.

import * as ImagePicker from "expo-image-picker";
import * as ImageManipulator from "expo-image-manipulator";

// Demande la permission camera. Retourne true/false.
export async function demanderPermissionCamera(addLog) {
  const { status } = await ImagePicker.requestCameraPermissionsAsync();
  if (status !== "granted") {
    if (addLog) addLog("Permission camera refusee.");
    return false;
  }
  return true;
}

// Ouvre l'appareil photo, capture une image, la compresse.
// Retourne { uri, width, height, base64 } ou null si annule/erreur.
export async function prendrePhotoDocument(addLog) {
  try {
    const ok = await demanderPermissionCamera(addLog);
    if (!ok) return null;

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ["images"],
      quality: 1,
    });

    if (result.canceled) {
      if (addLog) addLog("Photo annulee.");
      return null;
    }

    const photo = result.assets[0];

    // Redimensionne (max 1600px de large) + compresse en JPEG,
    // avec le base64 pret a etre envoye dans une prochaine brique.
    const manipule = await ImageManipulator.manipulateAsync(
      photo.uri,
      [{ resize: { width: 1600 } }],
      {
        compress: 0.7,
        format: ImageManipulator.SaveFormat.JPEG,
        base64: true,
      }
    );

    if (addLog) {
      addLog("Photo capturee (" + manipule.width + "x" + manipule.height + ").");
    }

    return {
      uri: manipule.uri,
      width: manipule.width,
      height: manipule.height,
      base64: manipule.base64,
    };
  } catch (e) {
    if (addLog) addLog("Erreur capture photo: " + e.message);
    return null;
  }
}