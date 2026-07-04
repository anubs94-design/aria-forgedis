// App.js
// Point d'entree de l'application. Verifie si l'onboarding a deja
// ete fait : si oui, affiche directement MainScreen ; sinon, affiche
// OnboardingScreen puis bascule vers MainScreen une fois termine.

import React, { useState, useEffect } from "react";
import { View, ActivityIndicator, StyleSheet } from "react-native";

import MainScreen from "./src/screens/MainScreen";
import OnboardingScreen from "./src/screens/OnboardingScreen";
import PairingScreen from "./src/screens/PairingScreen";
import { StorageService } from "./src/services/StorageService";
import { setProxyToken } from "./src/services/DocumentService";

export default function App() {
  const [chargement, setChargement] = useState(true);
  const [onboardingFait, setOnboardingFait] = useState(false);
  const [appairageFait, setAppairageFait] = useState(false);

  useEffect(() => {
    (async () => {
      const fait = await StorageService.isOnboardingDone();
      const token = await StorageService.getToken();
      if (token) {
        setProxyToken(token);
      }
      setOnboardingFait(fait);
      setAppairageFait(!!token);
      setChargement(false);
    })();
  }, []);

  if (chargement) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#34C759" />
      </View>
    );
  }

  if (!onboardingFait) {
    return <OnboardingScreen onDone={() => setOnboardingFait(true)} />;
  }

  if (!appairageFait) {
    return <PairingScreen onDone={() => setAppairageFait(true)} />;
  }

  return <MainScreen />;
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    backgroundColor: "#0A0A0F",
    justifyContent: "center",
    alignItems: "center",
  },
});