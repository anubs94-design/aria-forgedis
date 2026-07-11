import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  CLIENT_ID: 'forgedis_client_id',
  PROFILE: 'forgedis_profile',
  ONBOARDING_DONE: 'forgedis_onboarding_done',
  HISTORY: 'forgedis_history',
  SETTINGS: 'forgedis_settings',
  AGENT_TOKEN: 'forgedis_agent_token',
  ACCOUNT_EMAIL: 'forgedis_account_email',
  FORFAIT: 'forgedis_forfait',
};

export const StorageService = {
  async getClientId() {
    return await AsyncStorage.getItem(KEYS.CLIENT_ID);
  },
  async saveClientId(id) {
    await AsyncStorage.setItem(KEYS.CLIENT_ID, id);
  },
  async getProfile() {
    const raw = await AsyncStorage.getItem(KEYS.PROFILE);
    return raw ? JSON.parse(raw) : null;
  },
  async saveProfile(profile) {
    await AsyncStorage.setItem(KEYS.PROFILE, JSON.stringify(profile));
  },
  async isOnboardingDone() {
    const val = await AsyncStorage.getItem(KEYS.ONBOARDING_DONE);
    return val === 'true';
  },
  async setOnboardingDone() {
    await AsyncStorage.setItem(KEYS.ONBOARDING_DONE, 'true');
  },
  async getHistory() {
    const raw = await AsyncStorage.getItem(KEYS.HISTORY);
    return raw ? JSON.parse(raw) : [];
  },
  async addToHistory(entry) {
    const history = await StorageService.getHistory();
    history.unshift({ ...entry, timestamp: new Date().toISOString() });
    if (history.length > 100) history.splice(100);
    await AsyncStorage.setItem(KEYS.HISTORY, JSON.stringify(history));
    return history;
  },
  async getSettings() {
    const raw = await AsyncStorage.getItem(KEYS.SETTINGS);
    return raw ? JSON.parse(raw) : {
      volume: 80,
      speechRate: 1.0,
      largeText: false,
      highContrast: false,
      notifications: true,
    };
  },
  async saveSettings(settings) {
    await AsyncStorage.setItem(KEYS.SETTINGS, JSON.stringify(settings));
  },
  async getToken() {
    return await AsyncStorage.getItem(KEYS.AGENT_TOKEN);
  },
  async saveToken(token) {
    await AsyncStorage.setItem(KEYS.AGENT_TOKEN, token);
  },
  async getAccountEmail() {
    return await AsyncStorage.getItem(KEYS.ACCOUNT_EMAIL);
  },
  async saveAccountEmail(email) {
    await AsyncStorage.setItem(KEYS.ACCOUNT_EMAIL, email);
  },
  async getForfait() {
    return await AsyncStorage.getItem(KEYS.FORFAIT);
  },
  async saveForfait(forfait) {
    await AsyncStorage.setItem(KEYS.FORFAIT, forfait);
  },
  async resetAll() {
    await AsyncStorage.multiRemove(Object.values(KEYS));
  },
};