import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Image } from 'react-native';
import StorageService from '../services/StorageService';

const SUPABASE_URL = 'https://dvlrilklbspuckbplglv.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2bHJpbGtsYnNwdWNrYnBsZ2x2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MDcyNjcsImV4cCI6MjA2NTQ4MzI2N30.qdUCMTAFkRa-FZ4-aJH-FXPI3Ji2Vs30V0bCCKHSFHg';

const COULEURS_PROFIL = ['#FF7A59', '#4A90E2', '#7ED321', '#F5A623'];

const MATIERES_PAR_NIVEAU = {
  'cp': ['Lecture', 'Ecriture', 'Maths', 'Decouverte du monde'],
  'ce1': ['Francais', 'Maths', 'Sciences', 'Histoire'],
  'ce2': ['Francais', 'Maths', 'Sciences', 'Histoire-Geo'],
  'cm1': ['Francais', 'Maths', 'Sciences', 'Histoire-Geo', 'Anglais'],
  'cm2': ['Francais', 'Maths', 'Sciences', 'Histoire-Geo', 'Anglais'],
  '6eme': ['Francais', 'Maths', 'Histoire-Geo', 'SVT', 'Physique', 'Anglais'],
  '5eme': ['Francais', 'Maths', 'Histoire-Geo', 'SVT', 'Physique', 'Anglais', 'Espagnol'],
  '4eme': ['Francais', 'Maths', 'Histoire-Geo', 'SVT', 'Physique', 'Anglais', 'Espagnol'],
  '3eme': ['Francais', 'Maths', 'Histoire-Geo', 'SVT', 'Physique', 'Anglais', 'Espagnol'],
  'seconde': ['Francais', 'Maths', 'Histoire-Geo', 'SVT', 'Physique', 'Anglais', 'SES'],
  'premiere': ['Francais', 'Philo', 'Maths', 'Histoire-Geo', 'Anglais', 'Specialite'],
  'terminale': ['Philo', 'Maths', 'Histoire-Geo', 'Anglais', 'Specialite'],
  'bts': ['Matiere pro', 'Anglais', 'Culture generale'],
};

const MATIERES_VIE_REELLE = [
  'Budget & argent', 'Impots & declarations', 'Droits du travail',
  'Logement & bail', 'Sante & secu', 'Creer une entreprise',
  'Voter & citoyennete', 'Cuisine', 'Code & programmation', 'Musique & arts',
];

const SURPRISES = [
  { id: 'tva', titre: 'A quoi sert la TVA ?', niveau: 'tous' },
  { id: 'budget_base', titre: 'Comment faire un budget ?', niveau: 'tous' },
  { id: 'impots_base', titre: 'Pourquoi paie-t-on des impots ?', niveau: 'tous' },
  { id: 'contrat_travail', titre: 'Un contrat de travail, c est quoi ?', niveau: 'college' },
  { id: 'secu_sociale', titre: 'Comment fonctionne la secu ?', niveau: 'lycee' },
];

