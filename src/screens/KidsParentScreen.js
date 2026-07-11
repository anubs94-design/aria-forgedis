import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function KidsParentScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Aria Kids ? Espace parent</Text>
      <Text style={styles.sub}>En cours de d?veloppement</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#070B18', alignItems: 'center', justifyContent: 'center' },
  text: { fontFamily: 'Sora', fontSize: 22, fontWeight: '800', color: '#fff', marginBottom: 8 },
  sub: { fontSize: 14, color: '#7A8095' },
});
