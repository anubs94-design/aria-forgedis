import React, { useState } from "react";
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, SafeAreaView, ActivityIndicator, KeyboardAvoidingView, Platform
} from "react-native";
import { StorageService } from "../services/StorageService";
import { setProxyToken } from "../services/DocumentService";

const SUPABASE_URL = "https://dvlrilklbspuckbplglz.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_XraSG03zQGEaDyc962uqtA_Go3evCH6";
const RELAY_URL = "https://aria-forgelis.onrender.com/client-token";

export default function LoginScreen({ onDone }) {
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState("");

  const valider = async () => {
    const e = email.trim().toLowerCase();
    if (!e || !e.includes("@")) { setErreur("Email invalide."); return; }
    if (!motDePasse) { setErreur("Mot de passe requis."); return; }
    setErreur("");
    setChargement(true);
    try {
      // Supabase Auth
      const r = await fetch(SUPABASE_URL + "/auth/v1/token?grant_type=password", {
        method: "POST",
        headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
        body: JSON.stringify({ email: e, password: motDePasse })
      });
      const data = await r.json();
      if (data.error || !data.access_token) {
        setErreur("Email ou mot de passe incorrect.");
        setChargement(false);
        return;
      }
      // Recuperer le token relay via email
      const r2 = await fetch(RELAY_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: e })
      });
      const data2 = await r2.json();
      if (!data2.token) {
        setErreur("Compte introuvable. Contactez le support.");
        setChargement(false);
        return;
      }
      await StorageService.saveToken(data2.token);
      await StorageService.saveAccountEmail(e);
      if (data2.forfait) await StorageService.saveForfait(data2.forfait);
      setProxyToken(data2.token);
      setChargement(false);
      onDone(data2.forfait || "facility");
    } catch(err) {
      setErreur("Erreur de connexion. Reessayez.");
      setChargement(false);
    }
  };

  return (
    <KeyboardAvoidingView style={s.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <SafeAreaView style={s.container}>
        <Text style={s.logo}>FORGE<Text style={s.logoAccent}>DIS</Text></Text>
        <Text style={s.titre}>Connexion</Text>
        <Text style={s.sous}>Entrez vos identifiants pour acceder a votre espace.</Text>
        <TextInput style={s.input} placeholder="Email" placeholderTextColor="#777"
          value={email} onChangeText={setEmail} autoCapitalize="none"
          autoCorrect={false} keyboardType="email-address" />
        <TextInput style={s.input} placeholder="Mot de passe" placeholderTextColor="#777"
          value={motDePasse} onChangeText={setMotDePasse} secureTextEntry />
        {erreur ? <Text style={s.erreur}>{erreur}</Text> : null}
        {chargement
          ? <ActivityIndicator size="large" color="#FF7A59" style={{ marginTop: 16 }} />
          : <TouchableOpacity style={s.bouton} onPress={valider}>
              <Text style={s.boutonTexte}>Se connecter</Text>
            </TouchableOpacity>
        }
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  flex: { flex: 1 },
  container: { flex: 1, backgroundColor: "#0D0F1A", justifyContent: "center", alignItems: "center", padding: 24 },
  logo: { fontSize: 26, fontWeight: "800", color: "#FF7A59", marginBottom: 32 },
  logoAccent: { color: "#F0F3FB" },
  titre: { fontSize: 26, fontWeight: "700", color: "#F0F3FB", marginBottom: 8 },
  sous: { fontSize: 14, color: "#A6B0CC", marginBottom: 32, textAlign: "center", lineHeight: 20 },
  input: { width: "100%", backgroundColor: "#1E2235", borderRadius: 12, padding: 14,
    color: "#F0F3FB", fontSize: 15, marginBottom: 12, borderWidth: 1, borderColor: "rgba(255,255,255,0.09)" },
  erreur: { color: "#FF6B6B", fontSize: 13, marginBottom: 12 },
  bouton: { width: "100%", backgroundColor: "#FF7A59", borderRadius: 12, padding: 16, alignItems: "center", marginTop: 8 },
  boutonTexte: { color: "#fff", fontWeight: "700", fontSize: 16 },
});
