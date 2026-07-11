import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Image, TextInput } from 'react-native';
import { parlerKids } from '../services/ConversationService';
import * as ImagePicker from 'expo-image-picker';
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
  const [ecran, setEcran] = useState('selection');
  const [matiereActive, setMatiereActive] = useState('');
  const [session, setSession] = useState([]);
  const [inputText, setInputText] = useState('');
  const [envoiEnCours, setEnvoiEnCours] = useState(false);
  const [sessionRef, setSessionRef] = useState([]); // selection | accueil | socrate | passeport

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

  const ouvrirMatiere = async (matiere) => {
    setMatiereActive(matiere);
    const sess = await StorageService.getSession(profilActif.id + '_' + matiere);
    setSession(sess);
    setEcran('socrate');
  };

  const envoyerMessage = async (texte) => {
    if (!texte || !texte.trim() || envoiEnCours) return;
    const token = await StorageService.getToken();
    const newSession = [...session, { role: 'user', content: texte }];
    setSession(newSession);
    setInputText('');
    setEnvoiEnCours(true);
    const rep = await parlerKids(texte, session, profilActif.niveau || 'cm2', matiereActive, token);
    if (rep) {
      const finalSession = [...newSession, { role: 'assistant', content: rep }];
      setSession(finalSession);
      await StorageService.saveSession(profilActif.id + '_' + matiereActive, finalSession);
      const prog = await StorageService.getProgression(profilActif.id);
      const newProg = Object.assign({}, prog, { points: (prog.points || 0) + 10, sessions_count: (prog.sessions_count || 0) + 1 });
      await StorageService.saveProgression(profilActif.id, newProg);
      setProgression(newProg);
    }
    setEnvoiEnCours(false);
  };

  const scannerDevoir = async () => {
    const result = await ImagePicker.launchCameraAsync({ base64: true, quality: 0.7 });
    if (!result.canceled && result.assets[0]) {
      setEnvoiEnCours(true);
      await envoyerMessage('Voici mon devoir, aide-moi a le comprendre sans me donner la reponse ?');
      setEnvoiEnCours(false);
    }
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

  // ECRAN PASSEPORT
  if (ecran === 'passeport') {
    const TAMPONS = [
      { id: 'budget', emoji: 'B', titre: 'Budget', desc: 'Gerer son argent' },
      { id: 'impots', emoji: 'I', titre: 'Impots', desc: 'Comprendre les impots' },
      { id: 'travail', emoji: 'T', titre: 'Travail', desc: 'Droits du travail' },
      { id: 'logement', emoji: 'L', titre: 'Logement', desc: 'Bail et logement' },
      { id: 'sante', emoji: 'S', titre: 'Sante', desc: 'Secu sociale' },
      { id: 'entreprise', emoji: 'E', titre: 'Entreprise', desc: 'Creer son business' },
      { id: 'citoyen', emoji: 'C', titre: 'Citoyen', desc: 'Voter et agir' },
      { id: 'cuisine', emoji: 'Cu', titre: 'Cuisine', desc: 'Bien se nourrir' },
      { id: 'code', emoji: 'Co', titre: 'Code', desc: 'Programmer' },
      { id: 'musique', emoji: 'M', titre: 'Musique', desc: 'Arts et creation' },
    ];
    return (
      <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
        <View style={styles.socrateHeader}>
          <TouchableOpacity onPress={function() { setEcran('accueil'); }}>
            <Text style={styles.retour}>? Retour</Text>
          </TouchableOpacity>
          <Text style={styles.socrateMatiere}>Mon passeport de vie</Text>
          <Text style={styles.pointsText}>{passeport.length}/10</Text>
        </View>

        <Text style={styles.passeportIntro}>Chaque competence de vie reelle que tu maitrises te donne un tampon. Complete ton passeport avant tes 18 ans !</Text>

        <View style={styles.tamponsGrid}>
          {TAMPONS.map(function(t) {
            var obtenu = passeport.includes(t.id);
            return (
              <View key={t.id} style={[styles.tamponCard, obtenu ? styles.tamponObtenu : styles.tamponVide]}>
                <View style={[styles.tamponCircle, obtenu ? styles.tamponCircleObtenu : styles.tamponCircleVide]}>
                  <Text style={[styles.tamponEmoji, obtenu ? styles.tamponEmojiObtenu : styles.tamponEmojiVide]}>{t.emoji}</Text>
                </View>
                <Text style={[styles.tamponTitre, obtenu ? styles.tamponTitreObtenu : styles.tamponTitreVide]}>{t.titre}</Text>
                <Text style={styles.tamponDesc}>{t.desc}</Text>
                {obtenu && <Text style={styles.tamponCheck}>Obtenu</Text>}
                {!obtenu && (
                  <TouchableOpacity style={styles.tamponBtn} onPress={function() { ouvrirMatiere(t.titre + ' - ' + t.desc); }}>
                    <Text style={styles.tamponBtnText}>Apprendre</Text>
                  </TouchableOpacity>
                )}
              </View>
            );
          })}
        </View>

        <View style={styles.passeportProgress}>
          <Text style={styles.passeportProgressLabel}>{passeport.length} tampons sur 10</Text>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: (passeport.length / 10 * 100) + '%' }]} />
          </View>
        </View>
      </ScrollView>
    );
  }

  // ECRAN SOCRATE
  if (ecran === 'socrate') {
    return (
      <View style={styles.container}>
        <View style={styles.socrateHeader}>
          <TouchableOpacity onPress={function() { setEcran('accueil'); setSession([]); }}>
            <Text style={styles.retour}>? Retour</Text>
          </TouchableOpacity>
          <Text style={styles.socrateMatiere}>{matiereActive}</Text>
          <TouchableOpacity style={styles.scanBtn} onPress={scannerDevoir}>
            <Text style={styles.scanBtnText}>Scanner</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.socrateMessages} contentContainerStyle={{ paddingBottom: 20 }}>
          {session.length === 0 && (
            <View style={styles.socrateVide}>
              <Text style={styles.socrateVideTitre}>Pret a apprendre !</Text>
              <Text style={styles.socrateVideSub}>Pose ta question ou scanne ton devoir.</Text>
              <Text style={styles.socrateVideSub}>Aria va t'aider a trouver la reponse par toi-meme.</Text>
            </View>
          )}
          {session.map(function(msg, idx) {
            var isUser = msg.role === 'user';
            return (
              <View key={idx} style={[styles.messageRow, isUser ? styles.messageRowUser : styles.messageRowAria]}>
                {!isUser && <View style={styles.ariaAvatar}><Text style={styles.ariaAvatarText}>A</Text></View>}
                <View style={[styles.messageBulle, isUser ? styles.messageBulleUser : styles.messageBulleAria]}>
                  <Text style={[styles.messageTexte, isUser ? styles.messageTexteUser : styles.messageTexteAria]}>{msg.content}</Text>
                </View>
              </View>
            );
          })}
          {envoiEnCours && (
            <View style={styles.messageRowAria}>
              <View style={styles.ariaAvatar}><Text style={styles.ariaAvatarText}>A</Text></View>
              <View style={styles.messageBulleAria}>
                <ActivityIndicator color="#FF7A59" size="small" />
              </View>
            </View>
          )}
        </ScrollView>

        <View style={styles.socrateInput}>
          <TextInput
            style={styles.inputChat}
            placeholder="Ecris ta reponse ou ta question..."
            placeholderTextColor="#7A8095"
            value={inputText}
            onChangeText={setInputText}
            multiline
          />
          <TouchableOpacity style={styles.sendBtn} onPress={function() { envoyerMessage(inputText); }} disabled={envoiEnCours}>
            <Text style={styles.sendBtnText}>Envoyer</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }
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
          <TouchableOpacity key={m} style={styles.matiereCard} onPress={function() { ouvrirMatiere(m); }}>
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
  passeportIntro: { color: '#7A8095', fontSize: 13, textAlign: 'center', marginBottom: 20, paddingHorizontal: 8 },
  tamponsGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 12, marginBottom: 24 },
  tamponCard: { width: 140, borderRadius: 16, padding: 14, alignItems: 'center', borderWidth: 1 },
  tamponObtenu: { backgroundColor: '#F5A62315', borderColor: '#F5A623' },
  tamponVide: { backgroundColor: '#0F1626', borderColor: '#1E2535' },
  tamponCircle: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: 8 },
  tamponCircleObtenu: { backgroundColor: '#F5A62330' },
  tamponCircleVide: { backgroundColor: '#1E2535' },
  tamponEmoji: { fontSize: 16, fontWeight: '800' },
  tamponEmojiObtenu: { color: '#F5A623' },
  tamponEmojiVide: { color: '#7A8095' },
  tamponTitre: { fontSize: 13, fontWeight: '700', marginBottom: 2 },
  tamponTitreObtenu: { color: '#F5A623' },
  tamponTitreVide: { color: '#fff' },
  tamponDesc: { fontSize: 10, color: '#7A8095', textAlign: 'center', marginBottom: 6 },
  tamponCheck: { fontSize: 11, color: '#F5A623', fontWeight: '700' },
  tamponBtn: { backgroundColor: '#FF7A5920', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4, borderWidth: 1, borderColor: '#FF7A59' },
  tamponBtnText: { color: '#FF7A59', fontSize: 11, fontWeight: '700' },
  passeportProgress: { marginTop: 8, paddingHorizontal: 8 },
  passeportProgressLabel: { color: '#7A8095', fontSize: 12, marginBottom: 6, textAlign: 'center' },
  progressBar: { height: 6, backgroundColor: '#1E2535', borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: 6, backgroundColor: '#F5A623', borderRadius: 3 },
  socrateHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 40, marginBottom: 12, paddingHorizontal: 4 },
  socrateMatiere: { fontSize: 15, fontWeight: '700', color: '#fff' },
  scanBtn: { backgroundColor: '#FF7A5920', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 6, borderWidth: 1, borderColor: '#FF7A59' },
  scanBtnText: { color: '#FF7A59', fontSize: 12, fontWeight: '700' },
  socrateMessages: { flex: 1, paddingHorizontal: 4 },
  socrateVide: { alignItems: 'center', marginTop: 60, paddingHorizontal: 20 },
  socrateVideTitre: { fontSize: 20, fontWeight: '800', color: '#fff', marginBottom: 12 },
  socrateVideSub: { fontSize: 14, color: '#7A8095', textAlign: 'center', marginBottom: 6 },
  messageRow: { flexDirection: 'row', marginBottom: 12, alignItems: 'flex-end' },
  messageRowUser: { justifyContent: 'flex-end' },
  messageRowAria: { justifyContent: 'flex-start' },
  ariaAvatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#FF7A5920', alignItems: 'center', justifyContent: 'center', marginRight: 8, borderWidth: 1, borderColor: '#FF7A59' },
  ariaAvatarText: { color: '#FF7A59', fontWeight: '800', fontSize: 14 },
  messageBulle: { maxWidth: '75%', borderRadius: 16, padding: 12 },
  messageBulleUser: { backgroundColor: '#1E2535', borderBottomRightRadius: 4 },
  messageBulleAria: { backgroundColor: '#FF7A5915', borderWidth: 1, borderColor: '#FF7A5940', borderBottomLeftRadius: 4 },
  messageTexte: { fontSize: 14, lineHeight: 20 },
  messageTexteUser: { color: '#A0A8BC' },
  messageTexteAria: { color: '#fff' },
  socrateInput: { flexDirection: 'row', alignItems: 'flex-end', paddingTop: 8, paddingBottom: 16, gap: 8 },
  inputChat: { flex: 1, backgroundColor: '#0F1626', borderRadius: 12, padding: 12, color: '#fff', fontSize: 14, borderWidth: 1, borderColor: '#1E2535', maxHeight: 100 },
  sendBtn: { backgroundColor: '#FF7A59', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12 },
  sendBtnText: { color: '#fff', fontWeight: '800', fontSize: 13 },
});
