import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { SeverityBadge, UrgencyBadge, SafetyBadge, ScreeningStatusBadge } from '../components/common/SeverityBadge';
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
} from 'lucide-react';
import { SAMPLE_FUNDUS_IMAGES, SAMPLE_GRADCAM_HEATMAPS } from '../data/mockData';

export const PatientReportPage = () => {
  const { id } = useParams();
  const { t } = useLanguage();
  const { getScreeningById, screenings, getPatientById, activeScreening } = useApp();
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

  const patient = getPatientById(screening.patientId);

  const [shareSuccess, setShareSuccess] = useState(false);

  const handlePrint = () => {
    window.print();
  };

  const handleShare = () => {
    setShareSuccess(true);
    setTimeout(() => setShareSuccess(false), 2500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Controls (Hidden during print) */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => navigate(`/screenings/${screening.id}/result`)}
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

      {/* Demo Data Notice */}
      <div className="no-print flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <Shield className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS • Report template ready for PyTorch model integration via FastAPI.</span>
      </div>

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
            <p className="font-bold text-slate-900 font-mono">Report ID: {screening.id}</p>
            <p className="text-slate-500">Date: {screening.screeningDate}</p>
            <p className="text-slate-500">Center: Rampur Rural PHC</p>
          </div>
        </div>

        {/* Patient Demographics & Diabetes Profile */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-5 rounded-2xl bg-slate-50 border border-slate-200 text-xs">
          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">PATIENT NAME</span>
            <span className="font-bold text-slate-900 text-sm">{patient.name}</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">AGE / GENDER</span>
            <span className="font-bold text-slate-900 capitalize">
              {patient.age} Yrs / {patient.gender}
            </span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">ABHA HEALTH ID</span>
            <span className="font-bold text-slate-900 font-mono">
              {patient.abhaId || patient.id}
            </span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">VILLAGE / PANCHAYAT</span>
            <span className="font-bold text-slate-900">{patient.village}</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">DIABETES DURATION</span>
            <span className="font-bold text-slate-900">{patient.diabetesDuration} Years Known</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">LAST HbA1c</span>
            <span className="font-bold text-amber-700">{patient.lastHba1c}%</span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">VISUAL ACUITY</span>
            <span className="font-bold text-slate-900">
              OD: {patient.visualAcuityOD} | OS: {patient.visualAcuityOS}
            </span>
          </div>

          <div>
            <span className="text-slate-400 font-semibold block text-[11px]">CONTACT</span>
            <span className="font-bold text-slate-900">{patient.phone}</span>
          </div>
        </div>

        {/* AI Screening Classification & Grad-CAM Findings */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200">
            <h3 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">
              Explainable AI Diagnostic Assessment
            </h3>
            <div className="flex flex-wrap items-center gap-2">
              {screening.isRealPrediction || screening.confidence !== null ? (
                <div className="flex flex-wrap items-center gap-2">
                  <SafetyBadge status={screening.safetyStatus || 'READY_FOR_AI'} size="sm" />
                  <ScreeningStatusBadge status={screening.screeningStatus || 'RELIABLE AI SCREENING'} size="sm" />
                  <SeverityBadge severity={screening.overallSeverity} size="sm" />
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Confidence: {(screening.confidence <= 1 ? screening.confidence * 100 : screening.confidence).toFixed(2)}%
                  </span>
                </div>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300">
                  <Sparkles className="w-3.5 h-3.5 text-slate-400" />
                  <span>AI model not connected yet</span>
                </span>
              )}
            </div>
          </div>

          {/* Tri-Image Showcase: OD Fundus, OS Fundus, Grad-CAM Overlay */}
          <div className="grid grid-cols-3 gap-4">
            {/* OD Fundus */}
            <div className="space-y-1.5 text-center">
              <div className="w-full aspect-square rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-sm flex items-center justify-center">
                <img
                  src={screening.imageOD}
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
                  src={screening.imageOS}
                  alt="OS Fundus"
                  className="w-full h-full object-contain"
                />
              </div>
              <p className="text-[11px] font-bold text-slate-700">Left Eye (OS) Scan</p>
            </div>

            {/* GradCAM Heatmap */}
            <div className="space-y-1.5 text-center">
              <div className="relative w-full aspect-square rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 shadow-sm flex flex-col items-center justify-center">
                {screening.gradCamOD || screening.gradCamOS || screening.gradCamUrl ? (
                  <img
                    src={screening.gradCamOD || screening.gradCamOS || screening.gradCamUrl}
                    alt="Grad-CAM Heatmap"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="p-3 text-center">
                    <Sparkles className="w-6 h-6 text-brand-400 mb-1 mx-auto" />
                    <p className="text-[10px] font-bold text-slate-200 leading-snug">
                      Grad-CAM Activation
                    </p>
                    <p className="text-[9px] text-slate-400 mt-1">
                      Awaiting model connection
                    </p>
                  </div>
                )}
              </div>
              <p className="text-[11px] font-bold text-slate-600 flex items-center justify-center gap-1">
                <span>Grad-CAM Explainability</span>
              </p>
            </div>
          </div>
        </div>

        {/* Doctor Clinical Impression & Remarks Box */}
        <div className="p-6 rounded-2xl bg-teal-50/50 border border-teal-200 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-teal-950 uppercase tracking-wider flex items-center gap-2">
              <Stethoscope className="w-4 h-4 text-teal-600" />
              <span>{t('doctorRemarks')}</span>
            </h4>
            <span className="text-[11px] font-bold text-teal-800 bg-teal-100 px-2 py-0.5 rounded">
              Tele-Ophthalmologist Digital Verification
            </span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed italic">
            "{t('doctorRemarksText')}"
          </p>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-teal-200/60 text-xs">
            <div>
              <p className="font-bold text-slate-900">{t('doctorName')}</p>
              <p className="text-[11px] text-slate-500">{t('doctorHospital')}</p>
            </div>
            <div className="text-right">
              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-lg">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Digitally Signed & Validated</span>
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
            {t('patientAdvisoryText')}
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
                Dr. A. Swaminathan
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
