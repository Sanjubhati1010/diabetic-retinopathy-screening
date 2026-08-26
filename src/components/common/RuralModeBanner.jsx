import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import {
  Compass,
  Wifi,
  Volume2,
  VolumeX,
  Sparkles,
  Zap,
  Check,
  Smartphone,
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

  return (
    <div className="no-print bg-slate-900 text-white px-3 sm:px-6 py-2 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2.5 text-xs">
      {/* Left: Rural Badge & Guidance */}
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-teal-500/20 text-teal-300 border border-teal-500/30 text-[11px] font-bold">
          <Compass className="w-3.5 h-3.5 text-teal-400" />
          <span>PHC Field Deployment</span>
        </span>
        <span className="text-slate-400 hidden sm:inline text-[11px]">
          {language === 'hi'
            ? 'ग्रामीण स्वास्थ्य शिविर एवं प्राथमिक स्वास्थ्य केंद्र अनुकूलन'
            : 'Optimized for Rural Camps & Vision Technicians'}
        </span>
      </div>

      {/* Right: 3 Core Deployment Toggles */}
      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
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

        {/* 3. Voice Guidance Toggle */}
        <button
          type="button"
          onClick={toggleVoiceGuidance}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-bold text-[11px] transition border ${
            voiceGuidanceEnabled
              ? 'bg-purple-600 text-white border-purple-500 shadow-sm'
              : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
          }`}
          title="Audible step-by-step spoken workflow instructions"
        >
          {voiceGuidanceEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
          <span>{t('voiceGuidance')}</span>
          {voiceGuidanceEnabled && <span className="w-1.5 h-1.5 rounded-full bg-purple-300 animate-pulse"></span>}
        </button>
      </div>
    </div>
  );
};
