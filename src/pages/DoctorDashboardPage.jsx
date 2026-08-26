import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  SeverityBadge,
  UrgencyBadge,
  SafetyBadge,
  ScreeningStatusBadge,
  RiskBadge,
  ReferralBadge,
  DoctorReviewStatusBadge,
} from '../components/common/SeverityBadge';
import { GradCamViewer } from '../components/visualizer/GradCamViewer';
import { MetricCard } from '../components/common/MetricCard';
import {
  Stethoscope,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Eye,
  User,
  ShieldCheck,
  Edit3,
  RotateCcw,
  CheckCircle,
  FileText,
  AlertCircle,
  History,
  X,
  Info,
} from 'lucide-react';
import { submitDoctorReview, getScreeningReviewHistory } from '../services/api';

const DR_OPTIONS = [
  { value: 0, label: 'DR 0 — No Retinopathy', name: 'No DR' },
  { value: 1, label: 'DR 1 — Mild NPDR', name: 'Mild' },
  { value: 2, label: 'DR 2 — Moderate NPDR', name: 'Moderate' },
  { value: 3, label: 'DR 3 — Severe NPDR', name: 'Severe' },
  { value: 4, label: 'DR 4 — Proliferative DR', name: 'Proliferative DR' },
];

export const DoctorDashboardPage = () => {
  const { t } = useLanguage();
  const { screenings, getPatientById } = useApp();

  const [selectedScreeningId, setSelectedScreeningId] = useState(
    screenings.find((s) => s.doctorStatus === 'pending')?.id || screenings[0]?.id || 'SCR-2026-001'
  );

  const selectedScreening = screenings.find((s) => s.id === selectedScreeningId) || screenings[0] || {};
  const patient = getPatientById(selectedScreening.patientId) || {
    name: selectedScreening.patientName || 'Patient',
    age: 52,
    gender: 'Female',
    diabetesDuration: 8,
    lastHba1c: 8.4,
    visualAcuityOD: '6/12',
    visualAcuityOS: '6/9',
  };

  const [selectedEye, setSelectedEye] = useState('OD');
  const [activeModal, setActiveModal] = useState(null); // 'ACCEPT' | 'MODIFY' | 'RECAPTURE' | null
  const [overrideClass, setOverrideClass] = useState(1);
  const [overrideComment, setOverrideComment] = useState('');
  const [commentError, setCommentError] = useState('');
  const [recaptureComment, setRecaptureComment] = useState(
    'Image quality is insufficient / blurry in macula. Re-capture required.'
  );
  const [auditHistory, setAuditHistory] = useState([]);
  const [reviewState, setReviewState] = useState(null);
  const [loadingAction, setLoadingAction] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Load audit history and local review record on screening selection
  useEffect(() => {
    if (!selectedScreening.id) return;

    // Check cached review
    const local = localStorage.getItem(`madocs_review_${selectedScreening.id}`);
    if (local) {
      try {
        setReviewState(JSON.parse(local));
      } catch (e) {
        setReviewState(null);
      }
    } else {
      setReviewState(null);
    }

    getScreeningReviewHistory(selectedScreening.id).then((data) => {
      if (data && data.events) {
        setAuditHistory(data.events);
      }
    });
  }, [selectedScreening.id]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // 1. Handle Accept AI Result
  const handleAcceptAi = async () => {
    setLoadingAction(true);
    try {
      const originalAi = selectedScreening.className || t(selectedScreening.overallSeverity) || 'Moderate';
      const result = await submitDoctorReview(
        selectedScreening.id,
        {
          action: 'ACCEPT',
          originalAiResult: originalAi,
          originalConfidence: selectedScreening.confidence || 0.85,
          reviewerId: 'DOC-SWAMINATHAN',
          reviewerName: 'Dr. A. Swaminathan, MS',
          reviewComment: 'Verified and accepted AI-assisted screening findings.',
        },
        'doctor'
      );
      setReviewState(result);
      const history = await getScreeningReviewHistory(selectedScreening.id);
      setAuditHistory(history.events || []);
      setActiveModal(null);
      showToast(t('reviewActionSuccess') || 'AI screening result accepted successfully.');
    } catch (err) {
      alert(err.message || 'Failed to accept review.');
    } finally {
      setLoadingAction(false);
    }
  };

  // 2. Handle Modify / Override Result
  const handleModifyResult = async () => {
    if (!overrideComment || !overrideComment.trim()) {
      setCommentError(t('errReviewCommentRequired') || 'A clinical review reason is required for an override.');
      return;
    }

    setCommentError('');
    setLoadingAction(true);
    try {
      const selectedOption = DR_OPTIONS.find((o) => o.value === Number(overrideClass)) || DR_OPTIONS[1];
      const originalAi = selectedScreening.className || t(selectedScreening.overallSeverity) || 'Moderate';

      const result = await submitDoctorReview(
        selectedScreening.id,
        {
          action: 'MODIFY',
          reviewedClass: selectedOption.value,
          reviewedClassName: selectedOption.name,
          reviewComment: overrideComment.trim(),
          originalAiResult: originalAi,
          originalConfidence: selectedScreening.confidence || 0.85,
          reviewerId: 'DOC-SWAMINATHAN',
          reviewerName: 'Dr. A. Swaminathan, MS',
        },
        'doctor'
      );
      setReviewState(result);
      const history = await getScreeningReviewHistory(selectedScreening.id);
      setAuditHistory(history.events || []);
      setActiveModal(null);
      setOverrideComment('');
      showToast(t('reviewActionSuccess') || 'Doctor override recorded successfully.');
    } catch (err) {
      alert(err.message || 'Failed to submit override.');
    } finally {
      setLoadingAction(false);
    }
  };

  // 3. Handle Request Image Re-capture
  const handleRequestRecapture = async () => {
    setLoadingAction(true);
    try {
      const originalAi = selectedScreening.className || t(selectedScreening.overallSeverity) || 'Moderate';
      const result = await submitDoctorReview(
        selectedScreening.id,
        {
          action: 'RECAPTURE',
          reviewComment: recaptureComment.trim(),
          originalAiResult: originalAi,
          originalConfidence: selectedScreening.confidence || 0.85,
          reviewerId: 'DOC-SWAMINATHAN',
          reviewerName: 'Dr. A. Swaminathan, MS',
        },
        'doctor'
      );
      setReviewState(result);
      const history = await getScreeningReviewHistory(selectedScreening.id);
      setAuditHistory(history.events || []);
      setActiveModal(null);
      showToast('Image re-capture request recorded successfully.');
    } catch (err) {
      alert(err.message || 'Failed to request re-capture.');
    } finally {
      setLoadingAction(false);
    }
  };

  const currentStatus = reviewState?.review_status || (selectedScreening.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : 'PENDING DOCTOR REVIEW');
  const originalAiDisplay = reviewState?.original_ai_result || selectedScreening.className || t(selectedScreening.overallSeverity) || 'Moderate';
  const doctorReviewedDisplay = reviewState?.doctor_reviewed_result || (selectedScreening.doctorStatus === 'verified' ? originalAiDisplay : 'Pending Specialist Review');

  const pendingCount = screenings.filter((s) => s.doctorStatus === 'pending').length;
  const verifiedCount = screenings.filter((s) => s.doctorStatus === 'verified' || reviewState).length;

  return (
    <div className="space-y-6 font-sans">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-6 z-50 p-4 rounded-2xl bg-slate-900 text-white shadow-2xl border border-emerald-500/50 flex items-center gap-3 animate-fade-in text-xs font-bold">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Human-in-the-Loop Clinical Oversight Banner */}
      <div className="p-4 rounded-3xl bg-gradient-to-r from-teal-900 via-slate-900 to-teal-950 text-white border border-teal-700/50 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-teal-500/20 text-teal-300 border border-teal-400/30">
              <Stethoscope className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-extrabold tracking-tight">{t('doctorReviewTitle') || 'Doctor Review & Clinical Verification'}</h1>
          </div>
          <p className="text-xs text-teal-200/90 font-medium">
            {t('hitlDisclaimer') || 'AI provides screening assistance. Final clinical interpretation should be performed by a qualified healthcare professional.'}
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-extrabold text-teal-300 bg-teal-950/80 px-4 py-2 rounded-2xl border border-teal-700/60 shrink-0">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>{t('hitlSeparateNotice') || 'Doctor review is separate from the AI prediction.'}</span>
        </div>
      </div>

      {/* Triage Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title={t('urgentQueue')}
          value={pendingCount}
          subtitle="Screened in rural camps awaiting specialist review"
          icon={AlertTriangle}
          variant="amber"
        />
        <MetricCard
          title={t('verifiedToday')}
          value={verifiedCount}
          subtitle="Human-in-the-Loop verified cases signed off"
          icon={CheckCircle2}
          variant="emerald"
        />
        <MetricCard
          title="Clinical Safety Layer"
          value="Active"
          subtitle="Dual-record preservation & audit logging"
          icon={Sparkles}
          variant="teal"
        />
      </div>

      {/* Main Specialist Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Triage Queue (4 Cols) */}
        <div className="lg:col-span-4 bg-white rounded-3xl p-5 border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              {t('urgentQueue')}
            </h3>
            <span className="text-xs font-extrabold text-slate-500">
              {screenings.length} Cases
            </span>
          </div>

          <div className="space-y-2.5 max-h-[660px] overflow-y-auto pr-1">
            {screenings.map((s) => {
              const isSelected = s.id === selectedScreening.id;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setSelectedScreeningId(s.id)}
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
                  <div className="flex items-center justify-between mt-1.5 pt-1.5 border-t border-slate-200/60 text-[10px]">
                    <span className="text-slate-400 font-mono">{s.id}</span>
                    <DoctorReviewStatusBadge
                      status={s.id === selectedScreening.id && reviewState ? reviewState.review_status : s.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : 'PENDING DOCTOR REVIEW'}
                      size="sm"
                    />
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Case Inspection, Grad-CAM & Action Panel (8 Cols) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Patient Overview Strip */}
          <div className="p-5 rounded-3xl bg-white border border-slate-200 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-teal-100 text-teal-800 flex items-center justify-center font-bold">
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
              <DoctorReviewStatusBadge status={currentStatus} size="sm" />
              <RiskBadge risk={selectedScreening.riskCategory || 'MODERATE'} size="sm" />
              <ReferralBadge priority={selectedScreening.referralPriority || 'EYE SPECIALIST REVIEW RECOMMENDED'} size="sm" />
              <SafetyBadge status={selectedScreening.safetyStatus || 'READY_FOR_AI'} size="sm" />
            </div>
          </div>

          {/* Side-by-Side Result Comparison Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-3xl bg-slate-50 border border-slate-200">
            {/* Box 1: Original AI Result (Immutable) */}
            <div className="p-3.5 rounded-2xl bg-white border border-slate-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                {t('originalAiResultLabel') || 'Original AI Result (Preserved)'}
              </span>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-extrabold text-slate-900">{originalAiDisplay}</h4>
                <span className="text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  {selectedScreening.confidence ? `${(selectedScreening.confidence * 100).toFixed(1)}% Conf.` : '85.0% Conf.'}
                </span>
              </div>
              <p className="text-[10px] text-slate-500">Immutable screening inference baseline</p>
            </div>

            {/* Box 2: Doctor Reviewed Result */}
            <div className="p-3.5 rounded-2xl bg-teal-50/70 border border-teal-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-teal-700">
                {t('doctorReviewedResultLabel') || 'Doctor Reviewed Result'}
              </span>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-extrabold text-teal-950">{doctorReviewedDisplay}</h4>
                <span className="text-xs font-bold text-emerald-800 bg-emerald-100/70 px-2 py-0.5 rounded border border-emerald-300">
                  Dr. A. Swaminathan, MS
                </span>
              </div>
              <p className="text-[10px] text-teal-700 font-medium">
                {reviewState?.review_comment || 'Verified by specialist'}
              </p>
            </div>
          </div>

          {/* Dual Eye Grad-CAM Tri-View Inspector */}
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

          {/* 3 Core Human-in-the-Loop Action Buttons */}
          <div className="p-5 rounded-3xl bg-white border border-slate-200 shadow-card space-y-3">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-2">
              <Edit3 className="w-4 h-4 text-teal-600" />
              <span>Specialist Review Actions</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              {/* Action 1: Accept AI Screening */}
              <button
                type="button"
                onClick={() => setActiveModal('ACCEPT')}
                className="inline-flex items-center justify-center gap-2 p-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md hover:shadow-lg transition transform hover:-translate-y-0.5"
              >
                <CheckCircle className="w-4 h-4" />
                <span>{t('btnAcceptAiScreening') || 'Accept AI Screening'}</span>
              </button>

              {/* Action 2: Modify / Override Result */}
              <button
                type="button"
                onClick={() => {
                  setCommentError('');
                  setActiveModal('MODIFY');
                }}
                className="inline-flex items-center justify-center gap-2 p-3 rounded-2xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-md hover:shadow-lg transition transform hover:-translate-y-0.5"
              >
                <Edit3 className="w-4 h-4" />
                <span>{t('btnModifyOverride') || 'Modify / Override Result'}</span>
              </button>

              {/* Action 3: Request Image Re-capture */}
              <button
                type="button"
                onClick={() => setActiveModal('RECAPTURE')}
                className="inline-flex items-center justify-center gap-2 p-3 rounded-2xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-md hover:shadow-lg transition transform hover:-translate-y-0.5"
              >
                <RotateCcw className="w-4 h-4" />
                <span>{t('btnRequestRecapture') || 'Request Re-capture'}</span>
              </button>
            </div>
          </div>

          {/* Chronological Review Audit Trail Timeline */}
          <div className="p-5 rounded-3xl bg-white border border-slate-200 shadow-card space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <History className="w-4 h-4 text-slate-600" />
                <span>{t('reviewAuditTrailTitle') || 'Chronological Review Audit Trail'}</span>
              </h4>
              <span className="text-[10px] text-slate-400 font-mono">Screening ID: {selectedScreening.id}</span>
            </div>

            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {auditHistory.length === 0 ? (
                <div className="text-[11px] text-slate-400 py-2 text-center">
                  No review audit entries recorded yet.
                </div>
              ) : (
                auditHistory.map((ev, idx) => (
                  <div key={ev.event_id || idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-start gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-teal-500 mt-1.5 shrink-0" />
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-extrabold text-slate-800 text-[11px]">{ev.event_type}</span>
                        <span className="text-[10px] text-slate-400">{new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <p className="text-[11px] text-slate-600">{ev.description}</p>
                      {ev.review_comment && (
                        <p className="text-[10px] text-teal-800 font-medium italic bg-teal-50 p-1 rounded">
                          "{ev.review_comment}"
                        </p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modals */}
      {/* 1. Modal: ACCEPT AI SCREENING */}
      {activeModal === 'ACCEPT' && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <span>{t('modalAcceptTitle') || 'Accept AI Screening Result'}</span>
              </h3>
              <button type="button" onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {t('modalAcceptMsg') || 'Are you sure you want to accept this AI-assisted screening result?'}
            </p>

            <div className="p-3 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 space-y-1">
              <div className="font-bold">Original AI Result: {originalAiDisplay}</div>
              <div className="text-[11px]">Reviewer: Dr. A. Swaminathan, MS</div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loadingAction}
                onClick={handleAcceptAi}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition"
              >
                {loadingAction ? 'Processing...' : 'Confirm Accept'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Modal: MODIFY / OVERRIDE RESULT */}
      {activeModal === 'MODIFY' && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                <Edit3 className="w-5 h-5 text-brand-600" />
                <span>{t('modalModifyTitle') || 'Modify / Override Screening Result'}</span>
              </h3>
              <button type="button" onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  {t('lblSelectReviewedClass') || 'Reviewed Classification'}
                </label>
                <select
                  value={overrideClass}
                  onChange={(e) => setOverrideClass(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-bold text-slate-800 focus:ring-2 focus:ring-brand-500"
                >
                  {DR_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  {t('lblReviewReason') || 'Clinical Review Reason (Required for Override)'}
                </label>
                <textarea
                  rows="3"
                  value={overrideComment}
                  onChange={(e) => {
                    setOverrideComment(e.target.value);
                    if (commentError) setCommentError('');
                  }}
                  placeholder={t('placeholderReviewReason') || 'e.g., Clinical review indicates Mild NPDR based on isolated microaneurysms...'}
                  className={`w-full p-2.5 rounded-xl border text-xs ${
                    commentError ? 'border-rose-500 ring-2 ring-rose-200' : 'border-slate-300 focus:ring-2 focus:ring-brand-500'
                  }`}
                />
                {commentError && (
                  <p className="text-[11px] font-bold text-rose-600 mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>{commentError}</span>
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loadingAction}
                onClick={handleModifyResult}
                className="px-5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-sm transition"
              >
                {loadingAction ? 'Processing...' : 'Submit Override'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. Modal: REQUEST IMAGE RE-CAPTURE */}
      {activeModal === 'RECAPTURE' && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-amber-600" />
                <span>{t('modalRecaptureTitle') || 'Request Image Re-capture'}</span>
              </h3>
              <button type="button" onClick={() => setActiveModal(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {t('modalRecaptureMsg') || 'Please confirm that image quality or artifacts require re-capturing the fundus scan.'}
            </p>

            <div className="space-y-1 text-xs">
              <label className="block font-bold text-slate-700">Guidance for Health Worker</label>
              <textarea
                rows="2"
                value={recaptureComment}
                onChange={(e) => setRecaptureComment(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={loadingAction}
                onClick={handleRequestRecapture}
                className="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-sm transition"
              >
                {loadingAction ? 'Processing...' : 'Confirm Re-capture'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
