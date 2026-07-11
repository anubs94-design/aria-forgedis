// src/screens/PairingScreen.js
// Ecran d'appairage : demande l'email du client pour recuperer SON PROPRE
// token via /client-token (meme endpoint que l'installeur Windows utilise
// deja). Sans ca, l'appli utiliserait un token partage et essaierait de
// piloter le PC d'une autre personne : voir DocumentService.js / MainScreen.js.

import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";

import { StorageService } from "../services/StorageService";
import { setProxyToken } from "../services/DocumentService";

const CLIENT_TOKEN_URL = "https://aria-forgelis.onrender.com/client-token";

export default function PairingScreen({ onDone }) {
  const [email, setEmail] = useState("");
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState("");

  const valider = async () => {
    const propre = email.trim().toLowerCase();
    if (!propre || propre.indexOf("@") === -1) {
      setErreur("Merci d'entrer une adresse email valide.");
      return;
    }
    setErreur("");
    setChargement(true);
    try {
      const reponse = await fetch(CLIENT_TOKEN_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: propre }),
      });
      const data = await reponse.json();

      if (data.erreur) {
        setErreur(data.erreur);
        setChargement(false);
        return;
      }
      if (!data.token) {
        setErreur("Impossible de recuperer votre compte. Reessayez.");
        setChargement(false);
        return;
      }

      await StorageService.saveToken(data.token);
      await StorageService.saveAccountEmail(propre);
      if (data.forfait) { await StorageService.saveForfait(data.forfait); }
      setProxyToken(data.token);
      setChargement(false);
      onDone();
    } catch (e) {
      setChargement(false);
      setErreur("Connexion impossible. Verifiez votre internet et reessayez.");
    }
  };

  if (chargement) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#34C759" />
        <Text style={styles.savingText}>Connexion a votre compte Aria...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <Text style={styles.title}>Votre compte Aria</Text>
      <Text style={styles.subtitle}>
        Entrez l'adresse email utilisee lors de votre inscription sur forgedis.fr.
        Cela permet de relier cette appli a votre propre ordinateur.
      </Text>

      <TextInput
        style={styles.input}
        placeholder="votre@email.fr"
        placeholderTextColor="#777"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="email-address"
        onSubmitEditing={valider}
        returnKeyType="done"
      />

      {erreur ? <Text style={styles.erreur}>{erreur}</Text> : null}

      <TouchableOpacity style={styles.bouton} onPress={valider}>
        <Text style={styles.boutonTexte}>Continuer</Text>
      </TouchableOpacity>

      <Text style={styles.note}>
        Pas encore de compte ? Un compte gratuit (Aria Eco) sera cree automatiquement avec cet email.
      </Text>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0A0A0F",
    paddingTop: 90,
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
    marginBottom: 24,
    textAlign: "center",
    lineHeight: 21,
  },
  input: {
    backgroundColor: "#1a1a1f",
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
    color: "#ffffff",
    fontSize: 16,
    marginBottom: 12,
  },
  erreur: {
    color: "#FF7A59",
    fontSize: 14,
    marginBottom: 12,
    textAlign: "center",
  },
  bouton: {
    backgroundColor: "#34C759",
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 8,
  },
  boutonTexte: {
    color: "#0A0A0F",
    fontSize: 17,
    fontWeight: "bold",
  },
  note: {
    color: "#888888",
    fontSize: 13,
    marginTop: 20,
    textAlign: "center",
  },
  savingText: {
    color: "#cccccc",
    fontSize: 14,
    marginTop: 16,
    textAlign: "center",
  },
});