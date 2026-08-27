import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import {
  SeverityBadge,
  DoctorReviewStatusBadge,
} from '../common/SeverityBadge';
import { calculateLongitudinalComparison, formatConfidence, getFullResultUrl } from '../../services/api';
import {
  History,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  AlertOctagon,
  Eye,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Info,
  Layers,
  ChevronDown,
} from 'lucide-react';

export const ClassificationChangeBadge = ({ status, size = 'md' }) => {
  const { t } = useLanguage();

  let bg = 'bg-slate-100 text-slate-700 border-slate-200';
  let icon = Minus;
  let label = t('statusUnchanged') || 'Unchanged';

  if (status === 'CLASSIFICATION INCREASED') {
    bg = 'bg-amber-100 text-amber-900 border-amber-300';
    icon = TrendingUp;
    label = t('statusIncreased') || 'Classification Increased';
  } else if (status === 'CLASSIFICATION DECREASED' || status === 'IMPROVED') {
    bg = 'bg-emerald-100 text-emerald-900 border-emerald-300';
    icon = TrendingDown;
    label = t('statusDecreased') || 'Classification Decreased';
  } else if (status === 'NOT COMPARABLE') {
    bg = 'bg-rose-100 text-rose-900 border-rose-300';
    icon = AlertOctagon;
    label = t('statusNotComparable') || 'Not Comparable';
  } else if (status === 'HISTORY UNAVAILABLE') {
    bg = 'bg-slate-100 text-slate-600 border-slate-300';
    icon = Info;
    label = t('statusHistoryUnavailable') || 'History Unavailable';
  }

  const IconComp = icon;
  const padding = size === 'sm' ? 'px-2.5 py-1 text-[11px]' : 'px-3.5 py-1.5 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-xl font-extrabold border ${bg} ${padding} shadow-xs`}>
      <IconComp className="w-3.5 h-3.5 shrink-0" />
      <span>{label}</span>
    </span>
  );
};

