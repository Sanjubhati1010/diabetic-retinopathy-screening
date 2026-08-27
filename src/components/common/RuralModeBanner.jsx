import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import { voiceService } from '../../services/voiceService';
import {
  Compass,
  Wifi,
  Volume2,
  VolumeX,
  Sparkles,
  Zap,
  Check,
  Smartphone,
  Square,
  Play,
} from 'lucide-react';

export const RuralModeBanner = () => {
  const { t, language } = useLanguage();
  const {
    ruralMode,
    toggleRuralMode,
    lowBandwidthMode,
    toggleLowBandwidthMode,
    voiceGuidanceEnabled,
    toggleVoiceGuidance,
  } = useApp();

  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    const unsub = voiceService.subscribe((state) => {
      setIsSpeaking(state.isSpeaking);
    });
    return () => unsub();
  }, []);

  const handleVoiceToggle = () => {
    if (!voiceGuidanceEnabled) {
      toggleVoiceGuidance();
      // Directly speak on user gesture
      const text =
        language === 'hi'
          ? (voiceService.hasHindiVoice()
              ? 'आवाज़ मार्गदर्शन चालू है। कृपया स्क्रीनिंग शुरू करने के लिए मरीज चुनें।'
              : 'Voice guidance chalu hai. Kripya screening shuru karne ke liye mareez chunein.')
          : 'Voice guidance is enabled. Please select a patient to begin screening.';
      voiceService.speak(text, language);
    } else {
      voiceService.stop();
      toggleVoiceGuidance();
    }
  };

  const handleQuickPlay = (e) => {
    e.stopPropagation();
    if (isSpeaking) {
      voiceService.stop();
    } else {
      const text =
        language === 'hi'
          ? (voiceService.hasHindiVoice()
              ? 'प्राथमिक स्वास्थ्य केंद्र ग्रामीण स्क्रीनिंग मोड सक्रिय है।'
              : 'Primary health center rural screening mode active hai.')
          : 'Primary health center rural screening mode is active.';
      voiceService.speak(text, language);
    }
  };

  return (
    <div className="no-print bg-slate-900 text-white py-1.5 border-b border-slate-800 w-full min-w-0">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 flex items-center justify-between gap-2.5 text-xs flex-nowrap w-full min-w-0">
        {/* Left: Rural Badge & Guidance */}
        <div className="flex items-center gap-2 min-w-0 shrink">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-teal-500/20 text-teal-300 border border-teal-500/30 text-[11px] font-bold shrink-0">
            <Compass className="w-3.5 h-3.5 text-teal-400" />
            <span>PHC Field Deployment</span>
          </span>
          <span className="text-slate-400 hidden lg:inline text-[11px] truncate max-w-sm">
            {language === 'hi'
              ? 'ग्रामीण स्वास्थ्य शिविर एवं प्राथमिक स्वास्थ्य केंद्र अनुकूलन'
              : 'Optimized for Rural Camps & Vision Technicians'}
          </span>
        </div>

        {/* Right: 3 Core Deployment Toggles */}
        <div className="flex items-center gap-1.5 sm:gap-2 flex-nowrap shrink-0">
        {/* 1. Rural Mode Toggle */}
        <button
          type="button"
          onClick={toggleRuralMode}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-bold text-[11px] transition border ${
            ruralMode
              ? 'bg-brand-600 text-white border-brand-500 shadow-sm'
              : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
          }`}
          title="Toggle Large touch targets & simplified workflow"
        >
          <Smartphone className="w-3.5 h-3.5" />
          <span>{t('ruralMode')}</span>
          {ruralMode && <Check className="w-3 h-3 text-white ml-0.5" />}
        </button>

        {/* 2. Low Bandwidth Mode Toggle */}
        <button
          type="button"
          onClick={toggleLowBandwidthMode}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-bold text-[11px] transition border ${
            lowBandwidthMode
              ? 'bg-amber-600 text-white border-amber-500 shadow-sm'
              : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
          }`}
          title="Reduces network data usage, compresses previews"
        >
          <Zap className="w-3.5 h-3.5" />
          <span>{t('lowBandwidthMode')}</span>
          {lowBandwidthMode && <Check className="w-3 h-3 text-white ml-0.5" />}
        </button>

        {/* 3. Voice Guidance Toggle & Speaking State */}
        <div className="inline-flex items-center gap-1">
          <button
            type="button"
            onClick={handleVoiceToggle}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-bold text-[11px] transition border ${
              voiceGuidanceEnabled
                ? 'bg-purple-600 text-white border-purple-500 shadow-sm'
                : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
            }`}
            title="Toggle audible spoken instructions"
          >
            {isSpeaking ? (
              <Volume2 className="w-3.5 h-3.5 text-white animate-bounce" />
            ) : voiceGuidanceEnabled ? (
              <Volume2 className="w-3.5 h-3.5" />
            ) : (
              <VolumeX className="w-3.5 h-3.5" />
            )}
            <span>
              {isSpeaking ? '🔊 Speaking...' : t('voiceGuidance')}
            </span>
            {voiceGuidanceEnabled && !isSpeaking && (
              <span className="w-1.5 h-1.5 rounded-full bg-purple-300"></span>
            )}
          </button>

          {voiceGuidanceEnabled && (
            <button
              type="button"
              onClick={handleQuickPlay}
              className="p-1 rounded-lg bg-purple-700 hover:bg-purple-800 text-white transition"
              title={isSpeaking ? 'Stop Audio' : 'Play Audio'}
            >
              {isSpeaking ? <Square className="w-3 h-3 fill-white" /> : <Play className="w-3 h-3 fill-white" />}
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
  );
};
