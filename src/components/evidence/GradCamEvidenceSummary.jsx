import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { Sparkles, HelpCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

/**
 * Grad-CAM Evidence Summary Component
 * Explains "Why did the AI focus here?" without claiming to be a lesion detector.
 */
export const GradCamEvidenceSummary = ({ selectedEye = 'OD', className = '' }) => {
  const { t, language } = useLanguage();

  return (
    <div className={`rounded-3xl border border-purple-200 bg-purple-50/50 p-5 sm:p-6 space-y-3.5 ${className}`}>
      <div className="flex items-center gap-2 text-purple-950 font-bold text-sm">
        <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
          <HelpCircle className="w-4.5 h-4.5" />
        </div>
        <div>
          <h4 className="text-sm font-extrabold text-purple-950">
            {t('whyAiFocusedHere') || 'Why did the AI focus here?'}
          </h4>
          <span className="text-[11px] text-purple-700 font-medium">
            Grad-CAM Attention Mapping ({selectedEye} Eye)
          </span>
        </div>
      </div>

      <div className="space-y-2 text-xs text-purple-950 leading-relaxed font-medium">
        <p>
          {t('gradcamEvidenceExplain') ||
            'Highlighted regions represent areas that contributed to the model prediction. These are model attention regions and are not independent lesion diagnoses.'}
        </p>

        <div className="p-3 rounded-2xl bg-white/80 border border-purple-200/80 space-y-1 text-[11px]">
          <div className="flex items-center gap-1.5 font-bold text-purple-900">
            <Info className="w-3.5 h-3.5 text-purple-600 shrink-0" />
            <span>Clinical Notice on Explainability:</span>
          </div>
          <p className="text-slate-600">
            Grad-CAM visualizes gradients flowing into the final convolutional layer (conv_head) of the neural network. 
            Warm colored zones (red/yellow) indicate higher computational influence toward the classification decision. 
            They should always be correlated with professional slit-lamp or funduscopic examination.
          </p>
        </div>
      </div>
    </div>
  );
};
