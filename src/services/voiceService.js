/**
 * Voice Guidance Service for Rural Healthcare Deployments
 * Uses browser Web Speech Synthesis API to read step-by-step workflow instructions in Hindi and English.
 *
 * Exclusively designed for workflow navigation and explaining existing system results.
 * DOES NOT provide independent medical diagnoses.
 */

// Canonical Bilingual Workflow Scripts
export const WORKFLOW_SCRIPTS = {
  welcome: {
    en: "Welcome to MADOCS Rural DR Screening. Voice guidance is enabled.",
    hi_devanagari: "मैडॉक्स ग्रामीण डीआर स्क्रीनिंग में आपका स्वागत है। आवाज़ मार्गदर्शन चालू है।",
    hi_latin: "MADOCS rural screening mein aapka swagat hai. Voice guidance chalu hai.",
  },
  step1: {
    title: "1. Patient Information",
    en: "Step one: Please select or register patient information to begin screening.",
    hi_devanagari: "चरण एक: कृपया मरीज की जानकारी चुनें या नया मरीज पंजीकृत करें।",
    hi_latin: "Step 1: Kripya mareez ki jaankari chunein ya naya mareez register karein.",
  },
  step2: {
    title: "2. Right Eye (OD)",
    en: "Step two: Please upload the right eye fundus image.",
    hi_devanagari: "चरण दो: कृपया दाहिनी आँख यानी ओ डी का फंडस फोटो अपलोड करें।",
    hi_latin: "Step 2: Kripya right eye yaani O-D ki fundus image upload karein.",
  },
  step3: {
    title: "3. Left Eye (OS)",
    en: "Step three: Please upload the left eye fundus image.",
    hi_devanagari: "चरण तीन: अब बाईं आँख यानी ओ एस का फंडस फोटो अपलोड करें।",
    hi_latin: "Step 3: Ab left eye yaani O-S ki fundus image upload karein.",
  },
  step4: {
    title: "4. Quality Check",
    en: "Step four: Image quality check is in progress. Verifying illumination and sharpness.",
    hi_devanagari: "चरण चार: इमेज गुणवत्ता और एआई सुरक्षा जांच की जा रही है।",
    hi_latin: "Step 4: Image quality aur AI safety check kiya ja raha hai.",
  },
  step5: {
    title: "5. AI Screening",
    en: "Step five: AI screening is ready to start. Click Start AI Screening to analyze retinal biomarkers.",
    hi_devanagari: "चरण पांच: एआई स्क्रीनिंग शुरू करने के लिए तैयार है। एआई स्क्रीनिंग शुरू करें पर क्लिक करें।",
    hi_latin: "Step 5: AI screening shuru karne ke liye taiyaar hai. Start AI screening par click karein.",
  },
  step6: {
    title: "6. Explainable AI (Grad-CAM)",
    en: "Step six: Your AI-assisted screening result is ready. Please review the confidence and Grad-CAM heatmap.",
    hi_devanagari: "चरण छह: आपका एआई स्क्रीनिंग परिणाम तैयार है। कृपया परिणाम और ग्रैड-कैम हीटमैप देखें।",
    hi_latin: "Step 6: Aapka AI screening result taiyaar hai. Kripya result aur Grad-CAM heatmap review karein.",
  },
  step7: {
    title: "7. Risk & Referral",
    en: "Step seven: Review the screening risk category and specialist referral recommendation.",
    hi_devanagari: "चरण सात: जोखिम मूल्यांकन और नेत्र विशेषज्ञ रेफरल प्राथमिकता की समीक्षा करें।",
    hi_latin: "Step 7: Risk evaluation aur eye specialist referral recommendation review karein.",
  },
  step8: {
    title: "8. Doctor Review & Report",
    en: "Step eight: Doctor review is recommended for this screening. Bilingual patient report is ready.",
    hi_devanagari: "चरण आठ: इस स्क्रीनिंग के लिए डॉक्टर समीक्षा की सिफारिश की गई है। मरीज रिपोर्ट तैयार है।",
    hi_latin: "Step 8: Doctor review is recommended. Bilingual patient report taiyaar hai.",
  },
  recapture: {
    title: "Image Re-capture Required",
    en: "Doctor has requested an image re-capture. Please capture and upload a new fundus image.",
    hi_devanagari: "डॉक्टर ने दोबारा फोटो लेने का अनुरोध किया है। कृपया नई फंडस इमेज खींचकर अपलोड करें।",
    hi_latin: "Doctor ne image re-capture ka anurodh kiya hai. Kripya nayi fundus image upload karein.",
  },
  report: {
    title: "Patient Report Ready",
    en: "Patient screening report is ready. You can view, download, or print this report.",
    hi_devanagari: "मरीज स्क्रीनिंग रिपोर्ट तैयार है। आप इसे देख सकते हैं और प्रिंट कर सकते हैं।",
    hi_latin: "Patient screening report taiyaar hai. Aap ise view ya print kar sakte hain.",
  },
};

