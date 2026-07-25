/**
 * LoginScreen.js — Aria Facility FORGEDIS
 * Design senior : grands boutons, texte large, coral #FF7A59
 * Connexion email + mot de passe via Supabase Auth
 * Biométrie (Face ID / empreinte) au retour
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as LocalAuthentication from "expo-local-authentication";

const SUPABASE_URL = "https://dvlrilklbspuckbplglz.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2bHJpbGtsYnNwdWNrYnBsZ2x6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEzNzYyNjIsImV4cCI6MjA5Njk1MjI2Mn0.lC1rt8bvfIpi1c78L8OWGXjjYhXzqzNkIgykHTle6eM";
const RELAY_URL = "https://aria-forgelis.onrender.com/client-token";
const EMAIL_KEY = "aria_client_email";
const TOKEN_KEY = "aria_client_token";
const BIO_KEY = "aria_biometrie_active";

export default function LoginScreen({ onDone }) {
  const [email, setEmail]           = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur]         = useState("");
  const [modeMdpOublie, setModeMdpOublie] = useState(false);
  const [voirMdp, setVoirMdp]       = useState(false);
  const [biometrieDisponible, setBiometrieDisponible] = useState(false);

  // ── Vérifier biométrie au démarrage ──
  useEffect(() => {
    _verifierBiometrie();
    _preRemplirEmail();
  }, []);

  async function _preRemplirEmail() {
    try {
      const e = await AsyncStorage.getItem(EMAIL_KEY);
      if (e) setEmail(e);
    } catch {}
  }

  async function _verifierBiometrie() {
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled   = await LocalAuthentication.isEnrolledAsync();
      const bioActive  = await AsyncStorage.getItem(BIO_KEY);
      if (compatible && enrolled && bioActive === "true") {
        setBiometrieDisponible(true);
        // Proposer la biométrie automatiquement si email connu
        const e = await AsyncStorage.getItem(EMAIL_KEY);
        if (e) _connexionBiometrie();
      }
    } catch {}
  }

  async function _connexionBiometrie() {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: "Aria — Vérification rapide",
        cancelLabel: "Utiliser mon mot de passe",
        fallbackLabel: "Mot de passe",
      });
      if (result.success) {
        const token = await AsyncStorage.getItem(TOKEN_KEY);
        const e     = await AsyncStorage.getItem(EMAIL_KEY);
        if (token && e) {
          onDone({ email: e, token });
        }
      }
    } catch {}
  }

  // ── Connexion email + mot de passe ──
  async function valider() {
    const e = email.trim().toLowerCase();
    if (!e || !e.includes("@")) {
      setErreur("Veuillez entrer votre adresse email.");
      return;
    }

    if (modeMdpOublie) {
      await envoyerResetMdp(e);
      return;
    }

    if (!motDePasse || motDePasse.length < 6) {
      setErreur("Veuillez entrer votre mot de passe (6 caractères minimum).");
      return;
    }

    setErreur("");
    setChargement(true);

    try {
      // Supabase Auth
      const r = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
        body: JSON.stringify({ email: e, password: motDePasse }),
      });
      const data = await r.json();

      if (!r.ok || !data.access_token) {
        setErreur("Email ou mot de passe incorrect.");
        setChargement(false);
        return;
      }

      // Récupérer le token Aria via relay
      const relay = await fetch(RELAY_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: e }),
      });
      const relayData = await relay.json();

      // Sauvegarder
      await AsyncStorage.setItem(EMAIL_KEY, e);
      if (relayData.token) {
        await AsyncStorage.setItem(TOKEN_KEY, relayData.token);
      }

      // Proposer la biométrie si disponible et pas encore activée
      const bioActive = await AsyncStorage.getItem(BIO_KEY);
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled   = await LocalAuthentication.isEnrolledAsync();

      if (compatible && enrolled && bioActive !== "true") {
        Alert.alert(
          "Connexion rapide",
          "Voulez-vous utiliser votre empreinte ou Face ID pour vous connecter plus rapidement la prochaine fois ?",
          [
            { text: "Non merci", style: "cancel" },
            {
              text: "Oui, activer",
              onPress: async () => {
                await AsyncStorage.setItem(BIO_KEY, "true");
              },
            },
          ]
        );
      }

      setChargement(false);
      onDone({ email: e, token: relayData.token || "" });

    } catch (err) {
      setErreur("Erreur réseau. Vérifiez votre connexion internet.");
      setChargement(false);
    }
  }

  // ── Mot de passe oublié ──
  async function envoyerResetMdp(e) {
    setChargement(true);
    try {
      await fetch(`${SUPABASE_URL}/auth/v1/recover`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
        body: JSON.stringify({ email: e }),
      });
      setChargement(false);
      setModeMdpOublie(false);
      Alert.alert(
        "Email envoyé ✓",
        "Un lien pour réinitialiser votre mot de passe a été envoyé à " + e + ".\n\nVérifiez votre boîte mail.",
        [{ text: "Compris" }]
      );
    } catch {
      setChargement(false);
      setErreur("Erreur d'envoi. Réessayez.");
    }
  }

  return (
    <SafeAreaView style={s.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={s.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Logo */}
          <View style={s.logoWrap}>
            <Text style={s.logoText}>FORGE<Text style={s.logoCoral}>DIS</Text></Text>
            <Text style={s.logoSub}>Aria Facility</Text>
          </View>

          {/* Slogan */}
          <Text style={s.slogan}>
            {modeMdpOublie
              ? "Nous allons vous aider à retrouver l'accès."
              : "Bienvenue. Aria est prête à vous aider."}
          </Text>

          {/* Carte connexion */}
          <View style={s.card}>
            <Text style={s.titre}>
              {modeMdpOublie ? "Mot de passe oublié" : "Connexion"}
            </Text>
            <Text style={s.sous_titre}>
              {modeMdpOublie
                ? "Entrez votre email pour recevoir un lien de réinitialisation."
                : "Entrez votre email et votre mot de passe."}
            </Text>

            {/* Email */}
            <Text style={s.label}>Votre adresse email</Text>
            <TextInput
              style={s.input}
              placeholder="votre@email.com"
              placeholderTextColor="#6D7799"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType={modeMdpOublie ? "send" : "next"}
            />

            {/* Mot de passe */}
            {!modeMdpOublie && (
              <>
                <Text style={s.label}>Votre mot de passe</Text>
                <View style={s.inputWrap}>
                  <TextInput
                    style={[s.input, { flex: 1, marginBottom: 0 }]}
                    placeholder="••••••••"
                    placeholderTextColor="#6D7799"
                    value={motDePasse}
                    onChangeText={setMotDePasse}
                    secureTextEntry={!voirMdp}
                    returnKeyType="done"
                    onSubmitEditing={valider}
                  />
                  <TouchableOpacity
                    style={s.oeilBtn}
                    onPress={() => setVoirMdp(!voirMdp)}
                    accessibilityLabel={voirMdp ? "Masquer le mot de passe" : "Voir le mot de passe"}
                  >
                    <Text style={s.oeilTxt}>{voirMdp ? "🙈" : "👁"}</Text>
                  </TouchableOpacity>
                </View>

                {/* Mot de passe oublié */}
                <TouchableOpacity
                  onPress={() => { setModeMdpOublie(true); setErreur(""); }}
                  style={s.oubliBtn}
                >
                  <Text style={s.oubliTxt}>Mot de passe oublié ?</Text>
                </TouchableOpacity>
              </>
            )}

            {/* Erreur */}
            {erreur !== "" && (
              <View style={s.erreurWrap}>
                <Text style={s.erreurTxt}>⚠️ {erreur}</Text>
              </View>
            )}

            {/* Bouton principal */}
            <TouchableOpacity
              style={[s.btnPrincipal, chargement && s.btnDesactive]}
              onPress={valider}
              disabled={chargement}
              activeOpacity={0.85}
            >
              {chargement ? (
                <ActivityIndicator color="#fff" size="large" />
              ) : (
                <Text style={s.btnTxt}>
                  {modeMdpOublie ? "Envoyer le lien →" : "Me connecter →"}
                </Text>
              )}
            </TouchableOpacity>

            {/* Biométrie */}
            {biometrieDisponible && !modeMdpOublie && (
              <TouchableOpacity
                style={s.btnBio}
                onPress={_connexionBiometrie}
                activeOpacity={0.8}
              >
                <Text style={s.btnBioTxt}>🔒 Connexion rapide (empreinte / Face ID)</Text>
              </TouchableOpacity>
            )}

            {/* Retour depuis mot de passe oublié */}
            {modeMdpOublie && (
              <TouchableOpacity
                onPress={() => { setModeMdpOublie(false); setErreur(""); }}
                style={s.retourBtn}
              >
                <Text style={s.retourTxt}>← Retour à la connexion</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Slogan bas */}
          <Text style={s.sloganBas}>
            "L'indépendance n'a pas d'âge.{"\n"}Aria non plus."
          </Text>
          <Text style={s.tagline}>L'IA française qui n'oublie personne.</Text>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const CORAL   = "#FF7A59";
const NAVY    = "#070B18";
const PANEL   = "#0F1830";
const TEXT    = "#F0F3FB";
const SOFT    = "#A6B0CC";
const DIM     = "#6D7799";
const LINE    = "rgba(255,255,255,0.09)";

const s = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: NAVY,
  },
  scroll: {
    flexGrow: 1,
    padding: 24,
    justifyContent: "center",
  },
  logoWrap: {
    alignItems: "center",
    marginBottom: 8,
  },
  logoText: {
    fontFamily: Platform.OS === "ios" ? "System" : "sans-serif-medium",
    fontSize: 32,
    fontWeight: "800",
    color: TEXT,
    letterSpacing: -1,
  },
  logoCoral: {
    color: CORAL,
  },
  logoSub: {
    fontSize: 15,
    color: SOFT,
    marginTop: 2,
    letterSpacing: 2,
    textTransform: "uppercase",
  },
  slogan: {
    fontSize: 17,
    color: SOFT,
    textAlign: "center",
    marginBottom: 28,
    lineHeight: 24,
    paddingHorizontal: 16,
  },
  card: {
    backgroundColor: PANEL,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: LINE,
    marginBottom: 24,
    shadowColor: "#000",
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 8,
  },
  titre: {
    fontSize: 24,
    fontWeight: "800",
    color: TEXT,
    marginBottom: 6,
  },
  sous_titre: {
    fontSize: 15,
    color: SOFT,
    marginBottom: 24,
    lineHeight: 22,
  },
  label: {
    fontSize: 14,
    fontWeight: "700",
    color: SOFT,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  input: {
    backgroundColor: "#0C1226",
    borderWidth: 1,
    borderColor: LINE,
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    color: TEXT,
    marginBottom: 16,
  },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    gap: 8,
  },
  oeilBtn: {
    padding: 16,
    backgroundColor: "#0C1226",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: LINE,
  },
  oeilTxt: {
    fontSize: 20,
  },
  oubliBtn: {
    alignSelf: "flex-end",
    marginBottom: 20,
    marginTop: 4,
  },
  oubliTxt: {
    fontSize: 14,
    color: DIM,
  },
  erreurWrap: {
    backgroundColor: "rgba(239,68,68,0.08)",
    borderWidth: 1,
    borderColor: "rgba(239,68,68,0.25)",
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
  },
  erreurTxt: {
    color: "#f87171",
    fontSize: 15,
    lineHeight: 22,
  },
  btnPrincipal: {
    backgroundColor: CORAL,
    borderRadius: 14,
    padding: 20,
    alignItems: "center",
    marginBottom: 12,
    minHeight: 64,
    justifyContent: "center",
  },
  btnDesactive: {
    opacity: 0.6,
  },
  btnTxt: {
    color: "#fff",
    fontSize: 20,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
  btnBio: {
    backgroundColor: "rgba(255,122,89,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,122,89,0.25)",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginBottom: 8,
  },
  btnBioTxt: {
    color: CORAL,
    fontSize: 15,
    fontWeight: "600",
  },
  retourBtn: {
    alignItems: "center",
    marginTop: 8,
  },
  retourTxt: {
    color: DIM,
    fontSize: 15,
  },
  sloganBas: {
    fontSize: 17,
    color: SOFT,
    textAlign: "center",
    fontStyle: "italic",
    lineHeight: 26,
    marginBottom: 8,
  },
  tagline: {
    fontSize: 13,
    color: DIM,
    textAlign: "center",
    fontStyle: "italic",
    marginBottom: 24,
  },
});
