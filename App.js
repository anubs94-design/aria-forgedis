// App.js
// Point d'entree de l'application. Verifie si l'onboarding a deja
// ete fait : si oui, affiche directement MainScreen ; sinon, affiche
// OnboardingScreen puis bascule vers MainScreen une fois termine.

import React, { useState, useEffect } from "react";
import { View, ActivityIndicator, StyleSheet } from "react-native";

import MainScreen from "./src/screens/MainScreen";
import OnboardingScreen from "./src/screens/OnboardingScreen";
import { StorageService } from "./src/services/StorageService";

export default function App() {
  const [chargement, setChargement] = useState(true);
  const [onboardingFait, setOnboardingFait] = useState(false);

  useEffect(() => {
    StorageService.isOnboardingDone().then((fait) => {
      setOnboardingFait(fait);
      setChargement(false);
    });
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