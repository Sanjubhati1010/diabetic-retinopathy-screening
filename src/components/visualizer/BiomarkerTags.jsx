import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { Eye, Sparkles, CheckCircle2, Info, AlertTriangle } from 'lucide-react';

/**
 * AI Attention / Visual Evidence Regions Component
 * Reframed to accurately represent model attention regions rather than unvalidated lesion detections.
 */
export const BiomarkerTags = ({ biomarkers = [], activeBiomarker, onSelectBiomarker }) => {
  const { t, language } = useLanguage();

  if (!biomarkers || biomarkers.length === 0) {
    return (
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-500 font-medium">
        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
        <span>
          {language === 'hi'
            ? 'कोई असामान्य रेटिना ध्यान केंद्र चिन्हित नहीं है।'
            : 'No abnormal attention clusters detected.'}
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <div className="flex flex-wrap gap-2">
        {biomarkers.map((bm, index) => {
          const isSelected = activeBiomarker === bm;
          return (
            <button
              key={index}
              type="button"
              onClick={() => onSelectBiomarker && onSelectBiomarker(isSelected ? null : bm)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                isSelected
                  ? 'bg-purple-600 text-white border-purple-600 shadow-sm scale-105'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-purple-300 hover:bg-purple-50/50'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-white animate-ping' : 'bg-purple-500'}`} />
              <span>{bm}</span>
            </button>
          );
        })}
      </div>

      <div className="flex items-start gap-1.5 text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
        <Info className="w-3.5 h-3.5 text-purple-600 shrink-0 mt-0.5" />
        <p className="leading-normal">
          {t('aiAttentionDisclaimer') ||
            'These regions represent model attention and should not be interpreted as confirmed lesions.'}
        </p>
      </div>
    </div>
  );
};
