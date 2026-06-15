import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  CLIENT_ID: 'forgedis_client_id',
  PROFILE: 'forgedis_profile',
  ONBOARDING_DONE: 'forgedis_onboarding_done',
  HISTORY: 'forgedis_history',
  SETTINGS: 'forgedis_settings',
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
  async resetAll() {
    await AsyncStorage.multiRemove(Object.values(KEYS));
  },
};