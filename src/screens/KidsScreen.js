import React from 'react';
import { View, StyleSheet, SafeAreaView, ActivityIndicator, Text, TouchableOpacity } from 'react-native';
import { WebView } from 'react-native-webview';

export default function KidsScreen({ token, onRetour }) {
  const url = 'https://forgedis.fr/app-kids.html?token=' + encodeURIComponent(token || '') + '&forfait=kids_famille';
  return (
    <SafeAreaView style={s.container}>
      {onRetour && (
        <TouchableOpacity style={s.back} onPress={onRetour}>
          <Text style={s.backText}>{'? Retour au portail'}</Text>
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
  back: { padding: 12, paddingHorizontal: 20, backgroundColor: '#161928', borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.07)' },
  backText: { color: '#7C6FFF', fontSize: 14, fontWeight: '600' },
  load: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0D0F1A' },
  loadText: { color: '#7A7FA0', fontSize: 14, marginTop: 12 },
});
