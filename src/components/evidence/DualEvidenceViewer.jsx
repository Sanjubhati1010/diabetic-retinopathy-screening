import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import {
  Layers,
  Sparkles,
  ShieldCheck,
  Activity,
  AlertTriangle,
  Info,
  CheckCircle2,
  HelpCircle,
  Eye,
  Stethoscope,
  Clock,
  FileCheck,
} from 'lucide-react';
import { SeverityBadge, RiskBadge, DoctorReviewStatusBadge } from '../common/SeverityBadge';
import { GradCamViewer } from '../visualizer/GradCamViewer';
import { formatConfidence, getFullResultUrl } from '../../services/api';

/**
 * Dual-Evidence Analysis Component (Phase 9)
 * Conceptual separation of:
 * 1. DR Classification (EfficientNet-B0 Grade + Confidence)
 * 2. Lesion Evidence (Available / Unavailable state + supported categories)
 * 3. Grad-CAM Model Attention (Original, Heatmap, 40% Overlay)
 * Plus Clinical Evidence Comparison Matrix.
 */
export const DualEvidenceViewer = ({
  screening,
  selectedEye = 'OD',
  onEyeChange,
  className = '',
}) => {
  const { t, language } = useLanguage();
  const { isRuralMode } = useApp();

  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'classification' | 'lesion' | 'gradcam'

  if (!screening) return null;

  const isOD = selectedEye === 'OD';
  const analysis = isOD
    ? screening.rightEyeAnalysis || screening.aiResultOD || (screening.selectedEyeForAnalysis === 'OD' ? screening.aiResult : null)
    : screening.leftEyeAnalysis || screening.aiResultOS || (screening.selectedEyeForAnalysis === 'OS' ? screening.aiResult : null);

  const rawConfidence = analysis?.confidence ?? (isOD ? (screening.confidenceOD ?? screening.confidence) : (screening.confidenceOS ?? (screening.drSeverityOS === screening.drSeverityOD ? screening.confidence : null)));
  const confidenceVal = rawConfidence !== null && rawConfidence !== undefined
    ? (rawConfidence <= 1.0 ? rawConfidence : rawConfidence / 100.0)
    : null;

  const severityKey = isOD
    ? screening.drSeverityOD || (analysis?.predicted_class !== undefined ? (analysis.predicted_class === 0 ? 'dr0' : analysis.predicted_class === 1 ? 'dr1' : analysis.predicted_class === 2 ? 'dr2' : analysis.predicted_class === 3 ? 'dr3' : 'dr4') : screening.overallSeverity || 'drUncertain')
    : screening.drSeverityOS || (analysis?.predicted_class !== undefined ? (analysis.predicted_class === 0 ? 'dr0' : analysis.predicted_class === 1 ? 'dr1' : analysis.predicted_class === 2 ? 'dr2' : analysis.predicted_class === 3 ? 'dr3' : 'dr4') : screening.overallSeverity || 'drUncertain');

  const currentOriginal = isOD ? screening.imageOD : screening.imageOS;
  const gradcamImageUrl = isOD
    ? getFullResultUrl(screening.gradCamOD || analysis?.gradcam_url || screening.gradCamUrl)
    : getFullResultUrl(screening.gradCamOS || analysis?.gradcam_url || screening.gradCamUrl);
  const heatmapImageUrl = isOD
    ? getFullResultUrl(screening.heatmapOD || analysis?.heatmap_url || screening.gradCamOD || screening.gradCamUrl)
    : getFullResultUrl(screening.heatmapOS || analysis?.heatmap_url || screening.gradCamOS || screening.gradCamUrl);

  const reviewStatus = screening.reviewStatus || (screening.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : 'PENDING DOCTOR REVIEW');

  const plannedLesionCategories = [
    'Microaneurysms',
    'Hemorrhages',
    'Hard Exudates',
    'Cotton-Wool Spots',
  ];

  return (
    <div className={`rounded-3xl border border-slate-200 bg-white shadow-card p-5 sm:p-7 space-y-6 ${className}`}>
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 border border-indigo-200 flex items-center justify-center shadow-xs">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <span>{t('dualEvidenceTitle') || 'Dual-Evidence Analysis'}</span>
                <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-bold uppercase tracking-wider">
                  {selectedEye} Eye ({isOD ? 'Right Eye' : 'Left Eye'})
                </span>
              </h3>
              <p className="text-xs text-slate-500 font-medium">
                {isRuralMode
                  ? (language === 'hi' ? 'एआई परिणाम, असामान्य हिस्से और Grad-CAM का अलग-अलग विश्लेषण' : 'Separated evidence streams for rural decision support')
                  : (t('dualEvidenceSub') || 'Independent side-by-side evaluation of DR classification, lesion intelligence, and Grad-CAM attention')}
              </p>
            </div>
          </div>
        </div>

        {/* Eye Switcher */}
        {onEyeChange && (
          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-2xl border border-slate-200">
            <button
              type="button"
              onClick={() => onEyeChange('OD')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                selectedEye === 'OD'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Right Eye (OD)
            </button>
            <button
              type="button"
              onClick={() => onEyeChange('OS')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                selectedEye === 'OS'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Left Eye (OS)
            </button>
          </div>
        )}
      </div>

      {/* 3 Distinct Evidence Streams Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Stream A: DR Classification (4 cols) */}
        <div className="lg:col-span-4 rounded-2xl bg-slate-50 border border-slate-200 p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
              <span className="text-xs font-extrabold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-brand-600" />
                <span>1. DR Classification ({selectedEye} Eye)</span>
              </span>
              <span className="text-[10px] font-mono font-bold bg-brand-50 text-brand-700 px-2 py-0.5 rounded border border-brand-200">
                EfficientNet-B0
              </span>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500 font-medium">{selectedEye} Predicted Grade:</span>
                <SeverityBadge severity={severityKey} size="sm" />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500 font-medium">{selectedEye} Model Confidence:</span>
                <span className="text-xs font-extrabold font-mono text-slate-900">
                  {confidenceVal !== null ? formatConfidence(confidenceVal) : 'N/A'}
                </span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white border border-slate-200 text-[11px] text-slate-600 leading-relaxed space-y-1">
              <span className="font-bold text-slate-800 block">Whole-Image Statistical Agreement:</span>
              <p>
                Represents model classification agreement across global fundus feature vectors for the {selectedEye} ({isOD ? 'Right' : 'Left'}) eye.
              </p>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-100 text-[10px] text-slate-500 italic">
            Classification inference is distinct and not merged with lesion detection.
          </div>
        </div>

        {/* Stream B: Lesion Intelligence Layer (4 cols) */}
        <div className="lg:col-span-4 rounded-2xl bg-amber-50/40 border border-amber-200 p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-amber-200">
              <span className="text-xs font-extrabold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-amber-600" />
                <span>2. Lesion Evidence</span>
              </span>
              <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded border border-amber-300">
                Unavailable (Standby)
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white/90 border border-amber-200 text-xs space-y-2">
              <div className="flex items-center gap-1.5 text-amber-950 font-bold text-[11px]">
                <Info className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                <span>{t('lesionAnalysisUnavailable') || 'Lesion-specific analysis is not currently available'}</span>
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                {t('lesionModelNotConnected') ||
                  'No dedicated lesion detection model is currently connected. Grad-CAM provides model-attention visualization only; it does not confirm individual lesions.'}
              </p>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                PLANNED / SUPPORTED LESION CATEGORIES:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {plannedLesionCategories.map((cat, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-medium px-2 py-0.5 rounded-lg bg-white border border-slate-200 text-slate-600"
                  >
                    {cat} (Standby)
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-amber-100/60 text-[10px] text-amber-900 font-medium">
            Clinical Safety Guarantee: Zero fake lesion counts or fabricated segmentations.
          </div>
        </div>

        {/* Stream C: Grad-CAM Model Attention (4 cols) */}
        <div className="lg:col-span-4 rounded-2xl bg-purple-50/50 border border-purple-200 p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-purple-200">
              <span className="text-xs font-extrabold uppercase tracking-wider text-purple-950 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span>3. Grad-CAM Model Attention ({selectedEye} Eye)</span>
              </span>
              <span className="text-[10px] font-bold bg-purple-100 text-purple-800 px-2 py-0.5 rounded border border-purple-300">
                Active (40% Default)
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white/90 border border-purple-200 text-xs space-y-1.5">
              <div className="flex items-center gap-1.5 text-purple-900 font-bold text-[11px]">
                <HelpCircle className="w-3.5 h-3.5 text-purple-600 shrink-0" />
                <span>{t('whyAiFocusedHere') || 'Why did the AI focus here?'}</span>
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Highlighted regions indicate image areas that contributed to the model prediction. Grad-CAM provides model-attention visualization only; it does not confirm individual lesions.
              </p>
            </div>
          </div>

          <div className="p-2.5 rounded-xl bg-purple-100/70 text-[10px] text-purple-950 font-medium">
            Grad-CAM shows computational model attention, not confirmed lesions.
          </div>
        </div>
      </div>

      {/* Interactive Grad-CAM Tri-View Inspector */}
      <div className="space-y-3">
        <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-600" />
          <span>Interactive Attention Visualizer ({selectedEye} Eye)</span>
        </h4>
        <GradCamViewer
          originalImage={currentOriginal}
          heatmapImage={gradcamImageUrl}
          heatmapUrl={heatmapImageUrl}
          confidence={confidenceVal}
          severity={severityKey}
          selectedEye={selectedEye}
          onEyeChange={onEyeChange}
          showControls={true}
        />
      </div>

      {/* Clinical Evidence Source Comparison Matrix */}
      <div className="rounded-2xl border border-slate-200 overflow-hidden space-y-0">
        <div className="p-3.5 bg-slate-900 text-white flex items-center justify-between">
          <span className="text-xs font-extrabold uppercase tracking-wider flex items-center gap-2">
            <FileCheck className="w-4 h-4 text-teal-400" />
            <span>Clinical Evidence Source Comparison ({selectedEye} Eye)</span>
          </span>
          <span className="text-[10px] text-slate-300 font-mono">4 Independent Modalities</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-extrabold text-[10px] uppercase tracking-wider">
                <th className="p-3">{t('evidenceSource') || 'Evidence Source'}</th>
                <th className="p-3">{t('evidenceType') || 'Type & Purpose'}</th>
                <th className="p-3">{t('evidenceStatus') || 'Current Status'}</th>
                <th className="p-3">{t('evidenceFindings') || 'Clinical Interpretation'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {/* Row 1: DR Classification */}
              <tr className="hover:bg-slate-50/70 transition">
                <td className="p-3 font-bold text-slate-900 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-brand-600" />
                  <span>DR Classification ({selectedEye} Eye)</span>
                </td>
                <td className="p-3 text-slate-500">EfficientNet-B0 Whole-Image Classifier</td>
                <td className="p-3">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Active ({confidenceVal !== null ? formatConfidence(confidenceVal) : 'N/A'})</span>
                  </span>
                </td>
                <td className="p-3 font-bold text-slate-900">{t(severityKey) || 'Moderate NPDR'}</td>
              </tr>

              {/* Row 2: Lesion Analysis */}
              <tr className="hover:bg-slate-50/70 transition">
                <td className="p-3 font-bold text-slate-900 flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-amber-600" />
                  <span>Lesion Intelligence</span>
                </td>
                <td className="p-3 text-slate-500">Pathological Lesion Detection & Segmentation</td>
                <td className="p-3">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                    <Info className="w-3 h-3 text-amber-600" />
                    <span>Unavailable (Standby)</span>
                  </span>
                </td>
                <td className="p-3 text-slate-500 italic">
                  Lesion-specific analysis not connected. No fake detections.
                </td>
              </tr>

              {/* Row 3: Grad-CAM */}
              <tr className="hover:bg-slate-50/70 transition">
                <td className="p-3 font-bold text-slate-900 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                  <span>Grad-CAM Attention ({selectedEye} Eye)</span>
                </td>
                <td className="p-3 text-slate-500">Layer Gradients Attention Saliency Mapping</td>
                <td className="p-3">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-800 border border-purple-200">
                    <CheckCircle2 className="w-3 h-3 text-purple-600" />
                    <span>Available (40% Opacity)</span>
                  </span>
                </td>
                <td className="p-3 text-slate-600">Model attention visual overlay on retinal vessels; does not confirm clinical lesions.</td>
              </tr>

              {/* Row 4: Doctor Review */}
              <tr className="hover:bg-slate-50/70 transition">
                <td className="p-3 font-bold text-slate-900 flex items-center gap-1.5">
                  <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                  <span>Doctor Review</span>
                </td>
                <td className="p-3 text-slate-500">Tele-Ophthalmologist Specialist Sign-off</td>
                <td className="p-3">
                  <DoctorReviewStatusBadge status={reviewStatus} size="sm" />
                </td>
                <td className="p-3 font-medium text-slate-700">
                  {screening.doctorComment || 'Clinical verification of AI evidence package'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="p-3 bg-slate-50 border-t border-slate-200 text-[10px] text-slate-500 italic flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>
            {t('confidenceSeparationNotice') ||
              'Classification confidence reflects whole-image statistical pattern agreement and is strictly separated from lesion-specific detection.'}
          </span>
        </div>
      </div>
    </div>
  );
};
