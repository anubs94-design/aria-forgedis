import * as Crypto from 'expo-crypto';
import { StorageService } from './StorageService';

export const ClientService = {
  async getOrCreateClientId() {
    let id = await StorageService.getClientId();
    if (!id) {
      const bytes = await Crypto.getRandomBytesAsync(16);
      const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
      id = [
        hex.slice(0, 8),
        hex.slice(8, 12),
        '4' + hex.slice(13, 16),
        ((parseInt(hex[16], 16) & 0x3) | 0x8).toString(16) + hex.slice(17, 20),
        hex.slice(20, 32),
      ].join('-');
      await StorageService.saveClientId(id);
    }
    return id;
  },

  formatForDisplay(clientId) {
    if (!clientId) return '----';
    const short = clientId.replace(/-/g, '').toUpperCase().slice(0, 8);
    return `ARIA-${short.slice(0, 4)}-${short.slice(4, 8)}`;
  },
};