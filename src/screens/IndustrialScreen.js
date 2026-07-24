import React from "react";
import { View, StyleSheet, ActivityIndicator } from "react-native";
import { WebView } from "react-native-webview";
import { StorageService } from "../services/StorageService";

export default function IndustrialScreen({ onRetour }) {
  const INDUSTRIAL_URL = "https://industrial.forgedis.fr/connexion.html";

  return (
    <View style={s.container}>
      <WebView
        source={{ uri: INDUSTRIAL_URL }}
        style={s.webview}
        startInLoadingState={true}
        renderLoading={() => (
          <View style={s.loading}>
            <ActivityIndicator size="large" color="#F5A623" />
          </View>
        )}
        javaScriptEnabled={true}
        domStorageEnabled={true}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0D0F1A" },
  webview: { flex: 1 },
  loading: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0D0F1A" },
});
