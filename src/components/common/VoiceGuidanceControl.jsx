import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import { voiceService, WORKFLOW_SCRIPTS } from '../../services/voiceService';
import {
  Volume2,
  VolumeX,
  Play,
  Square,
  Sparkles,
  AlertCircle,
  Activity,
  Info,
} from 'lucide-react';

export const VoiceGuidanceControl = ({
  stepKey,
  customText,
  compact = false,
  autoPlay = false,
  className = '',
}) => {
  const { language, t } = useLanguage();
  const { voiceGuidanceEnabled, toggleVoiceGuidance } = useApp();

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [hasHindiVoice, setHasHindiVoice] = useState(true);

  useEffect(() => {
    const unsubscribe = voiceService.subscribe((state) => {
      setIsSpeaking(state.isSpeaking);
      setIsSupported(state.isSupported);
      setHasHindiVoice(state.hasHindiVoice);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const getSpokenContent = () => {
    if (customText) return customText;
    if (stepKey) {
      return voiceService.getScriptText(stepKey, language);
    }
    return voiceService.getScriptText('welcome', language);
  };

  const handlePlay = (e) => {
    if (e) e.stopPropagation();
    const text = getSpokenContent();
    if (text) {
      voiceService.speak(text, language);
    }
  };

  const handleStop = (e) => {
    if (e) e.stopPropagation();
    voiceService.stop();
  };

  const handleToggleEnable = (e) => {
    if (e) e.stopPropagation();
    toggleVoiceGuidance();
    if (!voiceGuidanceEnabled) {
      // User just turned it on via click gesture -> speak initial prompt immediately
      const text = getSpokenContent();
      if (text) {
        voiceService.speak(text, language);
      }
    } else {
      voiceService.stop();
    }
  };

  if (!isSupported) {
    return (
      <div className={`p-2.5 rounded-xl bg-slate-100 border border-slate-200 text-slate-500 text-xs flex items-center gap-2 ${className}`}>
        <Info className="w-4 h-4 text-slate-400 shrink-0" />
        <span>Voice guidance is not supported by this browser.</span>
      </div>
    );
  }

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1.5 ${className}`}>
        {isSpeaking ? (
          <button
            type="button"
            onClick={handleStop}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-sm transition animate-pulse"
            title="Stop Audio / आवाज़ बंद करें"
          >
            <Square className="w-3.5 h-3.5 fill-white" />
            <span>{t('voiceStop') || 'Stop'}</span>
          </button>
        ) : (
          <button
            type="button"
            onClick={handlePlay}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-sm transition"
            title="Play Audio Guidance / निर्देश सुनें"
          >
            <Volume2 className="w-3.5 h-3.5" />
            <span>{t('voicePlay') || 'Play'}</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      className={`p-3.5 sm:p-4 rounded-2xl border transition-all ${
        isSpeaking
          ? 'bg-purple-50/90 border-purple-300 shadow-md ring-2 ring-purple-200'
          : voiceGuidanceEnabled
          ? 'bg-white border-purple-200 shadow-xs'
          : 'bg-slate-50 border-slate-200'
      } ${className}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Status Indicator */}
        <div className="flex items-center gap-2.5">
          <div
            className={`p-2 rounded-xl text-white transition ${
              isSpeaking ? 'bg-purple-600 animate-pulse' : voiceGuidanceEnabled ? 'bg-purple-600' : 'bg-slate-400'
            }`}
          >
            {isSpeaking ? <Volume2 className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-extrabold text-slate-900">
                {t('voiceGuidance') || 'Voice Guidance'}
              </h4>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  isSpeaking
                    ? 'bg-purple-200 text-purple-900 animate-pulse'
                    : voiceGuidanceEnabled
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-slate-200 text-slate-600'
                }`}
              >
                {isSpeaking ? '🔊 Speaking...' : voiceGuidanceEnabled ? 'Voice Guidance: ON' : 'OFF'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">
              {language === 'hi'
                ? 'स्क्रीनिंग निर्देश हिंदी में बोलकर मार्गदर्शन'
                : 'Spoken workflow prompts for health workers'}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {/* Main Play / Stop Button */}
          {isSpeaking ? (
            <button
              type="button"
              onClick={handleStop}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-extrabold shadow-sm transition"
            >
              <Square className="w-3.5 h-3.5 fill-white" />
              <span>{t('voiceStop') || 'Stop Voice'}</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={handlePlay}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-extrabold shadow-sm hover:shadow transition transform hover:scale-102"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>{t('voicePlay') || 'Play Guidance'}</span>
            </button>
          )}

          {/* Toggle ON / OFF */}
          <button
            type="button"
            onClick={handleToggleEnable}
            className={`px-3 py-2 rounded-xl text-xs font-bold border transition ${
              voiceGuidanceEnabled
                ? 'border-purple-300 bg-purple-100 text-purple-900'
                : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-100'
            }`}
          >
            {voiceGuidanceEnabled ? 'Disable' : 'Enable'}
          </button>
        </div>
      </div>

      {/* Spoken Text Preview & Language Notification */}
      <div className="mt-2.5 pt-2.5 border-t border-slate-200/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1.5 text-[11px]">
        <p className="text-slate-600 italic">
          "{getSpokenContent()}"
        </p>

        {language === 'hi' && !hasHindiVoice && (
          <span className="text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-[10px] font-medium shrink-0">
            Hindi voice unavailable on device (using Indian English fallback)
          </span>
        )}
      </div>
    </div>
  );
};
