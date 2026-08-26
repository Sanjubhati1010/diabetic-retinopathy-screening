import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  Upload,
  Eye,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Image as ImageIcon,
  Check,
  RefreshCw,
  AlertTriangle,
  Loader2,
  XCircle,
  ShieldCheck,
  Activity,
  Sliders,
} from 'lucide-react';
import { SAMPLE_FUNDUS_IMAGES } from '../data/mockData';
import { ensureImageFile, validateImageQuality } from '../services/api';
import { VoiceGuidanceControl } from '../components/common/VoiceGuidanceControl';

export const ImageUploadPage = () => {
  const { t } = useLanguage();
  const { activeScreening, setActiveScreening, patients } = useApp();
  const navigate = useNavigate();

  const patient = patients.find((p) => p.id === activeScreening.patientId) || patients[0];

  const [imageOD, setImageOD] = useState(activeScreening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od);
  const [imageOS, setImageOS] = useState(activeScreening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os);
  const [fileOD, setFileOD] = useState(activeScreening.fileOD || null);
  const [fileOS, setFileOS] = useState(activeScreening.fileOS || null);

  // Phase 1 Bilateral Statuses: 'pending' | 'validating' | 'ready' | 'warning' | 'recapture_required'
  const [odStatus, setOdStatus] = useState(activeScreening.odStatus || (imageOD ? 'ready' : 'pending'));
  const [osStatus, setOsStatus] = useState(activeScreening.osStatus || (imageOS ? 'ready' : 'pending'));

  const [odValidation, setOdValidation] = useState(activeScreening.odValidation || null);
  const [osValidation, setOsValidation] = useState(activeScreening.osValidation || null);

  const [odQuality, setOdQuality] = useState({
    illumination: true,
    focus: true,
    noArtifacts: true,
  });

  const [osQuality, setOsQuality] = useState({
    illumination: true,
    focus: true,
    noArtifacts: true,
  });

  // Run initial validation on mount if images exist but no validation result is cached
  useEffect(() => {
    if (imageOD && !odValidation) {
      runValidationForEye(imageOD, fileOD, 'OD');
    }
    if (imageOS && !osValidation) {
      runValidationForEye(imageOS, fileOS, 'OS');
    }
  }, []);

  const runValidationForEye = async (imgSource, fileSource, eye) => {
    const isOD = eye === 'OD';
    if (isOD) {
      setOdStatus('validating');
    } else {
      setOsStatus('validating');
    }

    try {
      const filename = isOD ? 'od_retinal_scan.png' : 'os_retinal_scan.png';
      const result = await validateImageQuality(imgSource, filename);

      if (isOD) {
        setOdValidation(result);
        if (result.can_proceed) {
          setOdStatus(result.quality_grade === 'warning' ? 'warning' : 'ready');
        } else {
          setOdStatus('recapture_required');
        }
      } else {
        setOsValidation(result);
        if (result.can_proceed) {
          setOsStatus(result.quality_grade === 'warning' ? 'warning' : 'ready');
        } else {
          setOsStatus('recapture_required');
        }
      }

      // Update global context
      setActiveScreening((prev) => ({
        ...prev,
        [isOD ? 'odStatus' : 'osStatus']: result.can_proceed
          ? result.quality_grade === 'warning'
            ? 'warning'
            : 'ready'
          : 'recapture_required',
        [isOD ? 'odValidation' : 'osValidation']: result,
      }));
    } catch (err) {
      console.warn(`Validation failed for ${eye}:`, err);
      const fallbackFail = {
        is_valid_file: false,
        is_retinal: false,
        quality_grade: 'insufficient',
        screening_status: 'Image Re-capture Required',
        can_proceed: false,
        reasons: [err.message || 'Please upload a valid image file.'],
        metrics: { resolution: 'Unknown', sharpness_score: 0, brightness_score: 0, retinal_coverage: 0 },
        message: err.message || 'Please upload a valid image file.',
      };
      if (isOD) {
        setOdValidation(fallbackFail);
        setOdStatus('recapture_required');
      } else {
        setOsValidation(fallbackFail);
        setOsStatus('recapture_required');
      }
    }
  };

  const handleFileUpload = (e, eye) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      const isOD = eye === 'OD';
      if (isOD) {
        setFileOD(file);
      } else {
        setFileOS(file);
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        const dataUrl = event.target.result;
        if (isOD) {
          setImageOD(dataUrl);
        } else {
          setImageOS(dataUrl);
        }

        // Clear previous AI results and trigger validation
        setActiveScreening((prev) => ({
          ...prev,
          [isOD ? 'fileOD' : 'fileOS']: file,
          [isOD ? 'imageOD' : 'imageOS']: dataUrl,
          [isOD ? 'rightEyeAnalysis' : 'leftEyeAnalysis']: null,
          [isOD ? 'aiResultOD' : 'aiResultOS']: null,
          [isOD ? 'gradCamOD' : 'gradCamOS']: null,
          [isOD ? 'drSeverityOD' : 'drSeverityOS']: 'drUncertain',
          [isOD ? 'odAnalysisError' : 'osAnalysisError']: null,
          aiResult: null,
          confidence: null,
          probabilities: null,
          gradCamUrl: null,
          overallSeverity: 'drUncertain',
        }));

        runValidationForEye(dataUrl, file, eye);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleLoadSample = async () => {
    const sampleUrlOD = SAMPLE_FUNDUS_IMAGES.sample_od;
    const sampleUrlOS = SAMPLE_FUNDUS_IMAGES.sample_os;
    setImageOD(sampleUrlOD);
    setImageOS(sampleUrlOS);

    try {
      const fileODObj = await ensureImageFile(sampleUrlOD, 'od_sample_retinal_scan.png');
      const fileOSObj = await ensureImageFile(sampleUrlOS, 'os_sample_retinal_scan.png');
      setFileOD(fileODObj);
      setFileOS(fileOSObj);

      setActiveScreening((prev) => ({
        ...prev,
        fileOD: fileODObj,
        fileOS: fileOSObj,
        imageOD: sampleUrlOD,
        imageOS: sampleUrlOS,
        rightEyeAnalysis: null,
        leftEyeAnalysis: null,
        aiResultOD: null,
        aiResultOS: null,
        gradCamOD: null,
        gradCamOS: null,
        drSeverityOD: 'drUncertain',
        drSeverityOS: 'drUncertain',
        odAnalysisError: null,
        osAnalysisError: null,
        aiResult: null,
        confidence: null,
        probabilities: null,
        gradCamUrl: null,
        overallSeverity: 'drUncertain',
      }));

      runValidationForEye(sampleUrlOD, fileODObj, 'OD');
      runValidationForEye(sampleUrlOS, fileOSObj, 'OS');
    } catch (err) {
      console.warn('Could not create files from sample scan:', err);
    }
  };

  const handleClearEye = (eye) => {
    const isOD = eye === 'OD';
    if (isOD) {
      setImageOD(null);
      setFileOD(null);
      setOdStatus('pending');
      setOdValidation(null);
    } else {
      setImageOS(null);
      setFileOS(null);
      setOsStatus('pending');
      setOsValidation(null);
    }

    setActiveScreening((prev) => ({
      ...prev,
      [isOD ? 'imageOD' : 'imageOS']: null,
      [isOD ? 'fileOD' : 'fileOS']: null,
      [isOD ? 'odStatus' : 'osStatus']: 'pending',
      [isOD ? 'odValidation' : 'osValidation']: null,
      [isOD ? 'rightEyeAnalysis' : 'leftEyeAnalysis']: null,
      [isOD ? 'aiResultOD' : 'aiResultOS']: null,
      [isOD ? 'gradCamOD' : 'gradCamOS']: null,
      [isOD ? 'drSeverityOD' : 'drSeverityOS']: 'drUncertain',
      [isOD ? 'odAnalysisError' : 'osAnalysisError']: null,
    }));
  };

  const isODReady = odStatus === 'ready' || odStatus === 'warning';
  const isOSReady = osStatus === 'ready' || osStatus === 'warning';
  const canProceed = isODReady || isOSReady;

  const handleRunAi = async () => {
    let resolvedFileOD = fileOD;
    let resolvedFileOS = fileOS;

    if (!resolvedFileOD && imageOD) {
      try {
        resolvedFileOD = await ensureImageFile(imageOD, 'od_retinal_scan.png');
      } catch (err) {
        console.warn('Could not resolve fileOD:', err);
      }
    }
    if (!resolvedFileOS && imageOS) {
      try {
        resolvedFileOS = await ensureImageFile(imageOS, 'os_retinal_scan.png');
      } catch (err) {
        console.warn('Could not resolve fileOS:', err);
      }
    }

    // Determine target eye mode
    let targetMode = 'BOTH';
    if (isODReady && !isOSReady) targetMode = 'OD';
    if (!isODReady && isOSReady) targetMode = 'OS';

    setActiveScreening((prev) => ({
      ...prev,
      imageOD,
      imageOS,
      fileOD: resolvedFileOD,
      fileOS: resolvedFileOS,
      odStatus,
      osStatus,
      odValidation,
      osValidation,
      rightEyeAnalysis: null,
      leftEyeAnalysis: null,
      aiResultOD: null,
      aiResultOS: null,
      gradCamOD: null,
      gradCamOS: null,
      odAnalysisError: null,
      osAnalysisError: null,
      aiResult: null,
      confidence: null,
      probabilities: null,
      gradCamUrl: null,
      selectedEyeForAnalysis: targetMode === 'OS' ? 'OS' : 'OD',
      screeningTargetMode: targetMode,
      odQuality,
      osQuality,
      qualityChecked: true,
      patientId: patient.id,
      patientName: patient.name,
    }));

    navigate('/screenings/analysis');
  };

  const renderStatusBadge = (status, validation) => {
    switch (status) {
      case 'validating':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sky-50 text-sky-700 border border-sky-200 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-600" />
            <span>{t('statusValidating')}</span>
          </span>
        );
      case 'ready':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>✓ {t('statusReady')}</span>
          </span>
        );
      case 'warning':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>⚠ {t('statusQualityWarning')}</span>
          </span>
        );
      case 'recapture_required':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>✕ {t('statusRecapture')}</span>
          </span>
        );
      case 'pending':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            <span>{t('statusPending')}</span>
          </span>
        );
    }
  };

  const renderEyeUploadCard = (eye, image, file, status, validation, quality, setQuality) => {
    const isOD = eye === 'OD';
    const eyeTitle = isOD ? t('rightEyeOD') : t('leftEyeOS');
    const badgeColor = isOD ? 'bg-brand-500' : 'bg-teal-500';
    const tagLabel = isOD ? 'OD (Right Eye)' : 'OS (Left Eye)';

    return (
      <div
        className={`space-y-4 p-5 rounded-3xl border transition-all ${
          status === 'ready'
            ? 'border-emerald-300 bg-emerald-50/20 shadow-sm'
            : status === 'warning'
            ? 'border-amber-300 bg-amber-50/20 shadow-sm'
            : status === 'recapture_required'
            ? 'border-rose-300 bg-rose-50/20 shadow-sm'
            : 'border-slate-200 bg-slate-50/70'
        }`}
      >
        {/* Card Header with Eye Badge & Screening Status */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${badgeColor}`}></span>
            <h3 className="text-sm font-bold text-slate-900">{eyeTitle}</h3>
          </div>
          <div>{renderStatusBadge(status, validation)}</div>
        </div>

        {/* Fundus Preview Canvas */}
        <div className="relative rounded-2xl overflow-hidden bg-slate-950 aspect-square flex items-center justify-center border border-slate-800 group shadow-inner">
          {image ? (
            <>
              <img
                src={image}
                alt={`${tagLabel} Fundus Scan`}
                className="w-full h-full object-contain"
              />
              <div className="absolute top-2 right-2 flex items-center gap-1.5">
                <label className="px-2.5 py-1 rounded-lg bg-black/75 hover:bg-black/90 text-white text-[11px] font-bold cursor-pointer transition border border-white/20 shadow-sm">
                  <span>{t('btnReupload')}</span>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/jpg"
                    className="hidden"
                    onChange={(e) => handleFileUpload(e, eye)}
                  />
                </label>
                <button
                  type="button"
                  onClick={() => handleClearEye(eye)}
                  className="px-2 py-1 rounded-lg bg-rose-900/80 hover:bg-rose-900 text-white text-[11px] font-bold transition border border-rose-400/30"
                  title="Remove Image"
                >
                  ✕
                </button>
              </div>

              {/* Resolution Tag */}
              {validation?.metrics?.resolution && (
                <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-mono text-slate-300 border border-white/10">
                  {validation.metrics.resolution}
                </div>
              )}
            </>
          ) : (
            <label className="flex flex-col items-center justify-center p-6 text-center cursor-pointer w-full h-full hover:bg-slate-900/50 transition">
              <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mb-2 group-hover:scale-105 transition">
                <Upload className="w-6 h-6 text-slate-400" />
              </div>
              <span className="text-xs font-bold text-slate-200">{t('dragDropText')}</span>
              <span className="text-[10px] text-slate-400 mt-1">{t('supportedFormats')}</span>
              <span className="mt-3 px-3 py-1 rounded-xl bg-brand-600/30 text-brand-300 border border-brand-500/30 text-[11px] font-bold">
                Select {eye} Image
              </span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/jpg"
                className="hidden"
                onChange={(e) => handleFileUpload(e, eye)}
              />
            </label>
          )}
        </div>

        {/* Phase 1 Validation Error / Recapture Alert */}
        {status === 'recapture_required' && validation && (
          <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 space-y-1 text-xs">
            <div className="flex items-center gap-2 font-bold text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{validation.message || 'Image Quality Insufficient'}</span>
            </div>
            {validation.reasons && validation.reasons.length > 0 && (
              <ul className="list-disc list-inside text-[11px] text-rose-800 space-y-0.5 pt-1 pl-1">
                {validation.reasons.map((r, idx) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            )}
            <p className="text-[10px] text-rose-600 pt-1 font-semibold">
              {t('recaptureNote')}
            </p>
          </div>
        )}

        {/* Phase 1 Quality Warning Alert */}
        {status === 'warning' && validation && (
          <div className="p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-1 text-xs">
            <div className="flex items-center gap-2 font-bold text-amber-800">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
              <span>{t('statusQualityWarning')}</span>
            </div>
            {validation.reasons && validation.reasons.length > 0 && (
              <p className="text-[11px] text-amber-800">{validation.reasons[0]}</p>
            )}
          </div>
        )}

        {/* Phase 1 Computed Quality Metrics Breakdown */}
        {validation?.metrics && (
          <div className="bg-white/80 rounded-2xl p-3 border border-slate-200/80 space-y-2 text-xs">
            <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              <span>{t('qualityMetricsTitle')}</span>
              <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                validation.quality_grade === 'good'
                  ? 'bg-emerald-100 text-emerald-800'
                  : validation.quality_grade === 'warning'
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-rose-100 text-rose-800'
              }`}>
                {validation.quality_grade.toUpperCase()}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <span className="text-slate-500">{t('sharpnessLabel')}:</span>
                <span className="font-bold text-slate-800">{validation.metrics.sharpness_score}</span>
              </div>
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <span className="text-slate-500">{t('brightnessLabel')}:</span>
                <span className="font-bold text-slate-800">{validation.metrics.brightness_score}</span>
              </div>
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <span className="text-slate-500">{t('coverageLabel')}:</span>
                <span className="font-bold text-slate-800">
                  {Math.round((validation.metrics.retinal_coverage || 0) * 100)}%
                </span>
              </div>
              <div className="p-2 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <span className="text-slate-500">{t('resolutionLabel')}:</span>
                <span className="font-bold text-slate-800">{validation.metrics.resolution}</span>
              </div>
            </div>
          </div>
        )}

        {/* Quality Checklist (Clinical Verification) */}
        <div className="space-y-1.5 pt-1 text-xs">
          <p className="text-[11px] font-bold text-slate-500 uppercase">{t('qualityCheck')}</p>
          <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={quality.illumination}
              onChange={(e) => setQuality({ ...quality, illumination: e.target.checked })}
              className={`rounded border-slate-300 ${isOD ? 'text-brand-600 focus:ring-brand-500' : 'text-teal-600 focus:ring-teal-500'} w-3.5 h-3.5`}
            />
            <span>{t('checkIllumination')}</span>
          </label>
          <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={quality.focus}
              onChange={(e) => setQuality({ ...quality, focus: e.target.checked })}
              className={`rounded border-slate-300 ${isOD ? 'text-brand-600 focus:ring-brand-500' : 'text-teal-600 focus:ring-teal-500'} w-3.5 h-3.5`}
            />
            <span>{t('checkFocus')}</span>
          </label>
          <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={quality.noArtifacts}
              onChange={(e) => setQuality({ ...quality, noArtifacts: e.target.checked })}
              className={`rounded border-slate-300 ${isOD ? 'text-brand-600 focus:ring-brand-500' : 'text-teal-600 focus:ring-teal-500'} w-3.5 h-3.5`}
            />
            <span>{t('checkArtifacts')}</span>
          </label>
        </div>
      </div>
    );
  };

  const getProceedButtonLabel = () => {
    if (isODReady && isOSReady) return t('btnProceedBothEyes');
    if (isODReady && !isOSReady) return t('btnProceedODEye');
    if (!isODReady && isOSReady) return t('btnProceedOSEye');
    return t('btnProceedToAi');
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Demo Data Disclaimer */}
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS</span>
      </div>

      {/* Wizard Step Tracker */}
      <div className="bg-white rounded-3xl p-4 sm:p-6 border border-slate-200 shadow-card">
        <div className="grid grid-cols-3 gap-2 text-center text-xs font-bold">
          <Link
            to="/screenings/new"
            className="p-3 rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>1. {patient.name.split(' ')[0]}</span>
          </Link>

          <div className="p-3 rounded-2xl bg-brand-50 text-brand-700 border border-brand-200 flex items-center justify-center gap-2">
            <span className="w-5 h-5 rounded-full bg-brand-600 text-white flex items-center justify-center text-[10px]">
              2
            </span>
            <span>{t('stepUploadImages')}</span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 text-slate-400 border border-slate-200 flex items-center justify-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center text-[10px]">
              3
            </span>
            <span>{t('stepRunAi')}</span>
          </div>
        </div>
      </div>

      {/* Header with Quick Sample Switcher */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-extrabold text-slate-900">{t('uploadTitle')}</h1>
            <p className="text-xs text-slate-500">{t('uploadSubtitle')}</p>
          </div>

          {/* Quick Demo Sample Loader */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleLoadSample}
              className="px-3.5 py-2 rounded-xl border border-brand-200 bg-brand-50 hover:bg-brand-100 text-xs font-bold text-brand-700 transition flex items-center gap-2 shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5 text-brand-600" />
              <span>{t('btnUseSampleFundus')}</span>
            </button>
          </div>
        </div>

        {/* Spoken Voice Guidance Control */}
        <VoiceGuidanceControl stepKey="step2" />

        {/* Dual Eye Upload Grid (OD & OS) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {renderEyeUploadCard('OD', imageOD, fileOD, odStatus, odValidation, odQuality, setOdQuality)}
          {renderEyeUploadCard('OS', imageOS, fileOS, osStatus, osValidation, osQuality, setOsQuality)}
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between gap-4">
        <Link
          to="/screenings/new"
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-bold text-slate-700 transition shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Setup</span>
        </Link>

        <div className="flex items-center gap-3">
          {!canProceed && (
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">
              Upload at least one valid retinal scan to proceed
            </span>
          )}

          <button
            type="button"
            onClick={handleRunAi}
            disabled={!canProceed}
            className={`inline-flex items-center gap-2 px-6 py-3 rounded-2xl font-bold text-xs shadow-glow transition transform ${
              canProceed
                ? 'bg-brand-600 hover:bg-brand-700 text-white hover:-translate-y-0.5 cursor-pointer'
                : 'bg-slate-300 text-slate-500 cursor-not-allowed shadow-none'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>{getProceedButtonLabel()}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
