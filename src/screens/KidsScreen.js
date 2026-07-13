import React, { useState, useEffect } from 'react';
import { View, StyleSheet, SafeAreaView, ActivityIndicator, Text, TouchableOpacity } from 'react-native';
import { WebView } from 'react-native-webview';
import StorageService from '../services/StorageService';

export default function KidsScreen({ onRetour }) {
  const [token, setToken] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const t = await StorageService.getToken();
        setToken(t || '');
      } catch (e) {
        setToken('');
      }
      setReady(true);
    })();
  }, []);

  if (!ready) {
    return (
      <View style={s.load}>
        <ActivityIndicator size="large" color="#7C6FFF" />
      </View>
    );
  }

  const url = 'https://forgedis.fr/app-kids.html?token=' + encodeURIComponent(token || '') + '&forfait=kids_famille';

  return (
    <SafeAreaView style={s.container}>
      {onRetour && (
        <TouchableOpacity style={s.back} onPress={onRetour}>
          <Text style={s.backText}>{'\u2190 Retour au portail'}</Text>
        </TouchableOpacity>
      )}
      <WebView
        source={{ uri: url }}
        style={s.wv}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={true}
        renderLoading={() => (
          <View style={s.load}>
            <ActivityIndicator size="large" color="#7C6FFF" />
            <Text style={s.loadText}>Chargement Aria Kids...</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0D0F1A' },
  wv: { flex: 1 },
  back: { padding: 12, paddingHorizontal: 20, backgroundColor: '#161928' },
  backText: { color: '#7C6FFF', fontSize: 14, fontWeight: '600' },
  load: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0D0F1A' },
  loadText: { color: '#7A7FA0', fontSize: 14, marginTop: 12 },
});
