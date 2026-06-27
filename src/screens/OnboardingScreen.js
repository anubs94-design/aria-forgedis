// src/screens/OnboardingScreen.js
// Premier ecran vu par le client : choix de la langue.
//
// Cascade :
//   Ecran 1 = langues principales (vocales) + "Arabe +" + "Autres (ecrit)"
//   Ecran 2a (Arabe +) = dialectes arabes, tous vocaux
//   Ecran 2b (Autres ecrit) = langues sans reco vocale (ecrit seulement)
//
// Chaque langue porte un statut "vocal" :
//   vocal = true  -> micro actif dans MainScreen
//   vocal = false -> clavier seul (langue ecrit-seulement)
//
// Stocke { langue, vocal } via StorageService, puis appelle onDone().

import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from "react-native";

import { StorageService } from "../services/StorageService";
import { ClientService } from "../services/ClientService";

// --- Langues principales (vocales) ---
const LANGUES = [
  { code: "fr-FR", label: "Francais" },
  { code: "en-US", label: "English" },
  { code: "es-ES", label: "Espanol" },
  { code: "pt-BR", label: "Portugues" },
  { code: "cmn-Hans-CN", label: "Chinois" },
  { code: "hi-IN", label: "Hindi" },
  { code: "de-DE", label: "Deutsch" },
  { code: "it-IT", label: "Italiano" },
  { code: "ru-RU", label: "Russe" },
  { code: "tr-TR", label: "Turc" },
  { code: "pl-PL", label: "Polski" },
  { code: "ja-JP", label: "Japonais" },
];

// --- Dialectes arabes (tous vocaux) ---
const ARABE = [
  { code: "ar-DZ", label: "Arabe - Algerie" },
  { code: "ar-MA", label: "Arabe - Maroc" },
  { code: "ar-TN", label: "Arabe - Tunisie" },
  { code: "ar-EG", label: "Arabe - Egypte" },
  { code: "ar-SA", label: "Arabe - standard / Golfe" },
  { code: "ar-AE", label: "Arabe - Emirats" },
  { code: "ar-LB", label: "Arabe - Liban" },
  { code: "ar-SY", label: "Arabe - Syrie" },
  { code: "ar-JO", label: "Arabe - Jordanie" },
  { code: "ar-IQ", label: "Arabe - Irak" },
];

// --- Langues ecrit seulement (pas de reco vocale) ---
const ECRIT = [
  { code: "kab", label: "Kabyle (Tizi Ouzou)" },
  { code: "gcf", label: "Creole antillais" },
  { code: "rcf", label: "Creole reunionnais" },
  { code: "ht", label: "Creole haitien" },
  { code: "oc", label: "Occitan" },
  { code: "br", label: "Breton" },
  { code: "co", label: "Corse" },
  { code: "eu", label: "Basque" },
];

export default function OnboardingScreen({ onDone }) {
  const [ecran, setEcran] = useState("principal");
  const [saving, setSaving] = useState(false);

  const choisir = async (code, vocal) => {
    setSaving(true);
    await ClientService.getOrCreateClientId();
    await StorageService.saveProfile({ langue: code, vocal: vocal });
    await StorageService.setOnboardingDone();
    setSaving(false);
    onDone({ langue: code, vocal: vocal });
  };

  if (saving) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#34C759" />
        <Text style={styles.savingText}>Preparation d Aria...</Text>
      </View>
    );
  }

  // --- Ecran 2a : dialectes arabes ---
  if (ecran === "arabe") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Quel arabe parlez-vous ?</Text>
        <ScrollView style={styles.scroll}>
          {ARABE.map((l) => (
            <TouchableOpacity
              key={l.code}
              style={styles.optionButton}
              onPress={() => choisir(l.code, true)}
            >
              <Text style={styles.optionLabel}>{l.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
        <TouchableOpacity style={styles.backButton} onPress={() => setEcran("principal")}>
          <Text style={styles.backButtonText}>Retour</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // --- Ecran 2b : langues ecrit seulement ---
  if (ecran === "ecrit") {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Langues a l ecrit</Text>
        <Text style={styles.subtitle}>
          Ces langues fonctionnent au clavier. La voix n est pas encore disponible.
        </Text>
        <ScrollView style={styles.scroll}>
          {ECRIT.map((l) => (
            <TouchableOpacity
              key={l.code}
              style={styles.optionButton}
              onPress={() => choisir(l.code, false)}
            >
              <Text style={styles.optionLabel}>{l.label}</Text>
              <Text style={styles.optionTag}>ecrit seulement</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
        <TouchableOpacity style={styles.backButton} onPress={() => setEcran("principal")}>
          <Text style={styles.backButtonText}>Retour</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // --- Ecran 1 : langues principales ---
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Bienvenue</Text>
      <Text style={styles.subtitle}>Dans quelle langue voulez-vous parler avec Aria ?</Text>
      <ScrollView style={styles.scroll}>
        {LANGUES.map((l) => (
          <TouchableOpacity
            key={l.code}
            style={styles.optionButton}
            onPress={() => choisir(l.code, true)}
          >
            <Text style={styles.optionLabel}>{l.label}</Text>
          </TouchableOpacity>
        ))}

        <TouchableOpacity
          style={[styles.optionButton, styles.optionSpecial]}
          onPress={() => setEcran("arabe")}
        >
          <Text style={styles.optionLabel}>Arabe +</Text>
          <Text style={styles.optionTag}>choisir le dialecte</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.optionButton, styles.optionSpecial]}
          onPress={() => setEcran("ecrit")}
        >
          <Text style={styles.optionLabel}>Autres langues</Text>
          <Text style={styles.optionTag}>kabyle, creole... (ecrit)</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0A0A0F",
    paddingTop: 70,
    paddingHorizontal: 24,
  },
  center: {
    flex: 1,
    backgroundColor: "#0A0A0F",
    justifyContent: "center",
    alignItems: "center",
  },
  title: {
    color: "#ffffff",
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 10,
    textAlign: "center",
  },
  subtitle: {
    color: "#cccccc",
    fontSize: 15,
    marginBottom: 20,
    textAlign: "center",
  },
  scroll: {
    flex: 1,
  },
  optionButton: {
    backgroundColor: "#1a1a1f",
    borderRadius: 10,
    paddingVertical: 16,
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  optionSpecial: {
    backgroundColor: "#1f1a2a",
    borderLeftWidth: 3,
    borderLeftColor: "#FF9500",
  },
  optionLabel: {
    color: "#ffffff",
    fontSize: 17,
    fontWeight: "bold",
  },
  optionTag: {
    color: "#999999",
    fontSize: 12,
    marginTop: 3,
  },
  backButton: {
    paddingVertical: 14,
    alignItems: "center",
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