export default function KidsScreen() {
  const [profils, setProfils] = useState([]);
  const [profilActif, setProfilActif] = useState(null);
  const [progression, setProgression] = useState(null);
  const [defis, setDefis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [ecran, setEcran] = useState('selection'); // selection | accueil | socrate | passeport

  useEffect(() => { chargerDonnees(); }, []);

  const chargerDonnees = async () => {
    const emailParent = await StorageService.getAccountEmail();
    setEmail(emailParent || '');
    if (!emailParent) { setLoading(false); return; }
    try {
      const r = await fetch(SUPABASE_URL + '/rest/v1/profils_enfants?email_parent=eq.' + emailParent + '&select=*', {
        headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + SUPABASE_KEY }
      });
      const data = await r.json();
      setProfils(data || []);
      if (data && data.length === 1) {
        await selectionnerProfil(data[0]);
      }
    } catch (e) { console.log(e); }
    setLoading(false);
  };

  const selectionnerProfil = async (profil) => {
    setProfilActif(profil);
    const prog = await StorageService.getProgression(profil.id);
    setProgression(prog);
    try {
      const r = await fetch(SUPABASE_URL + '/rest/v1/defis?email_parent=eq.' + email + '&statut=eq.en_cours&select=*', {
        headers: { apikey: SUPABASE_KEY, Authorization: 'Bearer ' + SUPABASE_KEY }
      });
      const data = await r.json();
      setDefis((data || []).filter(function(d) { return !d.profil_id || d.profil_id === profil.id; }));
    } catch (e) { console.log(e); }
    setEcran('accueil');
  };

  if (loading) return <View style={styles.container}><ActivityIndicator color="#FF7A59" size="large" /></View>;

  // ECRAN SELECTION PROFIL
  if (ecran === 'selection' || profils.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.titre}>C'est qui ?</Text>
        <View style={styles.profilsGrid}>
          {profils.map(function(p, idx) { return (
            <TouchableOpacity key={p.id} style={[styles.profilCard, { borderColor: COULEURS_PROFIL[idx % 4] }]} onPress={function() { selectionnerProfil(p); }}>
              <View style={[styles.profilAvatar, { backgroundColor: COULEURS_PROFIL[idx % 4] + '30' }]}>
                <Text style={[styles.profilInitiale, { color: COULEURS_PROFIL[idx % 4] }]}>{p.prenom[0].toUpperCase()}</Text>
              </View>
              <Text style={styles.profilNom}>{p.prenom}</Text>
              <Text style={styles.profilNiveau}>{p.niveau || 'Niveau a definir'}</Text>
            </TouchableOpacity>
          ); })}
          {profils.length === 0 && (
            <View style={styles.videCard}>
              <Text style={styles.videTexte}>Aucun profil enfant.</Text>
              <Text style={styles.videSub}>Demande a un parent de creer ton profil.</Text>
            </View>
          )}
        </View>
      </View>
    );
  }

  // ECRAN ACCUEIL ENFANT
  const matieres = profilActif ? (MATIERES_PAR_NIVEAU[profilActif.niveau] || MATIERES_PAR_NIVEAU['cm2']) : [];
  const surpriseJour = SURPRISES.find(function(s) { return !progression || !(progression.surprises_faites || []).includes(s.id); });
  const points = progression ? (progression.points || 0) : 0;
  const passeport = progression ? (progression.passeport || []) : [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 60 }}>
      <View style={styles.header}>
        <TouchableOpacity onPress={function() { setEcran('selection'); }}>
          <Text style={styles.retour}>? Changer</Text>
        </TouchableOpacity>
        <Text style={styles.bonjour}>Bonjour {profilActif ? profilActif.prenom : ''} !</Text>
        <View style={styles.pointsBadge}>
          <Text style={styles.pointsText}>{points} pts</Text>
        </View>
      </View>

      {/* DEFI EN COURS */}
      {defis.length > 0 && (
        <View style={styles.defiCard}>
          <Text style={styles.defiLabel}>Defi en cours</Text>
          <Text style={styles.defiDesc}>{defis[0].description}</Text>
          <Text style={styles.defiRecompense}>Recompense : {defis[0].recompense}</Text>
        </View>
      )}

      {/* SURPRISE DU JOUR */}
      {surpriseJour && (
        <TouchableOpacity style={styles.surpriseCard} onPress={function() { setEcran('socrate'); }}>
          <Text style={styles.surpriseLabel}>Surprise du jour</Text>
          <Text style={styles.surpriseTitre}>{surpriseJour.titre}</Text>
          <Text style={styles.surpriseSub}>+50 pts bonus si tu la fais !</Text>
        </TouchableOpacity>
      )}

      {/* MATIERES SCOLAIRES */}
      <Text style={styles.section}>Matieres</Text>
      <View style={styles.matieresGrid}>
        {matieres.map(function(m) { return (
          <TouchableOpacity key={m} style={styles.matiereCard} onPress={function() { setEcran('socrate'); }}>
            <Text style={styles.matiereNom}>{m}</Text>
          </TouchableOpacity>
        ); })}
      </View>

      {/* VIE REELLE */}
      <Text style={styles.section}>La vie reelle</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        {MATIERES_VIE_REELLE.map(function(m) { return (
          <TouchableOpacity key={m} style={styles.vieCard} onPress={function() { setEcran('socrate'); }}>
            <Text style={styles.vieNom}>{m}</Text>
          </TouchableOpacity>
        ); })}
      </ScrollView>

      {/* PASSEPORT DE VIE */}
      <TouchableOpacity style={styles.passeportBtn} onPress={function() { setEcran('passeport'); }}>
        <Text style={styles.passeportBtnText}>Mon passeport de vie ? {passeport.length} tampons</Text>
      </TouchableOpacity>

    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#070B18', padding: 16 },
  titre: { fontSize: 32, fontWeight: '800', color: '#fff', textAlign: 'center', marginTop: 60, marginBottom: 40 },
  profilsGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 16 },
  profilCard: { width: 140, backgroundColor: '#0F1626', borderRadius: 20, padding: 20, alignItems: 'center', borderWidth: 2 },
  profilAvatar: { width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  profilInitiale: { fontSize: 28, fontWeight: '800' },
  profilNom: { fontSize: 16, fontWeight: '700', color: '#fff', marginBottom: 4 },
  profilNiveau: { fontSize: 12, color: '#7A8095' },
  videCard: { alignItems: 'center', marginTop: 40 },
  videTexte: { color: '#fff', fontSize: 16, fontWeight: '700', marginBottom: 8 },
  videSub: { color: '#7A8095', fontSize: 13, textAlign: 'center' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 40, marginBottom: 20 },
  retour: { color: '#7A8095', fontSize: 13 },
  bonjour: { fontSize: 18, fontWeight: '800', color: '#fff' },
  pointsBadge: { backgroundColor: '#FF7A5920', borderRadius: 20, paddingHorizontal: 12, paddingVertical: 4, borderWidth: 1, borderColor: '#FF7A59' },
  pointsText: { color: '#FF7A59', fontWeight: '700', fontSize: 13 },
  defiCard: { backgroundColor: '#0F1626', borderRadius: 16, padding: 16, marginBottom: 12, borderLeftWidth: 3, borderLeftColor: '#FF7A59' },
  defiLabel: { fontSize: 11, fontWeight: '700', color: '#FF7A59', marginBottom: 4 },
  defiDesc: { fontSize: 14, color: '#fff', marginBottom: 4 },
  defiRecompense: { fontSize: 12, color: '#7A8095' },
  surpriseCard: { backgroundColor: '#4A90E220', borderRadius: 16, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: '#4A90E2' },
  surpriseLabel: { fontSize: 11, fontWeight: '700', color: '#4A90E2', marginBottom: 4 },
  surpriseTitre: { fontSize: 16, fontWeight: '700', color: '#fff', marginBottom: 4 },
  surpriseSub: { fontSize: 12, color: '#4A90E2' },
  section: { fontSize: 13, fontWeight: '700', color: '#FF7A59', marginBottom: 12, marginTop: 16 },
  matieresGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  matiereCard: { backgroundColor: '#0F1626', borderRadius: 12, paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: '#1E2535' },
  matiereNom: { color: '#fff', fontSize: 13, fontWeight: '600' },
  vieCard: { backgroundColor: '#0F1626', borderRadius: 12, paddingHorizontal: 14, paddingVertical: 10, marginRight: 8, borderWidth: 1, borderColor: '#7ED32130' },
  vieNom: { color: '#7ED321', fontSize: 13, fontWeight: '600' },
  passeportBtn: { backgroundColor: '#0F1626', borderRadius: 16, padding: 16, alignItems: 'center', marginTop: 16, borderWidth: 1, borderColor: '#F5A623' },
  passeportBtnText: { color: '#F5A623', fontWeight: '700', fontSize: 14 },
});
