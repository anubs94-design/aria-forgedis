// src/screens/OnboardingScreen.js
// Premier ecran vu par le client : choix de la langue et du mode
// d'interaction (vocal / vocal+ecrit / ecrit). Stocke le profil via
// StorageService, puis appelle onDone() pour passer a l'app principale.

import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";

import { StorageService } from "../services/StorageService";
import { ClientService } from "../services/ClientService";
import { COMMUNICATION_MODES } from "../constants/theme";

const LANGUES = [
  { code: "fr-FR", label: "Francais" },
  { code: "en-US", label: "English" },
  { code: "es-ES", label: "Espanol" },
];

const MODES = [
  { value: COMMUNICATION_MODES.VOCAL, label: "Vocal uniquement", description: "Je parle, Aria me repond a voix haute" },
  { value: COMMUNICATION_MODES.VOCAL_ECRIT, label: "Vocal et ecrit", description: "Je peux parler ou ecrire, Aria me repond des deux facons" },
  { value: COMMUNICATION_MODES.ECRIT, label: "Ecrit uniquement", description: "J'ecris mes demandes, Aria repond par ecrit" },
];

export default function OnboardingScreen({ onDone }) {
  const [step, setStep] = useState(1);
  const [langue, setLangue] = useState(null);
  const [mode, setMode] = useState(null);
  const [saving, setSaving] = useState(false);

  const choisirLangue = (code) => {
    setLangue(code);
    setStep(2);
  };

  const choisirMode = async (value) => {
    setMode(value);
    setSaving(true);

    await ClientService.getOrCreateClientId();
    await StorageService.saveProfile({ langue, mode: value });
    await StorageService.setOnboardingDone();

    setSaving(false);
    onDone({ langue, mode: value });
  };

  if (saving) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#34C759" />
        <Text style={styles.savingText}>Preparation d Aria...</Text>
      </View>
    );
  }

  if (step === 1) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Bienvenue</Text>
        <Text style={styles.subtitle}>Dans quelle langue souhaitez-vous parler avec Aria ?</Text>

        {LANGUES.map((l) => (
          <TouchableOpacity
            key={l.code}
            style={styles.optionButton}
            onPress={() => choisirLangue(l.code)}
          >
            <Text style={styles.optionLabel}>{l.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Comment voulez-vous parler a Aria ?</Text>

      {MODES.map((m) => (
        <TouchableOpacity
          key={m.value}
          style={styles.optionButtonLarge}
          onPress={() => choisirMode(m.value)}
        >
          <Text style={styles.optionLabel}>{m.label}</Text>
          <Text style={styles.optionDescription}>{m.description}</Text>
        </TouchableOpacity>
      ))}

      <TouchableOpacity style={styles.backButton} onPress={() => setStep(1)}>
        <Text style={styles.backButtonText}>Retour</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0A0A0F",
    paddingTop: 80,
    paddingHorizontal: 24,
    alignItems: "stretch",
  },
  title: {
    color: "#ffffff",
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 12,
    textAlign: "center",
  },
  subtitle: {
    color: "#cccccc",
    fontSize: 15,
    marginBottom: 32,
    textAlign: "center",
  },
  optionButton: {
    backgroundColor: "#1a1a1f",
    borderRadius: 10,
    paddingVertical: 18,
    paddingHorizontal: 20,
    marginBottom: 12,
    alignItems: "center",
  },
  optionButtonLarge: {
    backgroundColor: "#1a1a1f",
    borderRadius: 10,
    paddingVertical: 20,
    paddingHorizontal: 20,
    marginBottom: 14,
  },
  optionLabel: {
    color: "#ffffff",
    fontSize: 17,
    fontWeight: "bold",
    marginBottom: 4,
  },
  optionDescription: {
    color: "#999999",
    fontSize: 13,
  },
  backButton: {
    marginTop: 12,
    alignItems: "center",
    paddingVertical: 10,
  },
  backButtonText: {
    color: "#888888",
    fontSize: 14,
  },
  savingText: {
    color: "#cccccc",
    fontSize: 14,
    marginTop: 16,
    textAlign: "center",
  },
});