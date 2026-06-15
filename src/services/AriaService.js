const ANTHROPIC_API_KEY = 'METS_TA_CLE_API_ICI';
const API_URL = 'https://api.anthropic.com/v1/messages';

const ARIA_SYSTEM_PROMPT = `Tu es Aria, une assistante vocale personnelle créée par Forgedis.
Tu aides des personnes seniors ou débutantes avec la technologie.

RÈGLES ABSOLUES :
- Réponds TOUJOURS en français, phrases courtes et claires
- Sois chaleureuse, patiente, jamais condescendante
- Le client est seul responsable de ses actions

FORMAT DE RÉPONSE — retourne TOUJOURS ce JSON :
{
  "type": "response" ou "pc_command",
  "text": "Ce que tu dis à voix haute",
  "command": null ou {
    "action": "open_app" | "type_text" | "click" | "search_web" | "open_url",
    "target": "...",
    "params": {}
  }
}`;

export const AriaService = {
  conversationHistory: [],

  async sendMessage(userMessage, clientId, location = null) {
    let contextualMessage = userMessage;
    if (location) {
      contextualMessage += `\n[Position: ${location.lat}, ${location.lng} — ${new Date().toLocaleString('fr-FR')}]`;
    }

    AriaService.conversationHistory.push({
      role: 'user',
      content: contextualMessage,
    });

    if (AriaService.conversationHistory.length > 20) {
      AriaService.conversationHistory = AriaService.conversationHistory.slice(-20);
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-6',
          max_tokens: 1024,
          system: ARIA_SYSTEM_PROMPT,
          messages: AriaService.conversationHistory,
        }),
      });

      if (!response.ok) throw new Error(`API Error: ${response.status}`);

      const data = await response.json();
      const rawText = data.content[0].text;

      let parsed;
      try {
        const clean = rawText.replace(/```json|```/g, '').trim();
        parsed = JSON.parse(clean);
      } catch {
        parsed = { type: 'response', text: rawText, command: null };
      }

      AriaService.conversationHistory.push({
        role: 'assistant',
        content: rawText,
      });

      return parsed;
    } catch (error) {
      console.error('AriaService error:', error);
      return {
        type: 'response',
        text: 'Je rencontre une difficulté de connexion. Vérifiez votre connexion internet.',
        command: null,
      };
    }
  },

  clearHistory() {
    AriaService.conversationHistory = [];
  },
};