/**
 * Voice Guidance Service for Rural Healthcare Deployments
 * Uses browser Web Speech Synthesis API to read step-by-step workflow instructions in Hindi and English.
 *
 * Designed exclusively for workflow navigation and explaining existing system results.
 * DOES NOT provide independent medical diagnoses.
 */

class VoiceService {
  constructor() {
    this.isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;
    this.currentUtterance = null;
    this.voices = [];
    this.isSpeaking = false;
    this.listeners = new Set();

    if (this.isSupported) {
      this.loadVoices();
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = () => this.loadVoices();
      }
    }
  }

  loadVoices() {
    if (!this.isSupported) return;
    this.voices = window.speechSynthesis.getVoices() || [];
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notifyListeners(speaking) {
    this.isSpeaking = speaking;
    this.listeners.forEach((listener) => {
      try {
        listener(speaking);
      } catch (err) {
        console.warn('Voice listener notification failed:', err);
      }
    });
  }

  getBestVoice(lang = 'en') {
    if (!this.voices || this.voices.length === 0) {
      this.loadVoices();
    }

    if (lang === 'hi') {
      // Prioritize Hindi voices
      const hindiVoice = this.voices.find(
        (v) => v.lang === 'hi-IN' || v.lang.startsWith('hi') || v.name.toLowerCase().includes('hindi')
      );
      if (hindiVoice) return hindiVoice;
    }

    // Indian English or generic English fallback
    const indianEnglish = this.voices.find(
      (v) => v.lang === 'en-IN' || v.name.toLowerCase().includes('india')
    );
    if (indianEnglish) return indianEnglish;

    const anyEnglish = this.voices.find((v) => v.lang.startsWith('en'));
    return anyEnglish || this.voices[0] || null;
  }

  speak(text, language = 'en', onEnd = null) {
    if (!this.isSupported || !text) return false;

    try {
      this.stop();

      const utterance = new SpeechSynthesisUtterance(text);
      const voice = this.getBestVoice(language);
      if (voice) {
        utterance.voice = voice;
      }
      utterance.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
      utterance.rate = language === 'hi' ? 0.9 : 0.95; // Slightly slower for clarity in rural camps
      utterance.pitch = 1.0;

      utterance.onstart = () => {
        this.notifyListeners(true);
      };

      utterance.onend = () => {
        this.notifyListeners(false);
        if (onEnd) onEnd();
      };

      utterance.onerror = (e) => {
        console.warn('Speech synthesis error or cancelled:', e);
        this.notifyListeners(false);
      };

      this.currentUtterance = utterance;
      window.speechSynthesis.speak(utterance);
      return true;
    } catch (err) {
      console.warn('Voice service execution error:', err);
      this.notifyListeners(false);
      return false;
    }
  }

  stop() {
    if (!this.isSupported) return;
    try {
      window.speechSynthesis.cancel();
      this.notifyListeners(false);
    } catch (err) {
      console.warn('Speech synthesis cancellation error:', err);
    }
  }
}

export const voiceService = new VoiceService();
