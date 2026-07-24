import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native';

export default function PortailScreen({ onChoix }) {
  return (
    <SafeAreaView style={s.container}>
      <Text style={s.logo}>FORGE<Text style={s.logoAccent}>DIS</Text></Text>
      <Text style={s.titre}>Bienvenue</Text>
      <Text style={s.sous}>Choisissez votre espace</Text>
      <TouchableOpacity style={s.card} onPress={() => onChoix('facility')}>
        <Text style={s.cardIcon}>🖥</Text>
        <Text style={s.cardTitre}>Aria Facility</Text>
        <Text style={s.cardDesc}>Pilotage PC par la voix</Text>
      </TouchableOpacity>
      <TouchableOpacity style={[s.card, s.cardKids]} onPress={() => onChoix('kids')}>
        <Text style={s.cardIcon}>📚</Text>
        <Text style={s.cardTitre}>Aria Kids</Text>
        <Text style={s.cardDesc}>Cours, exercices, jeux educatifs</Text>
      </TouchableOpacity>
      <TouchableOpacity style={[s.card, s.cardIndustrial]} onPress={() => onChoix('industrial')}>
        <Text style={s.cardIcon}>🏭</Text>
        <Text style={s.cardTitre}>Aria Industrial</Text>
        <Text style={s.cardDesc}>Gestion entreprise, terrain, postes metier</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0D0F1A', justifyContent: 'center', alignItems: 'center', padding: 24 },
  logo: { fontSize: 24, fontWeight: '800', color: '#FF7A59', marginBottom: 24 },
  logoAccent: { color: '#F0F2FF' },
  titre: { fontSize: 28, fontWeight: '700', color: '#F0F2FF', marginBottom: 6 },
  sous: { fontSize: 15, color: '#7A7FA0', marginBottom: 32 },
  card: { width: '100%', backgroundColor: '#1E2235', borderWidth: 1, borderColor: 'rgba(255,255,255,0.07)', borderRadius: 16, padding: 24, marginBottom: 16, alignItems: 'center' },
  cardKids: { borderColor: 'rgba(124,111,255,0.3)' },
  cardIndustrial: { borderColor: 'rgba(245,166,35,0.3)' },
  cardIcon: { fontSize: 40, marginBottom: 12 },
  cardTitre: { fontSize: 18, fontWeight: '700', color: '#F0F2FF', marginBottom: 6 },
  cardDesc: { fontSize: 13, color: '#7A7FA0', textAlign: 'center' },
});