import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  Cpu,
  CheckCircle2,
  Loader2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Eye,
  Layers,
  AlertCircle,
  RefreshCw,
  ArrowLeft,
  XCircle,
} from 'lucide-react';
import { SAMPLE_FUNDUS_IMAGES } from '../data/mockData';
import {
  analyzeRetinalImage,
  getSeverityKeyFromClass,
  getUrgencyFromClass,
  getFullResultUrl,
  formatConfidence,
} from '../services/api';

export const AiAnalysisPage = () => {
  const { t } = useLanguage();
  const { activeScreening, setActiveScreening, addScreening } = useApp();
  const navigate = useNavigate();

  const [progress, setProgress] = useState(15);
  const [currentStage, setCurrentStage] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState(null);
  
  // Independent bilateral analysis states
  const [rightEyeResult, setRightEyeResult] = useState(null);
  const [leftEyeResult, setLeftEyeResult] = useState(null);
  const [odErrorState, setOdErrorState] = useState(null);
  const [osErrorState, setOsErrorState] = useState(null);

  const hasStartedRef = useRef(false);

  const stages = [
    { name: t('pipeStage1'), desc: 'Adaptive Histogram Equalization & Illumination Normalization' },
    { name: t('pipeStage2'), desc: 'Verifying macula/disc centering, blur index & optical clarity (OD & OS)' },
    { name: t('pipeStage3'), desc: 'Extracting microaneurysms, hemorrhages, and exudate feature vectors' },
    { name: t('pipeStage4'), desc: 'Computing independent convolutional Grad-CAM gradient maps for OD and OS' },
    { name: t('pipeStage5'), desc: 'Stratifying International Clinical DR (ICDR) grades & referral urgency' },
  ];

  const executeAnalysis = async () => {
    setIsProcessing(true);
    setError(null);
    setProgress(15);
    setCurrentStage(0);
    setCompleted(false);
    setRightEyeResult(null);
    setLeftEyeResult(null);
    setOdErrorState(null);
    setOsErrorState(null);

    // Determine sources for OD and OS
    const imageSourceOD =
      activeScreening.fileOD || activeScreening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od;
    const imageSourceOS =
      activeScreening.fileOS || activeScreening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os;

    // Progress animation interval while waiting for backend
    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 92) return 92; // Hold at 92% until API responses complete
        const next = prev + 10;
        if (next > 25 && currentStage < 1) setCurrentStage(1);
        if (next > 50 && currentStage < 2) setCurrentStage(2);
        if (next > 72 && currentStage < 3) setCurrentStage(3);
        if (next >= 90 && currentStage < 4) setCurrentStage(4);
        return next;
      });
    }, 450);

    try {
      // Determine which eyes are scheduled for analysis
      const shouldAnalyzeOD =
        activeScreening.screeningTargetMode === 'OD' ||
        activeScreening.screeningTargetMode === 'BOTH' ||
        (!activeScreening.screeningTargetMode && imageSourceOD);

      const shouldAnalyzeOS =
        activeScreening.screeningTargetMode === 'OS' ||
        activeScreening.screeningTargetMode === 'BOTH' ||
        (!activeScreening.screeningTargetMode && imageSourceOS);

      // 1. Analyze Right Eye (OD) if selected
      let odRes = null;
      let odErr = null;
      if (shouldAnalyzeOD && imageSourceOD) {
        try {
          odRes = await analyzeRetinalImage(imageSourceOD, 'od_retinal_scan.png');
        } catch (err) {
          console.error('OD Analysis failed:', err);
          odErr = err;
        }
      }

      // 2. Analyze Left Eye (OS) if selected
      let osRes = null;
      let osErr = null;
      if (shouldAnalyzeOS && imageSourceOS) {
        try {
          osRes = await analyzeRetinalImage(imageSourceOS, 'os_retinal_scan.png');
        } catch (err) {
          console.error('OS Analysis failed:', err);
          osErr = err;
        }
      }

      clearInterval(progressTimer);
      setOdErrorState(odErr);
      setOsErrorState(osErr);

      // If all scheduled eyes failed, raise clear error
      if (!odRes && !osRes) {
        const primaryError = odErr || osErr;
        const isValidationError =
          primaryError?.status === 400 ||
          (primaryError?.message && primaryError.message.toLowerCase().includes('invalid retinal'));

        const message = isValidationError
          ? 'Invalid retinal image. Please upload a valid fundus image.'
          : primaryError?.isConnectionError || primaryError?.status === 0
          ? 'Unable to connect to AI screening service.'
          : primaryError?.message || 'AI analysis failed. Please try again.';

        setIsProcessing(false);
        setError({
          status: primaryError?.status || 400,
          title: isValidationError ? 'Invalid Retinal Image' : 'AI Screening Service Error',
          message,
          detail: primaryError?.message,
        });
        return;
      }

      setProgress(100);
      setCurrentStage(4);
      setCompleted(true);
      setIsProcessing(false);
      setRightEyeResult(odRes);
      setLeftEyeResult(osRes);

      // Save independent bilateral results in activeScreening context
      setActiveScreening((prev) => ({
        ...prev,
        rightEyeAnalysis: odRes,
        leftEyeAnalysis: osRes,
        aiResultOD: odRes,
        aiResultOS: osRes,
        aiResult: odRes || osRes,
        odAnalysisError: odErr ? odErr.message : null,
        osAnalysisError: osErr ? osErr.message : null,
      }));
    } catch (unexpectedErr) {
      clearInterval(progressTimer);
      setIsProcessing(false);
      console.error('Unexpected analysis failure:', unexpectedErr);
      setError({
        status: 500,
        title: 'AI Screening Service Error',
        message: 'AI analysis failed. Please try again.',
        detail: unexpectedErr.message,
      });
    }
  };

  useEffect(() => {
    if (!hasStartedRef.current) {
      hasStartedRef.current = true;
      executeAnalysis();
    }
  }, []);

  const handleComplete = () => {
    if (!rightEyeResult && !leftEyeResult) return;

    const odRes = rightEyeResult;
    const osRes = leftEyeResult;

    // ICDR Grade mappings for each eye
    const odSeverityKey = odRes ? getSeverityKeyFromClass(odRes.predicted_class) : 'drUncertain';
    const osSeverityKey = osRes ? getSeverityKeyFromClass(osRes.predicted_class) : 'drUncertain';

    // Overall diagnosis is driven by the maximum (worse) severity grade between both eyes
    const odClass = odRes ? odRes.predicted_class : -1;
    const osClass = osRes ? osRes.predicted_class : -1;
    const maxGrade = Math.max(odClass, osClass);
    const overallClass = maxGrade >= 0 ? maxGrade : 0;
    const overallSeverity = getSeverityKeyFromClass(overallClass);
    const overallUrgency = getUrgencyFromClass(overallClass);

    // Primary eye for overall stats (prefer worse eye, or available eye)
    const primaryRes = (odClass >= osClass && odRes) ? odRes : (osRes || odRes);

    // Biological feature indicators
    const biomarkersForGrade = {
      0: [],
      1: ['Microaneurysms (<5)'],
      2: ['Dot/Blot Hemorrhages', 'Hard Exudates', 'Microaneurysms'],
      3: ['Extensive Intraretinal Hemorrhages (4 quadrants)', 'Venous Beading (2 quadrants)', 'IRMA (1 quadrant)'],
      4: ['Neovascularization (NVD/NVE)', 'Preretinal/Vitreous Hemorrhage', 'Fibrovascular Proliferation'],
    };

    const combinedBiomarkers = Array.from(
      new Set([
        ...(odRes ? biomarkersForGrade[odRes.predicted_class] || [] : []),
        ...(osRes ? biomarkersForGrade[osRes.predicted_class] || [] : []),
      ])
    );

    const totalInferenceTime = Number(
      ((odRes?.inference_time || 0) + (osRes?.inference_time || 0)).toFixed(4)
    );

    const newScr = addScreening({
      patientId: activeScreening.patientId || 'PAT-2026-081',
      patientName: activeScreening.patientName || 'Ramesh Kumar Verma',
      age: 58,
      village: 'Rampur Gram Panchayat',
      campName: activeScreening.campLocation || 'Rampur PHC Community Camp',
      cameraModel: activeScreening.cameraModel || 'Forus 3nethra Classic HD',
      dilation: activeScreening.dilation || 'undilated',
      screenerName: activeScreening.screenerName || 'Pooja Sharma (ASHA Worker)',
      rightEyeAnalysis: odRes,
      leftEyeAnalysis: osRes,
      aiResultOD: odRes,
      aiResultOS: osRes,
      predictedClass: overallClass,
      className: primaryRes?.class_name || 'DR Screening',
      drSeverityOD: odSeverityKey,
      drSeverityOS: osSeverityKey,
      overallSeverity: overallSeverity,
      confidence: primaryRes?.confidence ?? 0,
      probabilities: primaryRes?.probabilities || null,
      safetyStatusOD: odRes?.safety_status || (odErrorState ? 'IMAGE_INVALID' : 'READY_FOR_AI'),
      safetyStatusOS: osRes?.safety_status || (osErrorState ? 'IMAGE_INVALID' : 'READY_FOR_AI'),
      screeningStatusOD: odRes?.screening_status || (odErrorState ? 'UNABLE TO ASSESS' : 'RELIABLE AI SCREENING'),
      screeningStatusOS: osRes?.screening_status || (osErrorState ? 'UNABLE TO ASSESS' : 'RELIABLE AI SCREENING'),
      isLowConfidenceOD: odRes?.is_low_confidence || false,
      isLowConfidenceOS: osRes?.is_low_confidence || false,
      safetyStatus: primaryRes?.safety_status || 'READY_FOR_AI',
      screeningStatus: primaryRes?.screening_status || 'RELIABLE AI SCREENING',
      isLowConfidence: primaryRes?.is_low_confidence || false,
      nextStep: primaryRes?.next_step || 'Continue to explanation / specialist review.',
      confidenceThreshold: primaryRes?.confidence_threshold || 0.60,
      gradCamUrl: getFullResultUrl(primaryRes?.gradcam_url),
      gradCamOD: odRes ? getFullResultUrl(odRes.gradcam_url) : null,
      gradCamOS: osRes ? getFullResultUrl(osRes.gradcam_url) : null,
      explanation: primaryRes?.explanation,
      disclaimer: primaryRes?.disclaimer,
      inferenceTime: totalInferenceTime,
      referralUrgency: overallUrgency,
      biomarkers: combinedBiomarkers,
      imageOD: activeScreening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od,
      imageOS: activeScreening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os,
      isRealPrediction: true,
      doctorRemarks: `Bilateral Analysis: OD=${odRes ? `${odRes.class_name} (${formatConfidence(odRes.confidence)}) [${odRes.screening_status}]` : (odErrorState ? 'Rejected: Safety Gate Blocked' : 'Not Analyzed')}, OS=${osRes ? `${osRes.class_name} (${formatConfidence(osRes.confidence)}) [${osRes.screening_status}]` : (osErrorState ? 'Rejected: Safety Gate Blocked' : 'Not Analyzed')}. Overall: ${overallSeverity.toUpperCase()}.`,
    });

    navigate(`/screenings/${newScr.id}/result`);
  };

  const hasAnyResult = Boolean(rightEyeResult || leftEyeResult);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card text-center space-y-3">
        <div className="inline-flex w-14 h-14 rounded-2xl bg-brand-50 border border-brand-200 items-center justify-center text-brand-600 shadow-glow mb-1">
          <Cpu className={`w-7 h-7 ${isProcessing ? 'animate-pulse' : ''}`} />
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900">{t('analysisTitle')}</h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-xl mx-auto">
          {t('analysisSubtitle')}
        </p>

        {/* Progress Bar */}
        <div className="max-w-md mx-auto space-y-2 pt-2">
          <div className="flex items-center justify-between text-xs font-bold text-slate-700">
            <span>Bilateral Inference Pipeline (Retinal Quality Gate + EfficientNet-B0)</span>
            <span className="text-brand-600 font-mono">{progress}%</span>
          </div>
          <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden p-0.5 border border-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-300 shadow-glow ${
                error
                  ? 'bg-rose-500'
                  : 'bg-gradient-to-r from-brand-600 via-teal-500 to-indigo-600'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Error Alert Display */}
      {error && (
        <div className="p-6 rounded-3xl bg-rose-50 border border-rose-200 text-rose-900 shadow-card space-y-4">
          <div className="flex items-start gap-3.5">
            <div className="p-2 rounded-2xl bg-rose-100 text-rose-600 shrink-0">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div className="flex-1 space-y-1">
              <h4 className="text-base font-extrabold text-rose-950">
                {error.title || 'Invalid Retinal Image'}
              </h4>
              <p className="text-xs text-rose-800 leading-relaxed font-medium">
                {error.message || 'Please upload a valid retinal fundus photograph.'}
              </p>
              {error.detail && error.detail !== error.message && (
                <p className="text-[11px] text-rose-600 font-mono pt-0.5">{error.detail}</p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-rose-200/70">
            <Link
              to="/screenings/upload"
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-white border border-rose-300 text-rose-800 text-xs font-bold hover:bg-rose-100/60 transition shadow-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Upload / Choose Another Image</span>
            </Link>
            <button
              type="button"
              onClick={executeAnalysis}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-rose-600 text-white text-xs font-bold hover:bg-rose-700 shadow-sm transition"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Retry AI Analysis</span>
            </button>
          </div>
        </div>
      )}

      {/* Bilateral Retinal Scan Visualizer Preview */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Retinal Scans Dual View */}
        <div className="md:col-span-5 flex flex-col sm:flex-row md:flex-col items-center justify-center gap-3">
          {/* OD Preview */}
          <div className="relative w-48 h-48 sm:w-56 sm:h-56 rounded-2xl overflow-hidden bg-black border-2 border-slate-800 shadow-xl">
            <img
              src={activeScreening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od}
              alt="OD Scanning Fundus"
              className="w-full h-full object-contain"
            />
            {isProcessing && (
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-brand-400 to-transparent shadow-[0_0_15px_#10b981] animate-scan pointer-events-none" />
            )}
            <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-white border border-white/10">
              OD (Right Eye)
            </div>
            <div className="absolute bottom-2 inset-x-2 bg-black/70 backdrop-blur-md rounded-lg p-1.5 text-center text-[10px] font-bold border border-white/10">
              {rightEyeResult ? (
                <span className="text-emerald-400">✓ {rightEyeResult.class_name} ({formatConfidence(rightEyeResult.confidence)})</span>
              ) : odErrorState ? (
                <span className="text-rose-400">✗ Invalid Retinal Image</span>
              ) : isProcessing ? (
                <span className="text-brand-300">Validating & Analyzing OD...</span>
              ) : (
                <span className="text-slate-400">Standby</span>
              )}
            </div>
          </div>

          {/* OS Preview */}
          <div className="relative w-48 h-48 sm:w-56 sm:h-56 rounded-2xl overflow-hidden bg-black border-2 border-slate-800 shadow-xl">
            <img
              src={activeScreening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os}
              alt="OS Scanning Fundus"
              className="w-full h-full object-contain"
            />
            {isProcessing && (
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-teal-400 to-transparent shadow-[0_0_15px_#14b8a6] animate-scan pointer-events-none" />
            )}
            <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-bold text-white border border-white/10">
              OS (Left Eye)
            </div>
            <div className="absolute bottom-2 inset-x-2 bg-black/70 backdrop-blur-md rounded-lg p-1.5 text-center text-[10px] font-bold border border-white/10">
              {leftEyeResult ? (
                <span className="text-teal-400">✓ {leftEyeResult.class_name} ({formatConfidence(leftEyeResult.confidence)})</span>
              ) : osErrorState ? (
                <span className="text-rose-400">✗ Invalid Retinal Image</span>
              ) : isProcessing ? (
                <span className="text-teal-300">Validating & Analyzing OS...</span>
              ) : (
                <span className="text-slate-400">Standby</span>
              )}
            </div>
          </div>
        </div>

        {/* 5-Stage Checklist */}
        <div className="md:col-span-7 bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
            Bilateral Execution Stages
          </h3>

          <div className="space-y-3">
            {stages.map((stage, idx) => {
              const isPast = currentStage > idx || completed;
              const isCurrent = currentStage === idx && !completed && !error;

              return (
                <div
                  key={idx}
                  className={`p-3 rounded-2xl border transition-all ${
                    isPast
                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                      : isCurrent
                      ? 'bg-brand-50 border-brand-300 text-brand-950 shadow-sm'
                      : 'bg-slate-50 border-slate-200 text-slate-400 opacity-60'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 shrink-0">
                      {isPast ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 text-brand-600 animate-spin" />
                      ) : (
                        <span className="w-4 h-4 rounded-full border border-slate-300 block text-[10px] text-center font-bold">
                          {idx + 1}
                        </span>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h4 className="text-xs font-bold leading-tight">{stage.name}</h4>
                      <p className="text-[11px] text-slate-500 mt-0.5">{stage.desc}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Completion Action */}
      <div className="flex justify-center pt-2">
        <button
          type="button"
          onClick={handleComplete}
          disabled={!completed || !hasAnyResult}
          className={`inline-flex items-center gap-2 px-8 py-4 rounded-2xl font-bold text-xs shadow-glow transition transform hover:-translate-y-0.5 ${
            completed && hasAnyResult
              ? 'bg-brand-600 hover:bg-brand-700 text-white cursor-pointer'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>{t('btnViewResults')}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
