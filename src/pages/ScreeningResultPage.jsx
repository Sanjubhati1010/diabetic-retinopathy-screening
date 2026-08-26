import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { SeverityBadge, UrgencyBadge, SafetyBadge, ScreeningStatusBadge } from '../components/common/SeverityBadge';
import { BiomarkerTags } from '../components/visualizer/BiomarkerTags';
import { Modal } from '../components/common/Modal';
import {
  FileCheck,
  Eye,
  Sparkles,
  FileText,
  Stethoscope,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Calendar,
  User,
  Share2,
  Clock,
  BarChart2,
  Info,
  AlertOctagon,
  ArrowUpRight,
  RotateCcw,
} from 'lucide-react';
import { formatConfidence, getSeverityKeyFromClass, CONFIDENCE_THRESHOLD, evaluateConfidence } from '../services/api';

export const ScreeningResultPage = () => {
  const { id } = useParams();
  const { t } = useLanguage();
  const { getScreeningById, screenings, activeScreening } = useApp();
  const navigate = useNavigate();

  const latestRealScreening = screenings.find(
    (s) => s.isRealPrediction || s.gradCamUrl || s.confidence !== null
  );

  let screening = id
    ? getScreeningById(id)
    : latestRealScreening || screenings[0];

  if (!screening.isRealPrediction && !screening.gradCamUrl && latestRealScreening) {
    screening = latestRealScreening;
  }

  const [teleModalOpen, setTeleModalOpen] = useState(false);
  const [teleSent, setTeleSent] = useState(false);

  const handleSendTeleConsult = () => {
    setTeleSent(true);
    setTimeout(() => {
      setTeleModalOpen(false);
      setTeleSent(false);
    }, 1500);
  };

  const isReal = screening.isRealPrediction || screening.confidence !== null;
  const probabilities = screening.probabilities || null;

  const rightEyeAnalysis =
    screening.rightEyeAnalysis ||
    screening.aiResultOD ||
    (screening.selectedEyeForAnalysis === 'OD' ? screening.aiResult : null);

  const leftEyeAnalysis =
    screening.leftEyeAnalysis ||
    screening.aiResultOS ||
    (screening.selectedEyeForAnalysis === 'OS' ? screening.aiResult : null);

  const hasRightEye = Boolean(rightEyeAnalysis);
  const hasLeftEye = Boolean(leftEyeAnalysis);

  const odSeverity =
    screening.drSeverityOD && screening.drSeverityOD !== 'drUncertain'
      ? screening.drSeverityOD
      : hasRightEye
      ? getSeverityKeyFromClass(rightEyeAnalysis.predicted_class)
      : 'drUncertain';

  const osSeverity =
    screening.drSeverityOS && screening.drSeverityOS !== 'drUncertain'
      ? screening.drSeverityOS
      : hasLeftEye
      ? getSeverityKeyFromClass(leftEyeAnalysis.predicted_class)
      : 'drUncertain';

  // Helper to extract Phase 2 evaluation for an eye
  const getEyePhase2Metrics = (analysis, fallbackSeverity, errorState) => {
    if (!analysis) {
      if (errorState) {
        return {
          aiPrediction: 'Unable to Assess',
          confidence: null,
          safetyStatus: 'IMAGE_INVALID',
          screeningStatus: 'UNABLE TO ASSESS',
          nextStep: t('nextStepUnable') || 'AI cannot reliably assess this image. Please capture another image or request specialist review.',
          isLowConfidence: false,
          hasAnalysis: false,
        };
      }
      return {
        aiPrediction: 'Not Screened',
        confidence: null,
        safetyStatus: 'IMAGE_INVALID',
        screeningStatus: 'UNABLE TO ASSESS',
        nextStep: 'Upload retinal scan to begin screening.',
        isLowConfidence: false,
        hasAnalysis: false,
      };
    }

    const conf = analysis.confidence ?? null;
    const isLow = analysis.is_low_confidence !== undefined
      ? analysis.is_low_confidence
      : (conf !== null && (conf > 1.0 ? conf / 100.0 : conf) < CONFIDENCE_THRESHOLD);

    const safetyStatus = analysis.safety_status || 'READY_FOR_AI';
    const screeningStatus = analysis.screening_status || (isLow ? 'LOW CONFIDENCE' : 'RELIABLE AI SCREENING');
    const nextStep = analysis.next_step || (
      isLow
        ? (t('nextStepLowConfidence') || 'AI confidence is low. Please capture a clearer image or request specialist review.')
        : (t('nextStepReliable') || 'Continue to explanation / specialist review.')
    );

    return {
      aiPrediction: analysis.class_name || 'DR Prediction',
      confidence: conf,
      safetyStatus,
      screeningStatus,
      nextStep,
      isLowConfidence: isLow,
      hasAnalysis: true,
      inferenceTime: analysis.inference_time,
    };
  };

  const odMetrics = getEyePhase2Metrics(rightEyeAnalysis, odSeverity, screening.odAnalysisError);
  const osMetrics = getEyePhase2Metrics(leftEyeAnalysis, osSeverity, screening.osAnalysisError);

  // Triage recommendations based on ICDR Severity
  const getTriageProtocol = (severity) => {
    switch (severity) {
      case 'dr0':
        return {
          title: 'Routine Annual Screening',
          action: 'Annual Community Rescreening',
          desc: 'No diabetic retinopathy lesions detected. Counsel patient on glycemic control, blood pressure maintenance, and annual fundus check.',
          badge: 'Low Risk',
        };
      case 'dr1':
        return {
          title: 'Mild Non-Proliferative DR',
          action: 'Follow-up in 6 to 12 Months',
          desc: 'Microaneurysms detected. Rescreen within 6-12 months. Advise strict HbA1c and lipid control at primary health center.',
          badge: 'Routine Review',
        };
      case 'dr2':
        return {
          title: 'Moderate Non-Proliferative DR',
          action: 'Ophthalmologist Referral within 1 Month',
          desc: 'Hemorrhages and exudates present. Schedule comprehensive dilated slit-lamp and OCT exam at District Eye Hospital.',
          badge: 'Semi-Urgent',
        };
      case 'dr3':
        return {
          title: 'Severe Non-Proliferative DR',
          action: 'Prompt Specialist Review within 1-2 Weeks',
          desc: 'High risk of conversion to proliferative retinopathy. Prioritize for urgent tertiary tele-ophthalmology assessment.',
          badge: 'High Priority',
        };
      case 'dr4':
        return {
          title: 'Proliferative Diabetic Retinopathy (PDR)',
          action: 'Immediate Vitreoretinal Consult (24-48 Hours)',
          desc: 'Active neovascularization detected. Immediate laser photocoagulation or anti-VEGF therapy review required.',
          badge: 'Critical Alert',
        };
      default:
        return {
          title: 'Referral Triage Protocol',
          action: 'Awaiting Tele-Ophthalmology Review',
          desc: 'Awaiting automated model inference and Tele-Ophthalmology clinical review.',
          badge: 'Pending',
        };
    }
  };

  const triage = getTriageProtocol(screening.overallSeverity);

  const renderEyeResultCard = (eyeName, tagLabel, imageSrc, severityKey, metrics, badgeColor) => {
    const isOD = eyeName === 'OD';
    const isLow = metrics.isLowConfidence;
    const isUnable = metrics.screeningStatus === 'UNABLE TO ASSESS';

    return (
      <div
        className={`p-6 rounded-3xl border transition shadow-sm space-y-5 ${
          isUnable
            ? 'border-rose-200 bg-rose-50/20'
            : isLow
            ? 'border-amber-200 bg-amber-50/20'
            : 'border-slate-200 bg-white'
        }`}
      >
        {/* Header: Eye Name + Screening Status Badge */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${badgeColor}`}></span>
            <h4 className="text-sm font-bold text-slate-900">{tagLabel}</h4>
          </div>
          <ScreeningStatusBadge status={metrics.screeningStatus} size="sm" />
        </div>

        {/* Scan Preview + Structured Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-start">
          {/* Fundus Preview */}
          <div className="sm:col-span-4 aspect-square rounded-2xl bg-black overflow-hidden border border-slate-800 shadow-inner flex items-center justify-center">
            {imageSrc ? (
              <img src={imageSrc} alt={`${tagLabel} Fundus`} className="w-full h-full object-contain" />
            ) : (
              <span className="text-xs text-slate-500">No Image</span>
            )}
          </div>

          {/* Structured Attributes */}
          <div className="sm:col-span-8 space-y-3">
            {/* 1. AI PREDICTION */}
            <div className="flex items-center justify-between text-xs pb-1.5 border-b border-slate-100">
              <span className="font-bold text-slate-500 uppercase tracking-wider">{t('aiPredictionLabel')}:</span>
              <div className="flex items-center gap-1.5">
                {metrics.hasAnalysis ? (
                  <SeverityBadge severity={severityKey} size="sm" />
                ) : (
                  <span className="font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 text-xs">
                    {metrics.aiPrediction}
                  </span>
                )}
              </div>
            </div>

            {/* 2. MODEL CONFIDENCE */}
            <div className="space-y-1 text-xs pb-1.5 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-500 uppercase tracking-wider">{t('modelConfidenceLabel')}:</span>
                <span className={`font-mono font-bold ${isLow ? 'text-amber-700' : 'text-emerald-700'}`}>
                  {metrics.confidence !== null ? formatConfidence(metrics.confidence) : 'N/A'}
                  {isLow && ' (Low)'}
                </span>
              </div>
              {metrics.confidence !== null && (
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
                  <div
                    className={`h-full rounded-full transition-all ${
                      isLow ? 'bg-amber-500' : 'bg-gradient-to-r from-emerald-500 to-teal-600'
                    }`}
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(5, (metrics.confidence <= 1 ? metrics.confidence * 100 : metrics.confidence))
                      )}%`,
                    }}
                  />
                </div>
              )}
            </div>

            {/* 3. SAFETY STATUS */}
            <div className="flex items-center justify-between text-xs pb-1.5 border-b border-slate-100">
              <span className="font-bold text-slate-500 uppercase tracking-wider">{t('safetyStatusLabel')}:</span>
              <SafetyBadge status={metrics.safetyStatus} size="sm" />
            </div>

            {/* 4. SCREENING STATUS */}
            <div className="flex items-center justify-between text-xs pb-1.5 border-b border-slate-100">
              <span className="font-bold text-slate-500 uppercase tracking-wider">{t('screeningStatusLabel')}:</span>
              <span className={`font-bold text-xs ${
                isUnable ? 'text-rose-700' : isLow ? 'text-amber-800' : 'text-emerald-700'
              }`}>
                {metrics.screeningStatus}
              </span>
            </div>
          </div>
        </div>

        {/* 5. NEXT STEP Callout Box */}
        <div
          className={`p-3.5 rounded-2xl border text-xs space-y-1 ${
            isUnable
              ? 'bg-rose-50/80 border-rose-200 text-rose-900'
              : isLow
              ? 'bg-amber-50/80 border-amber-200 text-amber-900'
              : 'bg-emerald-50/80 border-emerald-200 text-emerald-950'
          }`}
        >
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px]">
            {isUnable ? (
              <AlertOctagon className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            ) : isLow ? (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            )}
            <span>{t('nextStepLabel')}</span>
          </div>
          <p className="text-xs leading-relaxed font-medium pl-5">{metrics.nextStep}</p>
        </div>

        {/* Medical Certainty Disclaimer */}
        <p className="text-[10px] text-slate-500 italic leading-snug">
          {t('confidenceDisclaimer')}
        </p>
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Demo Data Notice */}
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>
          DEMO DATA — NOT REAL MEDICAL RESULTS • AI-assisted screening only. This result is not a medical diagnosis and must be reviewed by a qualified healthcare professional.
        </span>
      </div>

      {/* Top Banner with Patient & Camp details */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600 font-bold text-lg">
              <FileCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-extrabold text-slate-900">{t('resultTitle')}</h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
                  {screening.id}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Patient: <strong className="text-slate-800">{screening.patientName}</strong> • {screening.village}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <UrgencyBadge urgency={screening.referralUrgency} />
          </div>
        </div>

        {/* Primary Classification Showcase */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pt-6 items-start">
          {/* Main Grade & Probabilities Box (7 cols) */}
          <div className="md:col-span-7 p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                {t('overallAssessment')}
              </span>
              <span className="text-xs font-extrabold text-brand-700 bg-brand-50 px-2.5 py-1 rounded-lg border border-brand-200">
                {isReal ? 'Model: EfficientNet-B0 (PyTorch)' : 'Model: Standby Mode'}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {isReal ? (
                <>
                  <SeverityBadge severity={screening.overallSeverity} size="lg" />
                  <ScreeningStatusBadge status={screening.screeningStatus || 'RELIABLE AI SCREENING'} size="md" />
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Confidence: {formatConfidence(screening.confidence)}</span>
                  </span>
                  {screening.inferenceTime && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{Number(screening.inferenceTime).toFixed(3)}s</span>
                    </span>
                  )}
                </>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-sm font-bold bg-slate-100 text-slate-700 border border-slate-300">
                  <Sparkles className="w-4 h-4 text-slate-400" />
                  <span>AI model not connected yet</span>
                </span>
              )}
            </div>

            {/* 5-Class Probability Distribution */}
            {probabilities && (
              <div className="pt-2 border-t border-slate-200/80 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <span className="flex items-center gap-1">
                    <BarChart2 className="w-3.5 h-3.5 text-brand-600" />
                    <span>5-Class Probability Distribution</span>
                  </span>
                </div>

                <div className="space-y-1.5">
                  {Object.entries(probabilities).map(([className, prob]) => {
                    const pct = (prob * 100).toFixed(2);
                    const isPredicted =
                      (screening.className &&
                        screening.className.toLowerCase() === className.toLowerCase()) ||
                      (className === 'No DR' && screening.overallSeverity === 'dr0') ||
                      (className === 'Mild' && screening.overallSeverity === 'dr1') ||
                      (className === 'Moderate' && screening.overallSeverity === 'dr2') ||
                      (className === 'Severe' && screening.overallSeverity === 'dr3') ||
                      (className === 'Proliferative DR' && screening.overallSeverity === 'dr4');

                    return (
                      <div key={className} className="space-y-0.5">
                        <div className="flex items-center justify-between text-xs">
                          <span
                            className={`${
                              isPredicted ? 'font-bold text-brand-700' : 'text-slate-600'
                            }`}
                          >
                            {className} {isPredicted && '✓'}
                          </span>
                          <span
                            className={`font-mono text-[11px] ${
                              isPredicted ? 'font-bold text-brand-700' : 'text-slate-500'
                            }`}
                          >
                            {pct}%
                          </span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-200 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              isPredicted ? 'bg-brand-600' : 'bg-slate-400'
                            }`}
                            style={{ width: `${Math.max(Number(pct), 2)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <p className="text-xs text-slate-600 leading-relaxed pt-1">
              {screening.explanation ||
                (isReal
                  ? "Highlighted regions indicate image areas that contributed to the model's prediction."
                  : 'Retinal images have been captured and verified. Automated DR classification and severity scoring will populate here once the PyTorch model (.pth) is connected through the FastAPI backend.')}
            </p>
          </div>

          {/* Model Trust & Referral Box (5 cols) */}
          <div className="md:col-span-5 p-6 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-brand-600" />
              <span>{triage.title}</span>
            </h4>

            <div className="p-3.5 rounded-xl bg-white border border-slate-200 space-y-1.5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-bold text-slate-900">{triage.action}</p>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200">
                  {triage.badge}
                </span>
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">{triage.desc}</p>
            </div>

            {/* Disclaimer */}
            <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200/80 text-[11px] text-amber-900 leading-relaxed">
              <p className="font-semibold text-amber-950 flex items-center gap-1 mb-0.5">
                <Info className="w-3 h-3 text-amber-700" />
                <span>Clinical Disclaimer:</span>
              </p>
              {screening.disclaimer ||
                'AI-assisted screening only. This result is not a medical diagnosis and must be reviewed by a qualified healthcare professional.'}
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
              <span>Screener: {screening.screenerName}</span>
              <span>Dilation: {screening.dilation}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Phase 2 Independent Two-Eye Evaluation Cards (OD & OS) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-extrabold text-slate-900">{t('eyeComparison')}</h3>
          <span className="text-xs text-slate-500 font-medium">Independent AI Safety Gate & Confidence Evaluation</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {renderEyeResultCard(
            'OD',
            t('rightEyeOD') || 'Right Eye (OD - Oculus Dexter)',
            screening.imageOD,
            odSeverity,
            odMetrics,
            'bg-brand-500'
          )}
          {renderEyeResultCard(
            'OS',
            t('leftEyeOS') || 'Left Eye (OS - Oculus Sinister)',
            screening.imageOS,
            osSeverity,
            osMetrics,
            'bg-teal-500'
          )}
        </div>
      </div>

      {/* Biomarker Tags */}
      {screening.biomarkers && screening.biomarkers.length > 0 && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-3">
          <h3 className="text-sm font-bold text-slate-900">Detected Pathological Biomarkers</h3>
          <BiomarkerTags biomarkers={screening.biomarkers} />
        </div>
      )}

      {/* Action Footer */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-6 rounded-3xl bg-white border border-slate-200 shadow-card">
        <Link
          to="/screenings/new"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-xs font-bold text-slate-700 transition"
        >
          <RotateCcw className="w-4 h-4" />
          <span>New Screening Intake</span>
        </Link>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to={`/screenings/${screening.id}/gradcam`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 text-xs font-bold transition"
          >
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span>{t('btnExploreGradCam')}</span>
          </Link>

          <Link
            to={`/screenings/${screening.id}/report`}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white text-xs font-bold transition"
          >
            <FileText className="w-4 h-4" />
            <span>{t('btnGenerateReport')}</span>
          </Link>

          <button
            type="button"
            onClick={() => setTeleModalOpen(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-glow transition transform hover:-translate-y-0.5"
          >
            <Stethoscope className="w-4 h-4" />
            <span>{t('btnTeleConsult')}</span>
          </button>
        </div>
      </div>

      {/* Tele-Consult Modal */}
      <Modal
        isOpen={teleModalOpen}
        onClose={() => setTeleModalOpen(false)}
        title="Tele-Ophthalmologist Consultation Request"
      >
        <div className="space-y-4 text-xs text-slate-600">
          <p>
            Route screening packet (Bilateral Fundus, Grad-CAM Maps, Confidence Score, and AI Safety Gate decision) to District Hospital Tele-Ophthalmology Queue.
          </p>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <p><strong>Patient:</strong> {screening.patientName}</p>
            <p><strong>Overall Severity:</strong> {screening.overallSeverity.toUpperCase()}</p>
            <p><strong>Priority:</strong> {screening.referralUrgency.toUpperCase()}</p>
          </div>
          <button
            type="button"
            onClick={handleSendTeleConsult}
            disabled={teleSent}
            className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold transition flex items-center justify-center gap-2"
          >
            {teleSent ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-white" />
                <span>Request Dispatched to Specialist!</span>
              </>
            ) : (
              <span>Submit for Tele-Consultation</span>
            )}
          </button>
        </div>
      </Modal>
    </div>
  );
};
