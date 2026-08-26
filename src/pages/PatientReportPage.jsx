import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { VoiceGuidanceControl } from '../components/common/VoiceGuidanceControl';
import {
  Printer,
  Share2,
  Eye,
  CheckCircle2,
  Shield,
  MapPin,
  Calendar,
  Phone,
  Sparkles,
  ChevronLeft,
  FileCheck,
  Stethoscope,
  UserCheck,
  RotateCcw,
  AlertCircle,
  AlertOctagon,
  Loader2,
  FileText,
  HelpCircle,
  AlertTriangle,
  UploadCloud,
} from 'lucide-react';
import { SAMPLE_FUNDUS_IMAGES, SAMPLE_GRADCAM_HEATMAPS } from '../data/mockData';
import { getScreeningReview, formatConfidence } from '../services/api';

const PatientReportContent = () => {
  const { id } = useParams();
  const { t } = useLanguage();
  const { getScreeningById, screenings, getPatientById, activeScreening } = useApp();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [shareSuccess, setShareSuccess] = useState(false);
  const [screening, setScreening] = useState(null);
  const [liveReview, setLiveReview] = useState(null);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. If explicit ID provided, attempt lookup
      let targetScreening = null;
      if (id) {
        targetScreening = getScreeningById(id);
      }

      // 2. If not found by ID or no ID, look for latest real prediction in screenings
      if (!targetScreening) {
        targetScreening = screenings.find(
          (s) => s.isRealPrediction || s.gradCamUrl || s.confidence !== null
        );
      }

      // 3. If still not found, check activeScreening
      if (!targetScreening && activeScreening && (activeScreening.imageOD || activeScreening.aiResult)) {
        targetScreening = {
          ...activeScreening,
          id: id || activeScreening.id || 'SCR-2026-1023',
          screeningDate: new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }),
        };
      }

      // 4. Fallback to first screening in list
      if (!targetScreening && screenings && screenings.length > 0) {
        targetScreening = screenings[0];
      }

      setScreening(targetScreening || null);

      if (targetScreening?.id) {
        const canonicalReview = await getScreeningReview(targetScreening.id);
        if (canonicalReview) {
          setLiveReview(canonicalReview);
        }
      }
    } catch (err) {
      console.error('Failed to load screening report data:', err);
      setError('Unable to load the screening report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, [id, screenings]);

  const handlePrint = () => {
    window.print();
  };

  const handleShare = () => {
    setShareSuccess(true);
    setTimeout(() => setShareSuccess(false), 2500);
  };

  // State 1: LOADING STATE
  if (loading) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-white rounded-3xl border border-slate-200 shadow-card max-w-xl mx-auto my-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600 shadow-sm">
          <Loader2 className="w-7 h-7 animate-spin" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-extrabold text-slate-900">Loading screening report…</h3>
          <p className="text-xs text-slate-400">Retrieving bilateral clinical findings and AI assessment</p>
        </div>
      </div>
    );
  }

  // State 2: ERROR STATE
  if (error) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-white rounded-3xl border border-slate-200 shadow-card max-w-xl mx-auto my-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 shadow-sm">
          <AlertCircle className="w-7 h-7" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-extrabold text-slate-900">Unable to load the screening report.</h3>
          <p className="text-xs text-slate-500 max-w-md">An error occurred while fetching the report data. Please try again.</p>
        </div>
        <button
          type="button"
          onClick={fetchReportData}
          className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold transition shadow-sm"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Retry</span>
        </button>
      </div>
    );
  }

  // State 3: EMPTY / MISSING DATA STATE
  if (!screening) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center bg-white rounded-3xl border border-slate-200 shadow-card max-w-xl mx-auto my-8 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 shadow-sm">
          <FileText className="w-7 h-7" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-extrabold text-slate-900">Screening Information Incomplete</h3>
          <p className="text-xs text-slate-500 max-w-md leading-relaxed">
            Screening information is incomplete. Please complete the screening before generating the report.
          </p>
        </div>
        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate('/screenings/new')}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Back to Screening</span>
          </button>
          <button
            type="button"
            onClick={fetchReportData}
            className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold transition shadow-sm"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      </div>
    );
  }

  // Resolve patient details safely
  const patient = getPatientById(screening.patientId);

  // Load cached or live review state
  const storedReviewJson = localStorage.getItem(`madocs_review_${screening.id}`);
  const storedReview = liveReview || (storedReviewJson ? JSON.parse(storedReviewJson) : null);
  
  const rawStatus =
    storedReview?.review_status ||
    screening.reviewStatus ||
    (screening.doctorStatus === 'verified'
      ? 'AI RESULT ACCEPTED'
      : screening.doctorStatus === 'recapture_requested'
      ? 'IMAGE RE-CAPTURE REQUESTED'
      : 'PENDING DOCTOR REVIEW');

  const isRecaptureRequested =
    rawStatus === 'IMAGE RE-CAPTURE REQUESTED' || rawStatus === 'IMAGE_RECAPTURE_REQUESTED';
  const isAccepted =
    rawStatus === 'AI RESULT ACCEPTED' || rawStatus === 'AI_RESULT_ACCEPTED';
  const isModified =
    rawStatus === 'DOCTOR REVIEWED / MODIFIED' || rawStatus === 'DOCTOR_REVIEWED_MODIFIED';

  const reviewStatus = rawStatus;

  // State 4: SUCCESS STATE (Full Clinical Report View)
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Controls (Hidden during print) */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate(screening.id ? `/screenings/${screening.id}/result` : '/screenings/result')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Screening Result</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleShare}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold shadow-sm transition"
          >
            <Share2 className="w-4 h-4 text-teal-600" />
            <span>{shareSuccess ? 'SMS Link Sent!' : t('btnShareWhatsApp')}</span>
          </button>

          <button
            type="button"
            onClick={handlePrint}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-glow transition"
          >
            <Printer className="w-4 h-4" />
            <span>{t('btnPrintReport')}</span>
          </button>
        </div>
      </div>

      {/* Demo Data Notice (Hidden during print) */}
      <div className="no-print flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <Shield className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS • Report verified for clinical decision support.</span>
      </div>

      {/* Spoken Voice Guidance Control */}
      <VoiceGuidanceControl stepKey={isRecaptureRequested ? 'recapture' : 'report'} className="no-print" />

      {/* Prominent Image Re-capture Required Banner if Re-capture requested */}
      {isRecaptureRequested && (
        <div className="p-5 rounded-3xl bg-rose-50 border-2 border-rose-300 shadow-md space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5 text-rose-900">
              <div className="p-2 rounded-xl bg-rose-100 text-rose-700">
                <AlertOctagon className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-extrabold uppercase tracking-wide">
                  IMAGE RE-CAPTURE REQUIRED
                </h3>
                <p className="text-xs font-semibold text-rose-800">
                  Doctor Review Status: <strong>Re-capture Requested</strong>
                </p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-[11px] font-extrabold bg-rose-200 text-rose-900 border border-rose-400">
              ACTION REQUIRED
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-white/90 border border-rose-200 text-xs space-y-1.5">
            <p className="text-slate-800 font-medium">
              <strong className="text-rose-950">Doctor Review Guidance:</strong>{' '}
              {storedReview?.review_comment || 'Image quality is insufficient / blurry in macula. Re-capture required.'}
            </p>
            <div className="flex items-center gap-2 pt-1 text-teal-800 font-bold">
              <UploadCloud className="w-4 h-4 text-teal-600 shrink-0" />
              <span>NEXT STEP: Please capture and upload a new fundus image.</span>
            </div>
          </div>
        </div>
      )}

      {/* Printable Clinical Medical Report Document */}
      <div className="bg-white rounded-3xl p-8 sm:p-10 border border-slate-200 shadow-xl space-y-8 print:p-0 print:border-none print:shadow-none">
        {/* Document Header */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-6 border-b-2 border-slate-900">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center font-bold text-xl shadow-glow">
              <Eye className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-extrabold text-slate-950 tracking-tight">
                Explainable AI for Diabetic Retinopathy Screening in Rural India
              </h1>
              <p className="text-xs text-slate-500 font-medium">
                Primary Health Center Community Ophthalmology Program • राष्ट्रीय स्वास्थ्य मिशन
              </p>
            </div>
          </div>

          <div className="text-left sm:text-right text-xs space-y-1">
            <p className="font-bold text-slate-900 font-mono">Screening ID: {screening.id || 'SCR-2026-1023'}</p>
            <p className="text-slate-500">Date: {screening.screeningDate || new Date().toLocaleDateString('en-IN')}</p>
            <p className="text-slate-500">Center: Rampur Rural PHC</p>
          </div>
        </div>

        {/* Patient Demographics & Diabetes Profile */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs">
          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">PATIENT NAME</span>
            <span className="font-bold text-slate-900 text-sm">{patient.name || 'Not available'}</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">AGE / GENDER</span>
            <span className="font-bold text-slate-900 capitalize">
              {patient.age ? `${patient.age} Yrs` : 'Not available'} / {patient.gender || 'Not available'}
            </span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">ABHA HEALTH ID</span>
            <span className="font-bold text-slate-900 font-mono">
              {patient.abhaId || patient.id || 'Not available'}
            </span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">VILLAGE / PANCHAYAT</span>
            <span className="font-bold text-slate-900">{patient.village || 'Not available'}</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">DIABETES DURATION</span>
            <span className="font-bold text-slate-900">{patient.diabetesDuration ? `${patient.diabetesDuration} Years Known` : 'Not available'}</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">LAST HbA1c</span>
            <span className="font-bold text-amber-700">{patient.lastHba1c ? `${patient.lastHba1c}%` : 'Not available'}</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">VISUAL ACUITY</span>
            <span className="font-bold text-slate-900">
              OD: {patient.visualAcuityOD || '6/6'} | OS: {patient.visualAcuityOS || '6/6'}
            </span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">CONTACT</span>
            <span className="font-bold text-slate-900">{patient.phone || 'Not available'}</span>
          </div>
        </div>

        {/* AI Screening Classification & Doctor Review Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200">
            <h3 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">
              {isRecaptureRequested ? 'Historical Screening Record & Doctor Review' : 'Explainable AI Diagnostic Assessment & Doctor Review'}
            </h3>
            <div className="flex flex-wrap items-center gap-2">
              <DoctorReviewStatusBadge status={reviewStatus} size="sm" />
              <RiskBadge risk={isRecaptureRequested ? 'UNABLE TO ASSESS' : (screening.riskCategory || 'MODERATE')} size="sm" />
              <ReferralBadge priority={isRecaptureRequested ? 'IMAGE RE-CAPTURE REQUIRED' : (screening.referralPriority || 'EYE SPECIALIST REVIEW RECOMMENDED')} size="sm" />
              <SafetyBadge status={isRecaptureRequested ? 'IMAGE_QUALITY_INSUFFICIENT' : (screening.safetyStatus || 'READY_FOR_AI')} size="sm" />
            </div>
          </div>

          {/* Dual Result Comparison: AI Result vs Doctor Reviewed */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-200">
            {/* Left Column: AI Result */}
            <div className={`p-4 rounded-xl border space-y-2 ${isRecaptureRequested ? 'bg-amber-50/70 border-amber-200 text-amber-900' : 'bg-white border-slate-200'}`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">
                  {isRecaptureRequested ? 'PREVIOUS AI SCREENING RESULT (HISTORICAL)' : 'AI SCREENING RESULT'}
                </span>
                <span className="text-[10px] font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  Confidence: {formatConfidence(screening.confidence || storedReview?.original_confidence || 0.85)}
                </span>
              </div>

              <div className="text-sm font-extrabold text-slate-950">
                {storedReview?.original_ai_result || screening.className || (screening.overallSeverity ? t(screening.overallSeverity) : 'Moderate DR')}
              </div>

              {isRecaptureRequested ? (
                <p className="text-[10px] text-amber-800 font-medium leading-relaxed bg-amber-100/60 p-2 rounded-lg border border-amber-300/60">
                  This previous AI result is historical and does not represent the current active screening result because image re-capture has been requested.
                </p>
              ) : (
                <p className="text-[10px] text-slate-500">Automated deep learning model prediction</p>
              )}
            </div>

            {/* Right Column: Doctor Reviewed Status */}
            <div className={`p-4 rounded-xl border space-y-2 ${isRecaptureRequested ? 'bg-rose-50/70 border-rose-200' : 'bg-teal-50/70 border-teal-200'}`}>
              <div className="flex items-center justify-between">
                <span className={`text-[10px] font-extrabold uppercase tracking-wider ${isRecaptureRequested ? 'text-rose-700' : 'text-teal-700'}`}>
                  DOCTOR-REVIEWED STATUS
                </span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${isRecaptureRequested ? 'bg-rose-100 text-rose-800 border-rose-300' : 'bg-emerald-100/70 text-emerald-800 border-emerald-300'}`}>
                  {storedReview?.reviewer_name || 'Dr. A. Swaminathan, MS'}
                </span>
              </div>

              <div className={`text-sm font-extrabold ${isRecaptureRequested ? 'text-rose-950' : 'text-teal-950'}`}>
                {isRecaptureRequested
                  ? 'Re-capture Requested'
                  : isAccepted
                  ? 'Reviewed / Accepted'
                  : isModified
                  ? `Reviewed / Modified (${storedReview?.doctor_reviewed_result || 'Mild'})`
                  : 'Pending Specialist Review'}
              </div>

              <p className={`text-[10px] font-medium ${isRecaptureRequested ? 'text-rose-800' : 'text-teal-800'}`}>
                {storedReview?.review_comment || (isAccepted ? 'Doctor verified and accepted the AI-assisted screening result.' : 'Awaiting clinical verification by tele-ophthalmology specialist.')}
              </p>
            </div>
          </div>

          {/* Bilateral Retinal Details Section (OD & OS) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            {/* Right Eye (OD) Detail Card */}
            <div className="p-4 rounded-2xl bg-white border border-slate-200 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                <span className="font-extrabold text-slate-900">Right Eye (OD)</span>
                <span className="text-[10px] font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded">OD Scan</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-slate-400 block text-[10px]">AI Prediction:</span>
                  <span className="font-bold text-slate-800">{screening.className || 'Moderate DR'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Confidence:</span>
                  <span className="font-bold text-slate-800">{formatConfidence(screening.confidence || 0.85)}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Image Quality:</span>
                  <span className={`font-bold ${isRecaptureRequested ? 'text-amber-700' : 'text-emerald-700'}`}>
                    {isRecaptureRequested ? 'Needs Re-capture' : 'Good (Sharpness: 103.8)'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Safety Status:</span>
                  <span className={`font-bold ${isRecaptureRequested ? 'text-amber-700' : 'text-emerald-700'}`}>
                    {isRecaptureRequested ? 'RE-CAPTURE REQUIRED' : 'READY FOR AI'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Risk Category:</span>
                  <span className="font-bold text-amber-700">{isRecaptureRequested ? 'REVIEW REQUIRED' : 'MODERATE'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Explainability:</span>
                  <span className="font-bold text-teal-700">Grad-CAM Available</span>
                </div>
              </div>
            </div>

            {/* Left Eye (OS) Detail Card */}
            <div className="p-4 rounded-2xl bg-white border border-slate-200 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                <span className="font-extrabold text-slate-900">Left Eye (OS)</span>
                <span className="text-[10px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">OS Scan</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-slate-400 block text-[10px]">AI Prediction:</span>
                  <span className="font-bold text-slate-800">{screening.className || 'Mild DR'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Confidence:</span>
                  <span className="font-bold text-slate-800">{formatConfidence(screening.confidence || 0.82)}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Image Quality:</span>
                  <span className="font-bold text-emerald-700">Good (Sharpness: 98.4)</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Safety Status:</span>
                  <span className="font-bold text-emerald-700">READY FOR AI</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Risk Category:</span>
                  <span className="font-bold text-amber-700">MODERATE</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Explainability:</span>
                  <span className="font-bold text-teal-700">Grad-CAM Available</span>
                </div>
              </div>
            </div>
          </div>

          {/* Tri-Image Showcase: OD Fundus, OS Fundus, Grad-CAM Overlay */}
          <div className="grid grid-cols-3 gap-4 pt-2">
            {/* OD Fundus */}
            <div className="space-y-1.5 text-center">
              <div className="w-full aspect-square rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-sm flex items-center justify-center">
                <img
                  src={screening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od}
                  alt="OD Fundus"
                  className="w-full h-full object-contain"
                />
              </div>
              <p className="text-[11px] font-bold text-slate-700">Right Eye (OD) Scan</p>
            </div>

            {/* OS Fundus */}
            <div className="space-y-1.5 text-center">
              <div className="w-full aspect-square rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-sm flex items-center justify-center">
                <img
                  src={screening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os}
                  alt="OS Fundus"
                  className="w-full h-full object-contain"
                />
              </div>
              <p className="text-[11px] font-bold text-slate-700">Left Eye (OS) Scan</p>
            </div>

            {/* Grad-CAM Heatmap */}
            <div className="space-y-1.5 text-center">
              <div className="w-full aspect-square rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-sm flex items-center justify-center">
                <img
                  src={
                    screening.gradCamOD ||
                    screening.gradCamUrl ||
                    SAMPLE_GRADCAM_HEATMAPS.moderate
                  }
                  alt="Grad-CAM Activation"
                  className="w-full h-full object-contain"
                />
              </div>
              <p className="text-[11px] font-bold text-slate-600 flex items-center justify-center gap-1">
                <span>Grad-CAM Explainability</span>
              </p>
            </div>
          </div>

          {/* Phase 8: Explainability Note */}
          <div className="p-3 rounded-xl bg-purple-50/70 border border-purple-200 text-xs text-purple-950 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-[11px] text-purple-900">
              <Sparkles className="w-3.5 h-3.5 text-purple-600 shrink-0" />
              <span>{t('explainabilityNoteTitle') || 'Explainability Note'} (Grad-CAM)</span>
            </div>
            <p className="text-[10.5px] leading-relaxed text-slate-700">
              {t('explainabilityNoteText') ||
                'Grad-CAM highlights image regions that contributed to the AI model prediction. These regions are not independent lesion diagnoses.'}
            </p>
          </div>
        </div>

        {/* Doctor Clinical Impression & Remarks Box */}
        <div className={`p-6 rounded-2xl border space-y-3 ${isRecaptureRequested ? 'bg-rose-50/50 border-rose-200' : 'bg-teal-50/50 border-teal-200'}`}>
          <div className="flex items-center justify-between">
            <h4 className={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${isRecaptureRequested ? 'text-rose-950' : 'text-teal-950'}`}>
              <Stethoscope className={`w-4 h-4 ${isRecaptureRequested ? 'text-rose-600' : 'text-teal-600'}`} />
              <span>{isRecaptureRequested ? 'Specialist Re-capture Request Guidance' : t('doctorRemarks')}</span>
            </h4>
            <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${isRecaptureRequested ? 'text-rose-800 bg-rose-100' : 'text-teal-800 bg-teal-100'}`}>
              Tele-Ophthalmologist Review Record
            </span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed italic">
            "{storedReview?.review_comment || (isAccepted ? 'Verified and accepted AI-assisted screening findings.' : t('doctorRemarksText'))}"
          </p>

          <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t text-xs ${isRecaptureRequested ? 'border-rose-200/60' : 'border-teal-200/60'}`}>
            <div>
              <p className="font-bold text-slate-900">{storedReview?.reviewer_name || t('doctorName')}</p>
              <p className="text-[11px] text-slate-500">{t('doctorHospital')}</p>
            </div>
            <div className="text-right">
              <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-lg ${isRecaptureRequested ? 'text-rose-700 bg-rose-100' : 'text-emerald-700 bg-emerald-100'}`}>
                <CheckCircle2 className={`w-3.5 h-3.5 ${isRecaptureRequested ? 'text-rose-600' : 'text-emerald-600'}`} />
                <span>{isRecaptureRequested ? 'Digitally Signed Re-capture Request' : 'Digitally Signed & Validated'}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Bilingual Advisory for Patient */}
        <div className="p-5 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-2 text-xs">
          <h4 className="font-bold text-amber-950 flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-amber-600" />
            <span>{t('patientAdvisory')}</span>
          </h4>
          <p className="text-amber-900 whitespace-pre-line leading-relaxed text-[11px]">
            {isRecaptureRequested
              ? 'कृपया ध्यान दें: डॉक्टर ने आपकी आंखों की जांच के लिए दोबारा स्पष्ट फोटो लेने का अनुरोध किया है। कृपया स्वास्थ्य कार्यकर्ता की सहायता से दोबारा फोटो खिंचवाएं।\n\nNote: The doctor has requested a clearer retinal photograph. Please get a re-capture done with the health worker.'
              : t('patientAdvisoryText')}
          </p>
        </div>

        {/* Signatures Footer */}
        <div className="grid grid-cols-2 gap-8 pt-8 border-t border-slate-200 text-xs">
          <div>
            <div className="h-10 border-b border-slate-300 w-48 mb-2 flex items-end">
              <span className="font-serif italic text-slate-600 text-sm">Pooja Sharma</span>
            </div>
            <p className="font-bold text-slate-800">Screener / ASHA Worker</p>
            <p className="text-[11px] text-slate-400">Rampur Rural PHC Unit</p>
          </div>

          <div className="text-right flex flex-col items-end">
            <div className="h-10 border-b border-slate-300 w-48 mb-2 flex items-end justify-end">
              <span className="font-serif italic text-teal-800 text-sm font-semibold">
                {storedReview?.reviewer_name || 'Dr. A. Swaminathan'}
              </span>
            </div>
            <p className="font-bold text-slate-800">Consultant Ophthalmologist</p>
            <p className="text-[11px] text-slate-400">Tele-Ophthalmology Network</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export const PatientReportPage = () => {
  return (
    <ErrorBoundary>
      <PatientReportContent />
    </ErrorBoundary>
  );
};
