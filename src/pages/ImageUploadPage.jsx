import React, { useState } from 'react';
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
} from 'lucide-react';
import { SAMPLE_FUNDUS_IMAGES } from '../data/mockData';
import { ensureImageFile } from '../services/api';

export const ImageUploadPage = () => {
  const { t } = useLanguage();
  const { activeScreening, setActiveScreening, patients } = useApp();
  const navigate = useNavigate();

  const patient = patients.find((p) => p.id === activeScreening.patientId) || patients[0];

  const [imageOD, setImageOD] = useState(activeScreening.imageOD || SAMPLE_FUNDUS_IMAGES.sample_od);
  const [imageOS, setImageOS] = useState(activeScreening.imageOS || SAMPLE_FUNDUS_IMAGES.sample_os);
  const [fileOD, setFileOD] = useState(activeScreening.fileOD || null);
  const [fileOS, setFileOS] = useState(activeScreening.fileOS || null);
  const [selectedEye, setSelectedEye] = useState(activeScreening.selectedEyeForAnalysis || 'OD');

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

  const handleFileUpload = (e, eye) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      if (eye === 'OD') {
        setFileOD(file);
      } else {
        setFileOS(file);
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        const dataUrl = event.target.result;
        if (eye === 'OD') {
          setImageOD(dataUrl);
        } else {
          setImageOS(dataUrl);
        }

        // Immediately clear previous analysis results, gradcam, error, etc. for this eye
        setActiveScreening((prev) => ({
          ...prev,
          [eye === 'OD' ? 'fileOD' : 'fileOS']: file,
          [eye === 'OD' ? 'imageOD' : 'imageOS']: dataUrl,
          [eye === 'OD' ? 'rightEyeAnalysis' : 'leftEyeAnalysis']: null,
          [eye === 'OD' ? 'aiResultOD' : 'aiResultOS']: null,
          [eye === 'OD' ? 'gradCamOD' : 'gradCamOS']: null,
          [eye === 'OD' ? 'drSeverityOD' : 'drSeverityOS']: 'drUncertain',
          [eye === 'OD' ? 'odAnalysisError' : 'osAnalysisError']: null,
          aiResult: null,
          confidence: null,
          probabilities: null,
          gradCamUrl: null,
          overallSeverity: 'drUncertain',
        }));
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
    } catch (err) {
      console.warn('Could not create files from sample scan:', err);
    }
  };

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

    setActiveScreening((prev) => ({
      ...prev,
      imageOD,
      imageOS,
      fileOD: resolvedFileOD,
      fileOS: resolvedFileOS,
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
      selectedEyeForAnalysis: selectedEye,
      odQuality,
      osQuality,
      qualityChecked: true,
      patientId: patient.id,
      patientName: patient.name,
    }));
    navigate('/screenings/analysis');
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
              className="px-3 py-1.5 rounded-lg border border-brand-200 bg-brand-50 hover:bg-brand-100 text-xs font-bold text-brand-700 transition flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5 text-brand-600" />
              <span>Load Sample Test Scans</span>
            </button>
          </div>
        </div>

        {/* Dual Eye Upload Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Right Eye (OD) */}
          <div className="space-y-4 p-5 rounded-2xl border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-brand-500"></span>
                <span>{t('rightEyeOD')}</span>
              </h3>
              <span className="text-[11px] font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded border border-brand-200">
                OD Scan
              </span>
            </div>

            {/* Fundus Preview Canvas */}
            <div className="relative rounded-2xl overflow-hidden bg-slate-950 aspect-square flex items-center justify-center border border-slate-800 group shadow-inner">
              {imageOD ? (
                <>
                  <img
                    src={imageOD}
                    alt="Right Eye Fundus Scan"
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute top-2 right-2 flex items-center gap-1">
                    <label className="px-2.5 py-1 rounded-lg bg-black/70 hover:bg-black/90 text-white text-[11px] font-bold cursor-pointer transition border border-white/20">
                      <span>Change Image</span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFileUpload(e, 'OD')}
                      />
                    </label>
                  </div>
                </>
              ) : (
                <label className="flex flex-col items-center justify-center p-6 text-center cursor-pointer">
                  <Upload className="w-8 h-8 text-slate-500 mb-2" />
                  <span className="text-xs font-bold text-slate-300">{t('dragDropText')}</span>
                  <span className="text-[10px] text-slate-500 mt-1">{t('supportedFormats')}</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleFileUpload(e, 'OD')}
                  />
                </label>
              )}
            </div>

            {/* Quality Checklist */}
            <div className="space-y-1.5 pt-2 text-xs">
              <p className="text-[11px] font-bold text-slate-500 uppercase">{t('qualityCheck')}</p>
              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={odQuality.illumination}
                  onChange={(e) =>
                    setOdQuality({ ...odQuality, illumination: e.target.checked })
                  }
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-3.5 h-3.5"
                />
                <span>{t('checkIllumination')}</span>
              </label>
              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={odQuality.focus}
                  onChange={(e) => setOdQuality({ ...odQuality, focus: e.target.checked })}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-3.5 h-3.5"
                />
                <span>{t('checkFocus')}</span>
              </label>
              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={odQuality.noArtifacts}
                  onChange={(e) =>
                    setOdQuality({ ...odQuality, noArtifacts: e.target.checked })
                  }
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-3.5 h-3.5"
                />
                <span>{t('checkArtifacts')}</span>
              </label>
            </div>
          </div>

          {/* Left Eye (OS) */}
          <div className="space-y-4 p-5 rounded-2xl border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-teal-500"></span>
                <span>{t('leftEyeOS')}</span>
              </h3>
              <span className="text-[11px] font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                OS Scan
              </span>
            </div>

            {/* Fundus Preview Canvas */}
            <div className="relative rounded-2xl overflow-hidden bg-slate-950 aspect-square flex items-center justify-center border border-slate-800 group shadow-inner">
              {imageOS ? (
                <>
                  <img
                    src={imageOS}
                    alt="Left Eye Fundus Scan"
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute top-2 right-2 flex items-center gap-1">
                    <label className="px-2.5 py-1 rounded-lg bg-black/70 hover:bg-black/90 text-white text-[11px] font-bold cursor-pointer transition border border-white/20">
                      <span>Change Image</span>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFileUpload(e, 'OS')}
                      />
                    </label>
                  </div>
                </>
              ) : (
                <label className="flex flex-col items-center justify-center p-6 text-center cursor-pointer">
                  <Upload className="w-8 h-8 text-slate-500 mb-2" />
                  <span className="text-xs font-bold text-slate-300">{t('dragDropText')}</span>
                  <span className="text-[10px] text-slate-500 mt-1">{t('supportedFormats')}</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => handleFileUpload(e, 'OS')}
                  />
                </label>
              )}
            </div>

            {/* Quality Checklist */}
            <div className="space-y-1.5 pt-2 text-xs">
              <p className="text-[11px] font-bold text-slate-500 uppercase">{t('qualityCheck')}</p>
              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={osQuality.illumination}
                  onChange={(e) =>
                    setOsQuality({ ...osQuality, illumination: e.target.checked })
                  }
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5"
                />
                <span>{t('checkIllumination')}</span>
              </label>
              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={osQuality.focus}
                  onChange={(e) => setOsQuality({ ...osQuality, focus: e.target.checked })}
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5"
                />
                <span>{t('checkFocus')}</span>
              </label>
              <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={osQuality.noArtifacts}
                  onChange={(e) =>
                    setOsQuality({ ...osQuality, noArtifacts: e.target.checked })
                  }
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-3.5 h-3.5"
                />
                <span>{t('checkArtifacts')}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between">
        <Link
          to="/screenings/new"
          className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-bold text-slate-700 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Setup</span>
        </Link>

        <button
          type="button"
          onClick={handleRunAi}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-glow transition transform hover:-translate-y-0.5"
        >
          <Sparkles className="w-4 h-4" />
          <span>{t('btnProceedToAi')}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
