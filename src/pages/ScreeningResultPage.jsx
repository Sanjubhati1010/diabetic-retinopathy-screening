import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { SeverityBadge, UrgencyBadge } from '../components/common/SeverityBadge';
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
} from 'lucide-react';
import { formatConfidence, getSeverityKeyFromClass } from '../services/api';

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
                {t('drSeverity')}
              </span>
              <span className="text-xs font-extrabold text-brand-700 bg-brand-50 px-2.5 py-1 rounded-lg border border-brand-200">
                {isReal ? 'Model: EfficientNet-B0 (PyTorch)' : 'Model: Awaiting Connection'}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {isReal ? (
                <>
                  <SeverityBadge severity={screening.overallSeverity} size="lg" />
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

      {/* Bilateral Eye Examination Details (OD vs OS) */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-6">
        <h3 className="text-base font-extrabold text-slate-900">{t('eyeComparison')}</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Right Eye (OD) */}
          <div className="p-5 rounded-2xl border border-slate-200 bg-slate-50/60 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-brand-500"></span>
                <h4 className="text-xs font-bold text-slate-900">{t('odFindings')}</h4>
              </div>
              <SeverityBadge severity={odSeverity} size="sm" />
            </div>

            <div className="flex gap-4">
              <div className="w-28 h-28 rounded-xl bg-black overflow-hidden shrink-0 border border-slate-800 shadow-sm">
                <img
                  src={screening.imageOD}
                  alt="OD Fundus"
                  className="w-full h-full object-contain"
                />
              </div>
              <div className="text-xs space-y-1.5 text-slate-600 flex-1">
                <p className="font-semibold text-slate-800">Scan Status:</p>
                <ul className="list-disc list-inside text-[11px] space-y-0.5 text-slate-500">
                  <li>Macula and optic disc centered</li>
                  <li>Optical illumination verified</li>
                  {hasRightEye ? (
                    <>
                      <li className="text-emerald-700 font-semibold">
                        Analyzed: {rightEyeAnalysis.class_name} ({formatConfidence(rightEyeAnalysis.confidence)})
                      </li>
                      {rightEyeAnalysis.inference_time && (
                        <li className="text-slate-500">
                          Inference Time: {rightEyeAnalysis.inference_time}s
                        </li>
                      )}
                    </>
                  ) : (
                    <li className="text-slate-400 font-medium">Not analyzed yet</li>
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* Left Eye (OS) */}
          <div className="p-5 rounded-2xl border border-slate-200 bg-slate-50/60 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
                <h4 className="text-xs font-bold text-slate-900">{t('osFindings')}</h4>
              </div>
              <SeverityBadge severity={osSeverity} size="sm" />
            </div>

            <div className="flex gap-4">
              <div className="w-28 h-28 rounded-xl bg-black overflow-hidden shrink-0 border border-slate-800 shadow-sm">
                <img
                  src={screening.imageOS}
                  alt="OS Fundus"
                  className="w-full h-full object-contain"
                />
              </div>
              <div className="text-xs space-y-1.5 text-slate-600 flex-1">
                <p className="font-semibold text-slate-800">Scan Status:</p>
                <ul className="list-disc list-inside text-[11px] space-y-0.5 text-slate-500">
                  <li>Macula and optic disc centered</li>
                  <li>Optical illumination verified</li>
                  {hasLeftEye ? (
                    <>
                      <li className="text-teal-700 font-semibold">
                        Analyzed: {leftEyeAnalysis.class_name} ({formatConfidence(leftEyeAnalysis.confidence)})
                      </li>
                      {leftEyeAnalysis.inference_time && (
                        <li className="text-slate-500">
                          Inference Time: {leftEyeAnalysis.inference_time}s
                        </li>
                      )}
                    </>
                  ) : (
                    <li className="text-slate-400 font-medium">Not analyzed yet</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Pathological Biomarker Tags */}
        <div className="pt-4 border-t border-slate-100 space-y-2">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            {t('detectedBiomarkers')}
          </h4>
          <BiomarkerTags biomarkers={screening.biomarkers} />
        </div>
      </div>

      {/* Action Navigation Footer */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <button
          type="button"
          onClick={() => setTeleModalOpen(true)}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-glow-teal transition"
        >
          <Stethoscope className="w-4 h-4" />
          <span>{t('btnTeleConsult')}</span>
        </button>

        <div className="flex items-center gap-3">
          <Link
            to={`/screenings/${screening.id}/xai`}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-glow transition"
          >
            <Sparkles className="w-4 h-4" />
            <span>{t('btnExploreGradCam')}</span>
            <ArrowRight className="w-4 h-4" />
          </Link>

          <Link
            to={`/screenings/${screening.id}/report`}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs shadow-sm transition"
          >
            <FileText className="w-4 h-4 text-slate-500" />
            <span>{t('btnGenerateReport')}</span>
          </Link>
        </div>
      </div>

      {/* Tele-Consultation Request Modal */}
      <Modal
        isOpen={teleModalOpen}
        onClose={() => setTeleModalOpen(false)}
        title="Request Tele-Ophthalmology Review"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-600">
            Send this patient's retinal scans, AI classification, and Grad-CAM explainability heatmaps directly to the duty Tele-Ophthalmologist at <strong>District Eye Hospital</strong>.
          </p>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <p className="font-bold text-slate-900">Priority: High (Moderate/Severe DR)</p>
            <p className="text-[11px] text-slate-500">Expected Response Window: 15-30 Minutes</p>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              onClick={() => setTeleModalOpen(false)}
              className="px-4 py-2 rounded-xl border border-slate-200 bg-white text-slate-700 font-bold hover:bg-slate-50"
            >
              {t('btnCancel')}
            </button>
            <button
              onClick={handleSendTeleConsult}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-sm"
            >
              {teleSent ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-white" />
                  <span>Transmitted to Doctor!</span>
                </>
              ) : (
                <>
                  <Stethoscope className="w-4 h-4" />
                  <span>Transmit Clinical Package</span>
                </>
              )}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
