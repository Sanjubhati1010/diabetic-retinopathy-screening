import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { GradCamViewer } from '../components/visualizer/GradCamViewer';
import { SeverityBadge, ScreeningStatusBadge, SafetyBadge } from '../components/common/SeverityBadge';
import { ClinicalEvidenceCard } from '../components/evidence/ClinicalEvidenceCard';
import { GradCamEvidenceSummary } from '../components/evidence/GradCamEvidenceSummary';
import { DualEvidenceViewer } from '../components/evidence/DualEvidenceViewer';
import {
  Sparkles,
  Info,
  CheckCircle2,
  ChevronLeft,
  FileText,
  AlertTriangle,
  Eye,
  HelpCircle,
} from 'lucide-react';
import { DemoDisclaimer } from '../components/common/DemoDisclaimer';
import { SAMPLE_FUNDUS_IMAGES } from '../data/mockData';
import {
  getFullResultUrl,
  formatConfidence,
  getSeverityKeyFromClass,
  CONFIDENCE_THRESHOLD,
} from '../services/api';

export const ExplainableAiPage = () => {
  const { id } = useParams();
  const { t } = useLanguage();
  const { getScreeningById, screenings, activeScreening } = useApp();
  const navigate = useNavigate();

  // Find the target screening
  const latestRealScreening = screenings.find(
    (s) => s.isRealPrediction || s.gradCamUrl || s.confidence !== null
  );

  let screening = id ? getScreeningById(id) : (latestRealScreening || null);

  if (!screening) {
    screening =
      activeScreening.aiResult || activeScreening.rightEyeAnalysis || activeScreening.leftEyeAnalysis
        ? {
            id: activeScreening.id || id || 'SCR-CURRENT',
            patientId: activeScreening.patientId || 'PAT-2026-081',
            patientName: activeScreening.patientName || 'Sanjay Bhati',
            imageOD: activeScreening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od,
            imageOS: activeScreening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os,
            rightEyeAnalysis: activeScreening.rightEyeAnalysis || activeScreening.aiResultOD,
            leftEyeAnalysis: activeScreening.leftEyeAnalysis || activeScreening.aiResultOS,
            overallSeverity: activeScreening.overallSeverity || 'dr2',
            className: activeScreening.className || activeScreening.rightEyeAnalysis?.class_name,
            confidence: activeScreening.confidence || activeScreening.rightEyeAnalysis?.confidence,
            gradCamOD: activeScreening.rightEyeAnalysis?.gradcam_url
              ? getFullResultUrl(activeScreening.rightEyeAnalysis.gradcam_url)
              : null,
            gradCamOS: activeScreening.leftEyeAnalysis?.gradcam_url
              ? getFullResultUrl(activeScreening.leftEyeAnalysis.gradcam_url)
              : null,
            isRealPrediction: true,
          }
        : latestRealScreening || (screenings && screenings[0]) || {
            id: id || 'SCR-2026-1024',
            patientId: 'PAT-2026-081',
            patientName: 'Sanjay Bhati',
            imageOD: SAMPLE_FUNDUS_IMAGES.sample_od,
            imageOS: SAMPLE_FUNDUS_IMAGES.sample_os,
            overallSeverity: 'dr2',
            className: 'Moderate',
            confidence: 0.85,
            isRealPrediction: false,
          };
  }

  if (id && screening.id !== id && !screenings.some((s) => s.id === id)) {
    screening = {
      ...screening,
      id: id,
    };
  }

  if (screening && !screening.isRealPrediction && !screening.gradCamUrl && latestRealScreening) {
    screening = {
      ...latestRealScreening,
      id: screening.id || id || latestRealScreening.id,
      patientId: screening.patientId || latestRealScreening.patientId,
      patientName: screening.patientName || latestRealScreening.patientName,
    };
  }

  const [selectedEye, setSelectedEye] = useState(
    activeScreening.selectedEyeForAnalysis || 'OD'
  );

  // Bilateral analysis separation
  const rightEyeAnalysis =
    screening.rightEyeAnalysis ||
    screening.aiResultOD ||
    (screening.selectedEyeForAnalysis === 'OD' ? screening.aiResult : null);

  const leftEyeAnalysis =
    screening.leftEyeAnalysis ||
    screening.aiResultOS ||
    (screening.selectedEyeForAnalysis === 'OS' ? screening.aiResult : null);

  const isOD = selectedEye === 'OD';
  const currentAnalysis = isOD ? rightEyeAnalysis : leftEyeAnalysis;

  const currentOriginal = isOD
    ? screening.imageOD || activeScreening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od
    : screening.imageOS || activeScreening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os;

  const rawGradCamPath = isOD
    ? rightEyeAnalysis?.gradcam_url || screening.gradCamOD || (screening.selectedEyeForAnalysis === 'OD' ? screening.gradCamUrl : null)
    : leftEyeAnalysis?.gradcam_url || screening.gradCamOS || (screening.selectedEyeForAnalysis === 'OS' ? screening.gradCamUrl : null);

  const rawHeatmapPath = isOD
    ? rightEyeAnalysis?.heatmap_url || screening.heatmapOD
    : leftEyeAnalysis?.heatmap_url || screening.heatmapOS;

  const gradcamImageUrl = getFullResultUrl(rawGradCamPath);
  const heatmapImageUrl = getFullResultUrl(rawHeatmapPath) || gradcamImageUrl;

  const isEyeAnalyzed = Boolean(currentAnalysis && gradcamImageUrl);
  const isReal = Boolean(rightEyeAnalysis || leftEyeAnalysis || screening.isRealPrediction);

  const currentSeverity = isOD
    ? screening.drSeverityOD || (rightEyeAnalysis ? getSeverityKeyFromClass(rightEyeAnalysis.predicted_class) : 'drUncertain')
    : screening.drSeverityOS || (leftEyeAnalysis ? getSeverityKeyFromClass(leftEyeAnalysis.predicted_class) : 'drUncertain');

  const currentConfidence = currentAnalysis?.confidence ?? (isEyeAnalyzed ? screening.confidence : null);
  const currentClassName = currentAnalysis?.class_name || (isEyeAnalyzed ? screening.className : 'Not Analyzed');

  const safetyStatus = currentAnalysis?.safety_status || (isOD ? screening.safetyStatusOD : screening.safetyStatusOS) || 'READY_FOR_AI';
  const safetyBlocked = safetyStatus !== 'READY_FOR_AI';
  const isLowConfidence = currentConfidence !== null && (currentConfidence <= 1.0 ? currentConfidence : currentConfidence / 100.0) < CONFIDENCE_THRESHOLD;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Subtle Demo Data Notice */}
      <div>
        <DemoDisclaimer text="DEMO DATA — NOT REAL MEDICAL RESULTS • Grad-CAM explainability decision support." />
      </div>

      {/* Top Navigation & Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate(`/screenings/${screening.id}/result`)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition mr-1"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-600" />
              <span>{t('xaiTitle')}</span>
            </h1>
          </div>
          <p className="text-xs text-slate-500 pl-8">
            {isEyeAnalyzed
              ? `Visual explainability for ${screening.patientName} (${selectedEye}: ${currentClassName}) • Confidence: ${formatConfidence(currentConfidence)}`
              : isReal
              ? `Visual explainability for ${screening.patientName} • ${selectedEye}: Not analyzed yet`
              : t('xaiSubtitle')}
          </p>
        </div>

        <div className="flex items-center gap-2 pl-8 sm:pl-0">
          {isEyeAnalyzed ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>{selectedEye} Grad-CAM Active</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">
              <Sparkles className="w-3.5 h-3.5 text-slate-400" />
              <span>{selectedEye} Not analyzed yet</span>
            </span>
          )}
          <Link
            to={`/screenings/${screening.id}/report`}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-glow transition"
          >
            <FileText className="w-4 h-4" />
            <span>Generate Report</span>
          </Link>
        </div>
      </div>

      {/* Phase 8: AI Clinical Evidence Card */}
      <ClinicalEvidenceCard screening={screening} selectedEye={selectedEye} />

      {/* Phase 9: Dual-Evidence Analysis Workspace */}
      <DualEvidenceViewer
        screening={screening}
        selectedEye={selectedEye}
        onEyeChange={setSelectedEye}
      />

      {/* Interpretation & Clinical Context Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Healthcare Worker Interpretation Box */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <HelpCircle className="w-4 h-4 text-purple-600" />
            <span>{t('whatThisMeansTitle')} ({selectedEye})</span>
          </h3>

          {/* Bilingual Simple Explanations */}
          <div className="space-y-3">
            <div className="p-3 rounded-2xl bg-purple-50/70 border border-purple-200 text-xs space-y-1 text-purple-950">
              <span className="font-bold text-[10px] uppercase tracking-wider text-purple-800 block">English</span>
              <p className="leading-relaxed font-medium">{t('simpleExplanationEn')}</p>
            </div>

            <div className="p-3 rounded-2xl bg-indigo-50/70 border border-indigo-200 text-xs space-y-1 text-indigo-950">
              <span className="font-bold text-[10px] uppercase tracking-wider text-indigo-800 block">हिन्दी (Hindi)</span>
              <p className="leading-relaxed font-medium font-hindi">{t('simpleExplanationHi')}</p>
            </div>
          </div>
        </div>

        {/* Clinical Limitation Notice */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-3 flex flex-col justify-between">
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-3">
              <Info className="w-3.5 h-3.5 text-brand-600" />
              <span>{t('limitationTitle')}</span>
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              {t('limitationText')}
            </p>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 text-[11px] text-slate-500">
            {t('confidenceSeparationNotice')}
          </div>
        </div>
      </div>
    </div>
  );
};
