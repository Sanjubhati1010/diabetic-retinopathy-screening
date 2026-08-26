import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { Dot, Eye, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';

export const BiomarkerTags = ({ biomarkers = [], activeBiomarker, onSelectBiomarker }) => {
  const { t } = useLanguage();

  if (!biomarkers || biomarkers.length === 0) {
    return (
      <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
        <span>No abnormal retinal microvascular lesions detected.</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {biomarkers.map((bm, index) => {
          const isSelected = activeBiomarker === bm;
          return (
            <button
              key={index}
              onClick={() => onSelectBiomarker && onSelectBiomarker(isSelected ? null : bm)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                isSelected
                  ? 'bg-rose-600 text-white border-rose-600 shadow-glow-red scale-105'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-white animate-ping' : 'bg-rose-500'}`} />
              <span>{bm}</span>
            </button>
          );
        })}
      </div>
      <p className="text-[11px] text-slate-400">
        Click any biomarker tag to spotlight its corresponding activation zone in the Grad-CAM visualizer.
      </p>
    </div>
  );
};
