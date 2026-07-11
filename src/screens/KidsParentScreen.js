import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import StorageService from '../services/StorageService';

const SUPABASE_URL = 'https://dvlrilklbspuckbplglv.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2bHJpbGtsYnNwdWNrYnBsZ2x2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MDcyNjcsImV4cCI6MjA2NTQ4MzI2N30.qdUCMTAFkRa-FZ4-aJH-FXPI3Ji2Vs30V0bCCKHSFHg';

const RECOMPENSES = ['Une sortie cinema', '30 min jeux video en plus', 'Un dessert de son choix', 'Une sortie parc', 'Autre...'];

export default function KidsParentScreen() {
  const [profils, setProfils] = useState([]);
  const [profilSelectionne, setProfilSelectionne] = useState(null);
  const [defis, setDefis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [showDefiForm, setShowDefiForm] = useState(false);
  const [defiDescription, setDefiDescription] = useState('');
  const [recompense, setRecompense] = useState('');
  const [pourTous, setPourTous] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => { chargerDonnees(); }, []);

  const chargerDonnees = async () => {
    const emailParent = await StorageService.getAccountEmail();
    setEmail(emailParent || '');
    if (!emailParent) { setLoading(false); return; }
    await chargerProfils(emailParent);
    await chargerDefis(emailParent);
    setLoading(false);
  };

  const chargerProfils = async (emailParent) => {
    try {
      const r = await fetch(SUPABASE_URL + '/rest/v1/profils_enfants?email_parent=eq.' + emailParent + '&select=*', {
        headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + SUPABASE_KEY }
      });
      const data = await r.json();
      setProfils(data || []);
      if (data && data.length > 0) setProfilSelectionne(data[0]);
    } catch (e) { console.log(e); }
  };

  const chargerDefis = async (emailParent) => {
    try {
      const r = await fetch(SUPABASE_URL + '/rest/v1/defis?email_parent=eq.' + emailParent + '&select=*&order=created_at.desc', {
        headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + SUPABASE_KEY }
      });
      const data = await r.json();
      setDefis(data || []);
    } catch (e) { console.log(e); }
  };

  const lancerDefi = async () => {
    if (!defiDescription || !recompense) return;
    setSaving(true);
    try {
      const body = {
        email_parent: email,
        profil_id: pourTous ? null : profilSelectionne ? profilSelectionne.id : null,
        description: defiDescription,
        recompense: recompense,
        statut: 'en_cours',
      };
      await fetch(SUPABASE_URL + '/rest/v1/defis', {
        method: 'POST',
        headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json', Prefer: 'return=minimal' },
        body: JSON.stringify(body),
      });
      setDefiDescription('');
      setRecompense('');
      setShowDefiForm(false);
      await chargerDefis(email);
    } catch (e) { console.log(e); }
    setSaving(false);
  };

  if (loading) return <View style={styles.container}><ActivityIndicator color="#FF7A59" size="large" /></View>;

  const defisEnCours = defis.filter(function(d) { return d.statut === 'en_cours'; });

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      <Text style={styles.titre}>Espace parent</Text>

      <Text style={styles.section}>Choisir un enfant</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }}>
        {profils.map(function(p) { return (
          <TouchableOpacity key={p.id} style={[styles.profilBtn, profilSelectionne && profilSelectionne.id === p.id ? styles.profilBtnActif : null]} onPress={function() { setProfilSelectionne(p); }}>
            <Text style={[styles.profilBtnText, profilSelectionne && profilSelectionne.id === p.id ? styles.profilBtnTextActif : null]}>{p.prenom}</Text>
          </TouchableOpacity>
        ); })}
        {profils.length === 0 && <Text style={styles.muted}>Aucun profil enfant cree</Text>}
      </ScrollView>

      {profilSelectionne && (
        <View style={styles.card}>
          <Text style={styles.cardTitre}>Rapport ? {profilSelectionne.prenom}</Text>
          <View style={styles.statRow}><Text style={styles.statLabel}>Niveau</Text><Text style={styles.statVal}>{profilSelectionne.niveau || 'Non defini'}</Text></View>
          <View style={styles.statRow}><Text style={styles.statLabel}>Taches ce mois</Text><Text style={styles.statVal}>{profilSelectionne.taches_ce_mois || 0}</Text></View>
          <View style={styles.statRow}><Text style={styles.statLabel}>Defis en cours</Text><Text style={styles.statVal}>{defisEnCours.filter(function(d) { return !d.profil_id || d.profil_id === profilSelectionne.id; }).length}</Text></View>
        </View>
      )}

      <Text style={styles.section}>Defis en cours</Text>
      {defisEnCours.length === 0 && <Text style={styles.muted}>Aucun defi en cours</Text>}
      {defisEnCours.map(function(d) { return (
        <View key={d.id} style={styles.defiCard}>
          <Text style={styles.defiDesc}>{d.description}</Text>
          <Text style={styles.defiRecompense}>Recompense : {d.recompense}</Text>
          <Text style={styles.defiCible}>{d.profil_id ? (profils.find(function(p) { return p.id === d.profil_id; }) || {}).prenom || 'Un enfant' : 'Tous les enfants'}</Text>
        </View>
      ); })}

      <TouchableOpacity style={styles.btnDefi} onPress={function() { setShowDefiForm(!showDefiForm); }}>
        <Text style={styles.btnDefiText}>+ Lancer un defi</Text>
      </TouchableOpacity>

      {showDefiForm && (
        <View style={styles.card}>
          <Text style={styles.cardTitre}>Nouveau defi</Text>
          <TouchableOpacity style={[styles.toggleBtn, pourTous ? styles.toggleBtnActif : null]} onPress={function() { setPourTous(!pourTous); }}>
            <Text style={styles.toggleBtnText}>{pourTous ? 'Pour tous les enfants' : 'Pour ' + (profilSelectionne ? profilSelectionne.prenom : 'cet enfant') + ' uniquement'}</Text>
          </TouchableOpacity>
          <TextInput style={styles.input} placeholder="Ex: Faire 5 exercices de maths cette semaine" placeholderTextColor="#7A8095" value={defiDescription} onChangeText={setDefiDescription} multiline />
          <Text style={styles.label}>Recompense :</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 8 }}>
            {RECOMPENSES.map(function(r) { return (
              <TouchableOpacity key={r} style={[styles.recompBtn, recompense === r ? styles.recompBtnActif : null]} onPress={function() { setRecompense(r === 'Autre...' ? '' : r); }}>
                <Text style={[styles.recompBtnText, recompense === r ? styles.recompBtnTextActif : null]}>{r}</Text>
              </TouchableOpacity>
            ); })}
          </ScrollView>
          <TextInput style={styles.input} placeholder="Ou ecrivez votre propre recompense..." placeholderTextColor="#7A8095" value={recompense} onChangeText={setRecompense} />
          <TouchableOpacity style={styles.btnValider} onPress={lancerDefi} disabled={saving}>
            {saving ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnValiderText}>Lancer le defi</Text>}
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#070B18', padding: 16 },
  titre: { fontSize: 24, fontWeight: '800', color: '#fff', marginBottom: 20, marginTop: 40 },
  section: { fontSize: 13, fontWeight: '700', color: '#FF7A59', marginBottom: 8, marginTop: 16 },
  card: { backgroundColor: '#0F1626', borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: '#1E2535' },
  cardTitre: { fontSize: 15, fontWeight: '700', color: '#fff', marginBottom: 12 },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  statLabel: { fontSize: 14, color: '#7A8095' },
  statVal: { fontSize: 14, fontWeight: '600', color: '#fff' },
  profilBtn: { backgroundColor: '#0F1626', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 8, marginRight: 8, borderWidth: 1, borderColor: '#1E2535' },
  profilBtnActif: { backgroundColor: '#FF7A59', borderColor: '#FF7A59' },
  profilBtnText: { color: '#7A8095', fontWeight: '600' },
  profilBtnTextActif: { color: '#fff' },
  defiCard: { backgroundColor: '#0F1626', borderRadius: 12, padding: 12, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: '#FF7A59' },
  defiDesc: { color: '#fff', fontSize: 14, marginBottom: 4 },
  defiRecompense: { color: '#FF7A59', fontSize: 13, marginBottom: 2 },
  defiCible: { color: '#7A8095', fontSize: 12 },
  btnDefi: { backgroundColor: '#FF7A59', borderRadius: 12, padding: 14, alignItems: 'center', marginTop: 8 },
  btnDefiText: { color: '#fff', fontWeight: '800', fontSize: 15 },
  toggleBtn: { backgroundColor: '#1E2535', borderRadius: 8, padding: 10, marginBottom: 12, alignItems: 'center' },
  toggleBtnActif: { backgroundColor: '#1E2535', borderWidth: 1, borderColor: '#FF7A59' },
  toggleBtnText: { color: '#fff', fontSize: 13 },
  input: { backgroundColor: '#1E2535', borderRadius: 10, padding: 12, color: '#fff', fontSize: 14, marginBottom: 12 },
  label: { color: '#7A8095', fontSize: 13, marginBottom: 8 },
  recompBtn: { backgroundColor: '#1E2535', borderRadius: 20, paddingHorizontal: 12, paddingVertical: 6, marginRight: 8, borderWidth: 1, borderColor: '#1E2535' },
  recompBtnActif: { borderColor: '#FF7A59' },
  recompBtnText: { color: '#7A8095', fontSize: 12 },
  recompBtnTextActif: { color: '#FF7A59' },
  btnValider: { backgroundColor: '#FF7A59', borderRadius: 10, padding: 14, alignItems: 'center' },
  btnValiderText: { color: '#fff', fontWeight: '800', fontSize: 14 },
  muted: { color: '#7A8095', fontSize: 13, marginBottom: 8 },
});