export const LongitudinalComparisonCard = ({
  currentScreening,
  selectedPreviousId,
  onSelectPreviousId,
  className = '',
}) => {
  const { t, language } = useLanguage();
  const { getPatientScreenings, getLatestComparableScreening } = useApp();

  const [selectedEye, setSelectedEye] = useState('OD');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [syncZoom, setSyncZoom] = useState(true);

  const patientId = currentScreening?.patientId || currentScreening?.patient_id || 'PAT-2026-081';
  const allPatientScreenings = getPatientScreenings(patientId);

  // Available previous screenings (excluding the current screening itself)
  const currentId = currentScreening?.id || currentScreening?.screening_id;
  const previousOptions = allPatientScreenings.filter(
    (s) => (s.id || s.screening_id) !== currentId
  );

  // Determine active previous screening
  const activePrevious =
    previousOptions.find((s) => (s.id || s.screening_id) === selectedPreviousId) ||
    previousOptions[0] ||
    null;

  // Compute canonical comparison
  const comparison = calculateLongitudinalComparison(currentScreening, activePrevious);

  const isHi = language === 'hi';
  const changeSummary = isHi
    ? comparison?.classification_change_summary_hi
    : comparison?.classification_change_summary;
  const clinicalRec = isHi
    ? comparison?.clinical_recommendation_hi
    : comparison?.clinical_recommendation;

  const prevImage =
    selectedEye === 'OD'
      ? activePrevious?.imageOD || activePrevious?.image_od || '/samples/eyes.png'
      : activePrevious?.imageOS || activePrevious?.image_os || '/samples/eyes_os.png';

  const currImage =
    selectedEye === 'OD'
      ? currentScreening?.imageOD || currentScreening?.image_od || '/samples/eyes.png'
      : currentScreening?.imageOS || currentScreening?.image_os || '/samples/eyes_os.png';

  const prevGradCam =
    selectedEye === 'OD'
      ? activePrevious?.gradCamOD || activePrevious?.gradcam_od || activePrevious?.gradCamUrl
      : activePrevious?.gradCamOS || activePrevious?.gradcam_os || activePrevious?.gradCamUrl;

  const currGradCam =
    selectedEye === 'OD'
      ? currentScreening?.gradCamOD || currentScreening?.gradcam_od || currentScreening?.gradCamUrl
      : currentScreening?.gradCamOS || currentScreening?.gradcam_os || currentScreening?.gradCamUrl;

  return (
    <div className={`bg-white rounded-3xl border border-slate-200 shadow-card p-6 space-y-6 ${className}`}>
      {/* Header & Screening Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-teal-100 text-teal-800 flex items-center justify-center font-bold">
            <History className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-extrabold text-slate-900">
                {t('longitudinalOverview') || 'Longitudinal Screening Overview'}
              </h3>
              <ClassificationChangeBadge status={comparison?.classification_change_status} size="sm" />
            </div>
            <p className="text-xs text-slate-500 font-medium">
              {t('longitudinalSub') || 'Chronological patient tracking and multi-visit screening comparison'}
            </p>
          </div>
        </div>

        {/* Previous Screening Selector */}
        {previousOptions.length > 0 ? (
          <div className="flex items-center gap-2 bg-slate-50 p-2 rounded-2xl border border-slate-200 text-xs">
            <label className="font-bold text-slate-600 pl-1 shrink-0">
              {t('selectPreviousScreening') || 'Compare With'}:
            </label>
            <div className="relative">
              <select
                value={activePrevious?.id || activePrevious?.screening_id || ''}
                onChange={(e) => onSelectPreviousId && onSelectPreviousId(e.target.value)}
                className="py-1.5 pl-3 pr-8 rounded-xl bg-white border border-slate-300 font-bold text-slate-800 focus:ring-2 focus:ring-teal-500 text-xs cursor-pointer"
              >
                {previousOptions.map((opt) => (
                  <option key={opt.id || opt.screening_id} value={opt.id || opt.screening_id}>
                    {opt.screeningDate || opt.date} ({opt.className || opt.overallSeverity})
                  </option>
                ))}
              </select>
            </div>
          </div>
        ) : (
          <span className="text-xs font-bold text-slate-400 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
            {t('prevScreeningNotAvailable') || 'Previous screening history is unavailable.'}
          </span>
        )}
      </div>

      {/* Main Classification Change Highlight Banner */}
      <div className={`p-4 rounded-2xl border text-xs space-y-1.5 ${
        comparison?.classification_change_status === 'CLASSIFICATION INCREASED'
          ? 'bg-amber-50/80 border-amber-300 text-amber-950'
          : comparison?.classification_change_status === 'CLASSIFICATION DECREASED'
          ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
          : comparison?.classification_change_status === 'NOT COMPARABLE'
          ? 'bg-rose-50/80 border-rose-300 text-rose-950'
          : 'bg-slate-50 border-slate-200 text-slate-800'
      }`}>
        <div className="flex items-center justify-between">
          <span className="font-extrabold uppercase tracking-wider text-[11px] flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>{t('screeningClassificationChange') || 'Screening Classification Change'}</span>
          </span>
          <span className="text-[10px] font-mono text-slate-500">
            Visit Comparison
          </span>
        </div>
        <p className="font-bold text-sm">{changeSummary}</p>
        <p className="text-[11px] font-medium text-slate-600 flex items-center gap-1.5 pt-0.5">
          <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
          <span>{clinicalRec}</span>
        </p>
      </div>

      {/* Side-by-Side Dual Screening Cards (Previous vs Current) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Previous Screening Card */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200/70 pb-2">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500 block">
                {t('previousScreening') || 'Previous Screening'}
              </span>
              <span className="text-xs font-bold text-slate-900">
                {activePrevious?.screeningDate || activePrevious?.date || 'No Date'}
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              {activePrevious?.id || activePrevious?.screening_id || 'N/A'}
            </span>
          </div>

          {activePrevious ? (
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">AI Classification:</span>
                <span className="font-extrabold text-slate-900">
                  {activePrevious.className || activePrevious.overallSeverity || 'Mild DR'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">AI Confidence:</span>
                <span className="font-bold text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200 font-mono text-[11px]">
                  {formatConfidence(activePrevious.confidence || 0.78)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Doctor Review:</span>
                <DoctorReviewStatusBadge
                  status={activePrevious.reviewStatus || (activePrevious.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : 'PENDING DOCTOR REVIEW')}
                  size="sm"
                />
              </div>
            </div>
          ) : (
            <div className="py-4 text-center text-xs text-slate-400">
              {t('prevScreeningNotAvailable') || 'Previous screening history is unavailable.'}
            </div>
          )}
        </div>

        {/* Current Screening Card */}
        <div className="p-4 rounded-2xl bg-teal-50/60 border border-teal-200 space-y-3">
          <div className="flex items-center justify-between border-b border-teal-200/70 pb-2">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-teal-800 block">
                {t('currentScreening') || 'Current Screening'}
              </span>
              <span className="text-xs font-bold text-slate-900">
                {currentScreening?.screeningDate || currentScreening?.date || 'Today'}
              </span>
            </div>
            <span className="text-[10px] font-mono text-teal-700">
              {currentScreening?.id || currentScreening?.screening_id || 'Active'}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">AI Classification:</span>
              <span className="font-extrabold text-slate-900">
                {currentScreening?.className || currentScreening?.overallSeverity || 'Moderate DR'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">AI Confidence:</span>
              <span className="font-bold text-teal-900 bg-white px-2 py-0.5 rounded border border-teal-300 font-mono text-[11px]">
                {formatConfidence(currentScreening?.confidence || 0.85)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Doctor Review:</span>
              <DoctorReviewStatusBadge
                status={currentScreening?.reviewStatus || (currentScreening?.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : currentScreening?.doctorStatus === 'recapture_requested' ? 'IMAGE RE-CAPTURE REQUESTED' : 'PENDING DOCTOR REVIEW')}
                size="sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Visual Image & Grad-CAM Side-by-Side Inspection Panel */}
      {activePrevious && (
        <div className="p-5 rounded-3xl bg-slate-900 text-white shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
            <div>
              <span className="text-xs font-extrabold uppercase tracking-wider text-teal-400 flex items-center gap-2">
                <Eye className="w-4 h-4" />
                <span>{t('visualComparisonLabel') || 'Visual comparison for clinical review.'}</span>
              </span>
              <p className="text-[11px] text-slate-400">
                Side-by-side fundus anatomy and Grad-CAM model attention across visits
              </p>
            </div>

            {/* Eye Selector OD / OS */}
            <div className="flex items-center gap-2 bg-slate-800 p-1 rounded-xl border border-slate-700 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setSelectedEye('OD')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                  selectedEye === 'OD' ? 'bg-teal-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-700'
                }`}
              >
                Right Eye (OD)
              </button>
              <button
                type="button"
                onClick={() => setSelectedEye('OS')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                  selectedEye === 'OS' ? 'bg-teal-600 text-white shadow-sm' : 'text-slate-300 hover:bg-slate-700'
                }`}
              >
                Left Eye (OS)
              </button>
            </div>
          </div>

          {/* Side-by-Side Images Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Previous Image View */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span className="font-bold text-slate-300">Previous Fundus ({activePrevious.screeningDate})</span>
                <span className="font-mono text-[10px]">{activePrevious.id}</span>
              </div>
              <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-800 aspect-square flex items-center justify-center">
                <img
                  src={prevImage}
                  alt="Previous Fundus"
                  className="w-full h-full object-contain transition-transform duration-200"
                  style={{ transform: `scale(${zoomLevel})` }}
                />
                {prevGradCam && (
                  <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] text-purple-300 border border-purple-500/40">
                    Grad-CAM Available
                  </div>
                )}
              </div>
            </div>

            {/* Current Image View */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span className="font-bold text-teal-300">Current Fundus ({currentScreening.screeningDate || 'Today'})</span>
                <span className="font-mono text-[10px]">{currentScreening.id || 'Active'}</span>
              </div>
              <div className="relative rounded-2xl overflow-hidden bg-black border border-teal-500/40 aspect-square flex items-center justify-center">
                <img
                  src={currImage}
                  alt="Current Fundus"
                  className="w-full h-full object-contain transition-transform duration-200"
                  style={{ transform: `scale(${zoomLevel})` }}
                />
                {currGradCam && (
                  <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] text-teal-300 border border-teal-500/40">
                    Grad-CAM Available
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center justify-between pt-1 text-xs text-slate-400 border-t border-slate-800/80">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.max(1, z - 0.25))}
                disabled={zoomLevel <= 1}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white disabled:opacity-40 transition"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="font-mono text-xs text-slate-300">{(zoomLevel * 100).toFixed(0)}%</span>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.25))}
                disabled={zoomLevel >= 2.5}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white disabled:opacity-40 transition"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setZoomLevel(1)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition ml-1"
                title="Reset Zoom"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            <span className="text-[10px] text-slate-400 italic">
              Synchronized visual inspection
            </span>
          </div>

          {/* Grad-CAM & Lesion Disclaimers */}
          <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 text-[11px] space-y-1 text-slate-300">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <p>
                {t('gradcamLongitudinalDisclaimer') ||
                  'Grad-CAM shows model attention and is not a direct measurement of disease progression.'}
              </p>
            </div>
            <div className="flex items-start gap-2 text-slate-400 text-[10px] pl-6">
              <span>• {t('lesionSpecificUnavailable') || 'Lesion-specific comparison unavailable.'} (No fake lesion progression is inferred).</span>
            </div>
          </div>
        </div>
      )}

      {/* Mandatory Medical Safety Disclaimer */}
      <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-slate-500 text-xs flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
        <p className="leading-relaxed text-[11px]">
          {t('longitudinalDisclaimer') ||
            'This comparison summarizes AI-assisted screening results across visits. It does not independently establish disease progression or replace clinical assessment.'}
        </p>
      </div>
    </div>
  );
};