class VoiceService {
  constructor() {
    this.isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;
    this.voices = [];
    this.isSpeaking = false;
    this.listeners = new Set();
    this.activeUtterance = null;
    this.hasInitializedVoices = false;

    if (this.isSupported) {
      this.initVoices();
    }
  }

  initVoices() {
    if (!this.isSupported) return;

    const updateVoices = () => {
      try {
        const available = window.speechSynthesis.getVoices() || [];
        if (available.length > 0) {
          this.voices = available;
          this.hasInitializedVoices = true;
          this.notifyListeners();
        }
      } catch (err) {
        console.warn('SpeechSynthesis getVoices error:', err);
      }
    };

    updateVoices();
    if (typeof window.speechSynthesis.onvoiceschanged !== 'undefined') {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }

  refreshVoices() {
    if (!this.isSupported) return [];
    try {
      const v = window.speechSynthesis.getVoices() || [];
      if (v.length > 0) {
        this.voices = v;
      }
      return this.voices;
    } catch {
      return [];
    }
  }

  subscribe(listener) {
    this.listeners.add(listener);
    // Call immediately with current state
    try {
      listener({
        isSpeaking: this.isSpeaking,
        isSupported: this.isSupported,
        hasHindiVoice: this.hasHindiVoice(),
      });
    } catch (e) {
      console.warn('Initial voice listener error:', e);
    }
    return () => this.listeners.delete(listener);
  }

  notifyListeners() {
    const state = {
      isSpeaking: this.isSpeaking,
      isSupported: this.isSupported,
      hasHindiVoice: this.hasHindiVoice(),
    };
    this.listeners.forEach((listener) => {
      try {
        listener(state);
      } catch (err) {
        console.warn('Voice listener notification error:', err);
      }
    });
  }

  hasHindiVoice() {
    this.refreshVoices();
    return this.voices.some(
      (v) =>
        v.lang?.toLowerCase().startsWith('hi') ||
        v.lang?.toLowerCase().includes('hi-in') ||
        v.name?.toLowerCase().includes('hindi')
    );
  }

  getBestVoice(lang = 'en') {
    this.refreshVoices();
    if (!this.voices || this.voices.length === 0) return null;

    if (lang === 'hi') {
      // 1. Look for native Hindi voice
      const hindiVoice = this.voices.find(
        (v) =>
          v.lang?.toLowerCase().startsWith('hi') ||
          v.lang?.toLowerCase().includes('hi-in') ||
          v.name?.toLowerCase().includes('hindi')
      );
      if (hindiVoice) return { voice: hindiVoice, isNativeHindi: true };

      // 2. Look for Indian English voice for romanized Hindi fallback
      const indianEnglish = this.voices.find(
        (v) => v.lang?.toLowerCase().includes('en-in') || v.name?.toLowerCase().includes('india')
      );
      if (indianEnglish) return { voice: indianEnglish, isNativeHindi: false };
    }

    // Standard English selection (prefer Indian English, then US/GB, then any English)
    const indianEnglish = this.voices.find(
      (v) => v.lang?.toLowerCase().includes('en-in') || v.name?.toLowerCase().includes('india')
    );
    if (indianEnglish) return { voice: indianEnglish, isNativeHindi: false };

    const englishVoice = this.voices.find((v) => v.lang?.toLowerCase().startsWith('en'));
    if (englishVoice) return { voice: englishVoice, isNativeHindi: false };

    return { voice: this.voices[0], isNativeHindi: false };
  }

  getScriptText(stepKey, lang = 'en') {
    const item = WORKFLOW_SCRIPTS[stepKey] || WORKFLOW_SCRIPTS[`step${stepKey}`];
    if (!item) return null;

    if (lang === 'hi') {
      const hasNative = this.hasHindiVoice();
      return hasNative ? item.hi_devanagari : item.hi_latin;
    }
    return item.en;
  }

  speak(text, language = 'en', onEnd = null) {
    if (!this.isSupported) {
      console.warn('Speech synthesis is not supported in this browser.');
      return false;
    }

    if (!text || typeof text !== 'string' || !text.trim()) {
      return false;
    }

    try {
      // 1. Cancel previous speaking
      this.stop();

      // 2. Resume synthesizer if paused by browser
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }

      // 3. Resolve voice & speech parameters
      const voiceInfo = this.getBestVoice(language);
      const utterance = new SpeechSynthesisUtterance(text.trim());

      if (voiceInfo?.voice) {
        utterance.voice = voiceInfo.voice;
      }

      if (language === 'hi') {
        utterance.lang = voiceInfo?.isNativeHindi ? 'hi-IN' : 'en-IN';
        utterance.rate = 0.9; // clear, accessible pace for PHC field staff
      } else {
        utterance.lang = 'en-IN';
        utterance.rate = 0.95;
      }
      utterance.pitch = 1.0;

      // 4. Attach lifecycle listeners
      utterance.onstart = () => {
        this.isSpeaking = true;
        this.notifyListeners();
      };

      utterance.onend = () => {
        this.isSpeaking = false;
        this.activeUtterance = null;
        if (typeof window !== 'undefined') {
          window.__madocs_active_utterance = null;
        }
        this.notifyListeners();
        if (onEnd) onEnd();
      };

      utterance.onerror = (event) => {
        // 'interrupted' / 'canceled' is standard when calling stop()
        this.isSpeaking = false;
        this.activeUtterance = null;
        if (typeof window !== 'undefined') {
          window.__madocs_active_utterance = null;
        }
        this.notifyListeners();
      };

      // 5. Prevent garbage collection of utterance in Chromium
      this.activeUtterance = utterance;
      if (typeof window !== 'undefined') {
        window.__madocs_active_utterance = utterance;
      }

      // 6. Execute speech
      window.speechSynthesis.speak(utterance);
      return true;
    } catch (err) {
      console.error('Speech synthesis execution failure:', err);
      this.isSpeaking = false;
      this.notifyListeners();
      return false;
    }
  }

  speakStep(stepNumberOrKey, language = 'en', onEnd = null) {
    const text = this.getScriptText(stepNumberOrKey, language);
    if (!text) {
      console.warn(`No workflow script found for step: ${stepNumberOrKey}`);
      return false;
    }
    return this.speak(text, language, onEnd);
  }

  stop() {
    if (!this.isSupported) return;
    try {
      window.speechSynthesis.cancel();
      this.isSpeaking = false;
      this.activeUtterance = null;
      if (typeof window !== 'undefined') {
        window.__madocs_active_utterance = null;
      }
      this.notifyListeners();
    } catch (err) {
      console.warn('Speech synthesis cancellation error:', err);
    }
  }
}

export const voiceService = new VoiceService();
