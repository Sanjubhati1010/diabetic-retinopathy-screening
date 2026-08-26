import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { SeverityBadge, UrgencyBadge, SafetyBadge, ScreeningStatusBadge, RiskBadge, ReferralBadge } from '../components/common/SeverityBadge';
import { GradCamViewer } from '../components/visualizer/GradCamViewer';
import { MetricCard } from '../components/common/MetricCard';
import {
  Stethoscope,
  CheckCircle2,
  AlertTriangle,
  Clock,
  FileCheck,
  Sparkles,
  Eye,
  User,
  ShieldCheck,
  Send,
  Edit3,
} from 'lucide-react';
import { SAMPLE_GRADCAM_HEATMAPS } from '../data/mockData';
import { evaluateRiskAndReferral, aggregateTwoEyeScreening } from '../services/api';

export const DoctorDashboardPage = () => {
  const { t } = useLanguage();
  const { screenings, doctorVerifyScreening, getPatientById } = useApp();

  const [selectedScreeningId, setSelectedScreeningId] = useState(
    screenings.find((s) => s.doctorStatus === 'pending')?.id || screenings[0].id
  );

  const selectedScreening = screenings.find((s) => s.id === selectedScreeningId) || screenings[0];
  const patient = getPatientById(selectedScreening.patientId);

  const [confirmedSeverity, setConfirmedSeverity] = useState(selectedScreening.overallSeverity);
  const [doctorRemarks, setDoctorRemarks] = useState(
    'Findings consistent with bilateral Moderate NPDR. Advised glycemic control (HbA1c < 7.0%) and slit-lamp examination at District Hospital within 4 weeks.'
  );
  const [agreeWithAi, setAgreeWithAi] = useState(true);
  const [successToast, setSuccessToast] = useState(false);
  const [selectedEye, setSelectedEye] = useState('OD');

  const pendingCount = screenings.filter((s) => s.doctorStatus === 'pending').length;
  const verifiedCount = screenings.filter((s) => s.doctorStatus === 'verified').length;

  const handleSignOff = (e) => {
    e.preventDefault();
    doctorVerifyScreening(selectedScreening.id, {
      confirmedSeverity,
      doctorRemarks,
      signatureApproved: true,
    });
    setSuccessToast(true);
    setTimeout(() => setSuccessToast(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Demo Data Disclaimer */}
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS</span>
      </div>

      {/* Top Specialist Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-teal-100 text-teal-700">
              <Stethoscope className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-extrabold text-slate-900">{t('docTitle')}</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">{t('docSubtitle')}</p>
        </div>

        <div className="flex items-center gap-2 text-xs font-bold text-teal-800 bg-teal-50 px-3.5 py-1.5 rounded-xl border border-teal-200">
          <span className="w-2 h-2 rounded-full bg-teal-600 animate-pulse" />
          <span>Tele-Ophthalmology Triage Queue Active</span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title={t('urgentQueue')}
          value={pendingCount}
          subtitle="Screened in rural camps awaiting review"
          icon={AlertTriangle}
          variant="amber"
        />
        <MetricCard
          title={t('verifiedToday')}
          value={verifiedCount}
          subtitle="Digitally signed tele-reports transmitted"
          icon={CheckCircle2}
          variant="emerald"
        />
        <MetricCard
          title="Backend Integration"
          value="Ready"
          subtitle="Awaiting trained PyTorch .pth model"
          icon={Sparkles}
          variant="teal"
        />
      </div>

      {/* Main Specialist Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Triage Priority Queue (4 Cols) */}
        <div className="lg:col-span-4 bg-white rounded-3xl p-5 border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              {t('urgentQueue')}
            </h3>
            <span className="text-xs font-extrabold text-slate-500">
              {screenings.length} Cases
            </span>
          </div>

          <div className="space-y-2.5 max-h-[620px] overflow-y-auto pr-1">
            {screenings.map((s) => {
              const isSelected = s.id === selectedScreening.id;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    setSelectedScreeningId(s.id);
                    setConfirmedSeverity(s.overallSeverity);
                  }}
                  className={`w-full text-left p-3.5 rounded-2xl border transition-all ${
                    isSelected
                      ? 'bg-teal-50/80 border-teal-500 shadow-sm ring-2 ring-teal-500/20'
                      : 'bg-slate-50/70 border-slate-200 hover:bg-slate-100/70'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-bold text-slate-900">{s.patientName}</p>
                    <UrgencyBadge urgency={s.referralUrgency} />
                  </div>
                  <div className="flex items-center justify-between mt-2 text-[11px] text-slate-500">
                    <span>{s.village}</span>
                    <SeverityBadge severity={s.overallSeverity} size="sm" />
                  </div>
                  <div className="flex items-center justify-between mt-1 pt-1.5 border-t border-slate-200/60 text-[10px] text-slate-400">
                    <span>{s.screeningDate.split(' ')[0]}</span>
                    <span
                      className={`font-semibold ${
                        s.doctorStatus === 'verified' ? 'text-emerald-600' : 'text-amber-600'
                      }`}
                    >
                      {s.doctorStatus === 'verified' ? '✓ Signed Off' : '• Awaiting Sign-Off'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Case Inspection, Grad-CAM & Doctor Sign-Off Form (8 Cols) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Patient Overview Strip */}
          <div className="p-5 rounded-3xl bg-white border border-slate-200 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center font-bold">
                <User className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-extrabold text-slate-900">{selectedScreening.patientName}</h3>
                  <span className="text-xs text-slate-400 font-mono">({selectedScreening.id})</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  {patient.age}y, {patient.gender} • Diabetes: {patient.diabetesDuration} yrs • HbA1c: {patient.lastHba1c}% • Visual Acuity (OD: {patient.visualAcuityOD}, OS: {patient.visualAcuityOS})
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <RiskBadge risk={selectedScreening.riskCategory || 'MODERATE'} size="sm" />
              <ReferralBadge priority={selectedScreening.referralPriority || 'EYE SPECIALIST REVIEW RECOMMENDED'} size="sm" />
              <SafetyBadge status={selectedScreening.safetyStatus || 'READY_FOR_AI'} size="sm" />
              <ScreeningStatusBadge status={selectedScreening.screeningStatus || 'RELIABLE AI SCREENING'} size="sm" />
              <SeverityBadge severity={selectedScreening.overallSeverity} />
            </div>
          </div>

          {/* Dual Eye / Grad-CAM Inspection Viewer */}
          <GradCamViewer
            originalImage={
              selectedEye === 'OD' ? selectedScreening.imageOD : selectedScreening.imageOS
            }
            heatmapImage={
              selectedEye === 'OD'
                ? selectedScreening.gradCamOD || selectedScreening.gradCamUrl
                : selectedScreening.gradCamOS || selectedScreening.gradCamUrl
            }
            heatmapUrl={
              selectedEye === 'OD'
                ? selectedScreening.heatmapOD || selectedScreening.gradCamOD || selectedScreening.gradCamUrl
                : selectedScreening.heatmapOS || selectedScreening.gradCamOS || selectedScreening.gradCamUrl
            }
            confidence={selectedScreening.confidence}
            severity={selectedScreening.overallSeverity}
            selectedEye={selectedEye}
            onEyeChange={setSelectedEye}
            showControls={true}
          />

          {/* Doctor Sign-Off & Diagnostic Validation Form */}
          <form
            onSubmit={handleSignOff}
            className="p-6 rounded-3xl bg-white border border-slate-200 shadow-card space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-teal-600" />
                <span>Specialist Diagnostic Verification & Digital Sign-Off</span>
              </h4>
              <span className="text-[11px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                Dr. A. Swaminathan, MS
              </span>
            </div>

            {/* Diagnostic Agreement & Stage Selection */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  {t('modifyDiagnosis')}
                </label>
                <select
                  value={confirmedSeverity}
                  onChange={(e) => {
                    setConfirmedSeverity(e.target.value);
                    setAgreeWithAi(e.target.value === selectedScreening.overallSeverity);
                  }}
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-teal-500 focus:border-teal-500 bg-white font-bold"
                >
                  <option value="dr0">DR 0 — No Retinopathy</option>
                  <option value="dr1">DR 1 — Mild NPDR</option>
                  <option value="dr2">DR 2 — Moderate NPDR</option>
                  <option value="dr3">DR 3 — Severe NPDR</option>
                  <option value="dr4">DR 4 — Proliferative DR</option>
                </select>
              </div>

              <div className="flex items-center pt-5">
                <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={agreeWithAi}
                    onChange={(e) => setAgreeWithAi(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-4 h-4"
                  />
                  <span className="text-xs font-bold text-slate-800">{t('agreeWithAi')}</span>
                </label>
              </div>
            </div>

            {/* Doctor Remarks Input */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Clinical Impression & Management Plan for Rural Screener
              </label>
              <textarea
                rows="3"
                value={doctorRemarks}
                onChange={(e) => setDoctorRemarks(e.target.value)}
                className="w-full text-xs p-3 rounded-xl border border-slate-300 focus:ring-teal-500 focus:border-teal-500"
                placeholder="Enter clinical instructions, medication advice, or hospital referral priority..."
              />
            </div>

            {/* Submit Button */}
            <div className="flex items-center justify-between pt-2">
              {successToast ? (
                <span className="text-xs font-bold text-emerald-700 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Clinical sign-off transmitted to Rampur PHC successfully!</span>
                </span>
              ) : (
                <span className="text-[11px] text-slate-400">
                  Electronic timestamp will be attached with your medical council registration number.
                </span>
              )}

              <button
                type="submit"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-glow-teal transition transform hover:-translate-y-0.5"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>{t('submitVerification')}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
