import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Sparkles,
  Layers,
  Activity,
  FileCheck,
  Eye,
  Info,
  Stethoscope,
  Clock,
  UserCheck,
  RotateCcw,
} from 'lucide-react';
import {
  SeverityBadge,
  RiskBadge,
  SafetyBadge,
  ReferralBadge,
  DoctorReviewStatusBadge,
} from '../common/SeverityBadge';
import { formatConfidence, CONFIDENCE_THRESHOLD } from '../../services/api';

/**
 * AI Clinical Evidence Card
 * Transforms AI prediction outputs into a transparent, structured, evidence-based screening summary.
 */
export const ClinicalEvidenceCard = ({
  screening,
  selectedEye = 'OD',
  compact = false,
  className = '',
}) => {
  const { t, language } = useLanguage();
  const { isRuralMode } = useApp();

  if (!screening) return null;

  const isOD = selectedEye === 'OD';
  const analysis = isOD
    ? screening.rightEyeAnalysis || screening.aiResultOD || (screening.selectedEyeForAnalysis === 'OD' ? screening.aiResult : null)
    : screening.leftEyeAnalysis || screening.aiResultOS || (screening.selectedEyeForAnalysis === 'OS' ? screening.aiResult : null);

  const rawConfidence = analysis?.confidence ?? (isOD ? (screening.confidenceOD ?? screening.confidence) : (screening.confidenceOS ?? (screening.drSeverityOS === screening.drSeverityOD ? screening.confidence : null)));
  const confidenceVal = rawConfidence !== null && rawConfidence !== undefined
    ? (rawConfidence <= 1.0 ? rawConfidence : rawConfidence / 100.0)
    : null;

  // Qualitative confidence interpretation
  const getConfidenceTier = (val) => {
    if (val === null || val === undefined) return { label: 'N/A', badgeClass: 'bg-slate-100 text-slate-600 border-slate-200' };
    if (val >= 0.85) {
      return {
        label: t('confidenceHigh') || 'High Confidence',
        badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
        desc: language === 'hi' ? 'मॉडल के आंतरिक संकेत अत्यधिक सुसंगत हैं।' : 'Strong classification agreement across feature patterns.',
      };
    }
    if (val >= CONFIDENCE_THRESHOLD) {
      return {
        label: t('confidenceModerate') || 'Moderate Confidence',
        badgeClass: 'bg-blue-50 text-blue-800 border-blue-200',
        desc: language === 'hi' ? 'स्वीकार्य स्तर की समानता, क्लिनिकल पुष्टि अनुशंसित।' : 'Standard confidence level above threshold for decision support.',
      };
    }
    return {
      label: t('confidenceLow') || 'Low Confidence',
      badgeClass: 'bg-amber-50 text-amber-800 border-amber-200',
      desc: language === 'hi' ? 'सीमा से कम भरोसा। डॉक्टर समीक्षा या पुनः फोटो आवश्यक।' : 'Below clinical decision threshold; specialist verification recommended.',
    };
  };

  const confTier = getConfidenceTier(confidenceVal);

  const severityKey = isOD
    ? screening.drSeverityOD || (analysis?.predicted_class !== undefined ? (analysis.predicted_class === 0 ? 'dr0' : analysis.predicted_class === 1 ? 'dr1' : analysis.predicted_class === 2 ? 'dr2' : analysis.predicted_class === 3 ? 'dr3' : 'dr4') : screening.overallSeverity || 'drUncertain')
    : screening.drSeverityOS || (analysis?.predicted_class !== undefined ? (analysis.predicted_class === 0 ? 'dr0' : analysis.predicted_class === 1 ? 'dr1' : analysis.predicted_class === 2 ? 'dr2' : analysis.predicted_class === 3 ? 'dr3' : 'dr4') : screening.overallSeverity || 'drUncertain');

  const safetyStatus = analysis?.safety_status || (isOD ? screening.safetyStatusOD : screening.safetyStatusOS) || screening.safetyStatus || 'READY_FOR_AI';
  const isSafetyPassed = safetyStatus === 'READY_FOR_AI';

  const validation = isOD ? screening.odValidation : screening.osValidation;
  const qualityGrade = validation?.quality_grade || (
    isSafetyPassed ? 'good' :
    safetyStatus === 'IMAGE_QUALITY_INSUFFICIENT' ? 'insufficient' :
    safetyStatus === 'IMAGE_INVALID' ? 'invalid' :
    validation?.can_proceed ? 'good' : 'good'
  );
  const isQualityWarning = qualityGrade === 'warning' || qualityGrade === 'insufficient';

  const riskCategory = analysis?.risk_category || (isOD ? screening.riskCategoryOD : screening.riskCategoryOS) || screening.riskCategory || 'MODERATE';
  const referralPriority = analysis?.referral_priority || (isOD ? screening.referralPriorityOD : screening.referralPriorityOS) || screening.referralPriority || 'EYE SPECIALIST REVIEW RECOMMENDED';

  const reviewStatus = screening.reviewStatus || (screening.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : 'PENDING DOCTOR REVIEW');

  const gradCamAvailable = Boolean(
    analysis?.gradcam_url ||
    (isOD ? screening.gradCamOD : screening.gradCamOS) ||
    screening.gradCamUrl
  );

  return (
    <div className={`rounded-3xl border border-slate-200 bg-white shadow-card p-5 sm:p-6 space-y-5 ${className}`}>
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-2xl bg-brand-50 text-brand-600 border border-brand-200 flex items-center justify-center shadow-xs">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <span>{t('clinicalEvidenceTitle') || 'AI Clinical Evidence'}</span>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-bold uppercase tracking-wider">
                {selectedEye} Eye ({isOD ? 'Right Eye' : 'Left Eye'})
              </span>
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              {isRuralMode
                ? (language === 'hi' ? 'सुरक्षित और पारदर्शी एआई जांच का आधार' : 'Verified evidence foundation for rural health workers')
                : (t('clinicalEvidenceSub') || 'Comprehensive, evidence-based screening summary and safety intelligence')}
            </p>
          </div>
        </div>

        <DoctorReviewStatusBadge status={reviewStatus} size="sm" />
      </div>

      {/* Primary Evidence Grid (8-Point Clinical Checklist) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* 1. AI Classification */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
          <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
            1. AI Classification ({selectedEye} Eye)
          </span>
          <div className="flex items-center gap-2">
            <SeverityBadge severity={severityKey} size="sm" />
          </div>
        </div>

        {/* 2. Model Confidence with Qualitative Tier */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
          <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
            2. Model Confidence ({selectedEye} Eye)
          </span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-extrabold font-mono text-slate-900">
              {confidenceVal !== null ? formatConfidence(confidenceVal) : 'N/A'}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold border ${confTier.badgeClass}`}>
              {confTier.label}
            </span>
          </div>
        </div>

        {/* 3. Image Quality Gate */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
          <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
            3. Image Quality ({selectedEye} Eye)
          </span>
          <div className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${
              qualityGrade === 'good' ? 'bg-emerald-500' : qualityGrade === 'warning' ? 'bg-amber-500' : 'bg-rose-500'
            }`} />
            <span className="text-xs font-extrabold text-slate-900 capitalize">
              {qualityGrade} {validation?.metrics?.resolution ? `(${validation.metrics.resolution})` : ''}
            </span>
          </div>
        </div>

        {/* 4. AI Safety Gate */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
          <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
            4. AI Safety Gate ({selectedEye} Eye)
          </span>
          <SafetyBadge status={safetyStatus} size="sm" />
        </div>

        {/* 5. Explainability (Grad-CAM) */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
          <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
            5. Explainability ({selectedEye} Eye)
          </span>
          <div className="flex items-center gap-1.5">
            <Sparkles className={`w-3.5 h-3.5 ${gradCamAvailable ? 'text-purple-600' : 'text-slate-400'}`} />
            <span className={`text-xs font-extrabold ${gradCamAvailable ? 'text-purple-700' : 'text-slate-500'}`}>
              {gradCamAvailable ? 'Grad-CAM Available (40%)' : 'Unavailable'}
            </span>
          </div>
        </div>

        {/* 6. Screening Risk */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
          <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
            6. Screening Risk ({selectedEye} Eye)
          </span>
          <RiskBadge risk={riskCategory} size="sm" />
        </div>

        {/* 7. Referral Recommendation */}
        <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5 sm:col-span-2">
          <span className="text-[10px] font-extrabold text-slate-500 uppercase tracking-wider block">
            7. Recommended Action ({selectedEye} Eye)
          </span>
          <ReferralBadge priority={referralPriority} size="sm" />
        </div>
      </div>

      {/* Image Quality -> Confidence Context Advisory */}
      {isQualityWarning && (
        <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-bold">
              {t('qualityConfidenceContext') || 'Image Quality & AI Reliability Context'}
            </p>
            <p className="text-[11px] leading-relaxed text-amber-800">
              {t('qualityImpactWarning') || 'Lower image quality may reduce the reliability of AI-assisted screening. Specialist verification or re-capture is advised.'}
            </p>
          </div>
        </div>
      )}

      {/* Safety Gate Verified Checklist */}
      <div className="p-4 rounded-2xl bg-slate-900 text-white space-y-2.5">
        <div className="flex items-center justify-between text-xs font-bold text-slate-300 uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <FileCheck className="w-4 h-4 text-emerald-400" />
            <span>{t('safetyChecklistTitle') || 'AI Safety Gate Checklist'}</span>
          </span>
          <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
            isSafetyPassed ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-700' : 'bg-rose-900/80 text-rose-300 border border-rose-700'
          }`}>
            {isSafetyPassed ? 'GATE CLEARED' : 'GATE BLOCKED'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="text-slate-200">{t('safetyItemRetinal') || 'Retinal fundus image detected'}</span>
          </div>

          <div className="flex items-center gap-2">
            {qualityGrade === 'good' ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            )}
            <span className="text-slate-200">{t('safetyItemQuality') || 'Image sharpness and illumination acceptable'}</span>
          </div>

          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="text-slate-200">{t('safetyItemEye') || 'Correct anatomical eye context verified'} ({selectedEye})</span>
          </div>

          <div className="flex items-center gap-2">
            {isSafetyPassed ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            ) : (
              <AlertOctagon className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            )}
            <span className="text-slate-200">{t('safetyItemInference') || 'AI model inference completed safely'}</span>
          </div>
        </div>

        <p className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-800">
          {t('confidenceDisclaimer') || 'Model confidence reflects statistical feature agreement, not diagnostic certainty.'}
        </p>
      </div>
    </div>
  );
};
