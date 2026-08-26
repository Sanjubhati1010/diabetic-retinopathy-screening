import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import {
  Eye,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Activity,
  MapPin,
  Stethoscope,
  Users,
  CheckCircle2,
  Cpu,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { SAMPLE_FUNDUS_IMAGES, SAMPLE_GRADCAM_HEATMAPS } from '../data/mockData';

export const LandingPage = () => {
  const { t, language, toggleLanguage } = useLanguage();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Top Floating Navbar for Landing */}
      <header className="sticky top-0 z-50 bg-white/85 backdrop-blur-md border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center text-white shadow-glow">
                <Eye className="w-5 h-5" />
              </div>
              <div>
                <span className="font-extrabold text-base text-slate-900 tracking-tight">
                  Rural DR Screening <span className="text-brand-600">AI</span>
                </span>
                <span className="ml-1.5 text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-100 text-brand-800 border border-brand-200">
                  Clinical
                </span>
              </div>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleLanguage}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-bold text-slate-700 transition"
            >
              {language === 'en' ? 'हिन्दी में देखें' : 'View in English'}
            </button>
            <Link
              to="/login"
              className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-slate-700 hover:text-brand-700 hover:bg-brand-50 border border-slate-200 transition"
            >
              Sign In
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-glow transition"
            >
              <span>{t('btnStartScreening')}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28 bg-gradient-to-b from-emerald-50/50 via-white to-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Content */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-100 text-brand-800 border border-brand-200 text-xs font-bold">
                <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                <span>Ayushman Bharat & Tele-Ophthalmology Aligned</span>
              </div>

              <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-slate-950 tracking-tight leading-[1.15]">
                {t('heroTitle')}
              </h1>

              <p className="text-base sm:text-lg text-slate-600 max-w-2xl leading-relaxed">
                {t('heroDesc')}
              </p>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3 pt-2">
                <Link
                  to="/dashboard"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl text-sm font-bold text-white bg-brand-600 hover:bg-brand-700 shadow-glow transition transform hover:-translate-y-0.5"
                >
                  <Eye className="w-4 h-4" />
                  <span>{t('btnStartScreening')}</span>
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Link>

                <Link
                  to="/doctor"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl text-sm font-bold text-slate-800 bg-white hover:bg-slate-50 border border-slate-200 shadow-sm transition"
                >
                  <Stethoscope className="w-4 h-4 text-teal-600" />
                  <span>{t('btnDoctorPortal')}</span>
                </Link>
              </div>

              {/* Trust Indicators */}
              <div className="pt-4 flex flex-wrap items-center justify-center lg:justify-start gap-4 text-xs font-semibold text-slate-500">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Works 100% Offline in Camps</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Grad-CAM Visual Heatmaps</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>English / हिन्दी Interface</span>
                </div>
              </div>
            </div>

            {/* Right Interactive Card Preview */}
            <div className="lg:col-span-5">
              <div className="relative mx-auto max-w-md rounded-3xl p-4 bg-slate-900 text-white shadow-2xl border border-slate-700">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                    <span className="text-xs font-bold text-slate-200">Explainable AI Interface</span>
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-brand-500/20 text-brand-300 font-semibold">
                    FastAPI Ready
                  </span>
                </div>

                <div className="relative mt-3 rounded-2xl overflow-hidden bg-black aspect-square flex items-center justify-center border border-slate-800">
                  <img
                    src={SAMPLE_FUNDUS_IMAGES.sample_od}
                    alt="Sample Fundus Scan"
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute top-3 left-3 bg-black/70 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/10 text-[11px] font-bold">
                    OD • Retinal Fundus Scan
                  </div>
                  <div className="absolute bottom-3 inset-x-3 bg-slate-900/90 border border-slate-700 px-3 py-2 rounded-xl text-[11px] font-semibold text-slate-300 text-center">
                    Awaiting PyTorch (.pth) Model Connection
                  </div>
                </div>

                <div className="mt-3 p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-slate-200">Primary Health Center Rampur</p>
                    <p className="text-[11px] text-slate-400">ABHA Compatible Record</p>
                  </div>
                  <Link
                    to="/screenings/SCR-2026-0991/xai"
                    className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-bold transition flex items-center gap-1 text-[11px]"
                  >
                    <span>View XAI</span>
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Impact Stats Grid */}
      <section className="py-12 bg-white border-y border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-center">
              <h3 className="text-3xl sm:text-4xl font-extrabold text-brand-600">{t('statScreened')}</h3>
              <p className="mt-1 text-xs sm:text-sm font-semibold text-slate-600">{t('statScreenedLabel')}</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-center">
              <h3 className="text-3xl sm:text-4xl font-extrabold text-teal-600">{t('statAccuracy')}</h3>
              <p className="mt-1 text-xs sm:text-sm font-semibold text-slate-600">{t('statAccuracyLabel')}</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-center">
              <h3 className="text-3xl sm:text-4xl font-extrabold text-indigo-600">{t('statVillages')}</h3>
              <p className="mt-1 text-xs sm:text-sm font-semibold text-slate-600">{t('statVillagesLabel')}</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-center">
              <h3 className="text-3xl sm:text-4xl font-extrabold text-rose-600">{t('statPrevented')}</h3>
              <p className="mt-1 text-xs sm:text-sm font-semibold text-slate-600">{t('statPreventedLabel')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* 4-Step Rural Workflow */}
      <section className="py-16 sm:py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
              Community Health Protocol
            </span>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-slate-900">{t('workflowTitle')}</h2>
            <p className="text-sm sm:text-base text-slate-600">{t('workflowSub')}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition">
              <div className="w-12 h-12 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-lg mb-4">
                <Users className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-slate-900">{t('step1Title')}</h4>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed">{t('step1Desc')}</p>
            </div>

            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition">
              <div className="w-12 h-12 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-lg mb-4">
                <Eye className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-slate-900">{t('step2Title')}</h4>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed">{t('step2Desc')}</p>
            </div>

            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition">
              <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-lg mb-4">
                <Cpu className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-slate-900">{t('step3Title')}</h4>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed">{t('step3Desc')}</p>
            </div>

            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition">
              <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-lg mb-4">
                <Stethoscope className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-slate-900">{t('step4Title')}</h4>
              <p className="mt-2 text-xs text-slate-600 leading-relaxed">{t('step4Desc')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Bar */}
      <section className="py-16 bg-gradient-to-r from-brand-900 via-teal-900 to-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
            Ready to deploy explainable retinal screening in your health center?
          </h2>
          <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto">
            Experience the complete end-to-end interface designed specifically for rural healthcare workers and tele-ophthalmology triage.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl text-sm font-bold text-slate-950 bg-brand-400 hover:bg-brand-300 transition shadow-glow"
            >
              <Eye className="w-4 h-4" />
              <span>Launch Field Worker Dashboard</span>
            </Link>
            <Link
              to="/doctor"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl text-sm font-bold text-white bg-slate-800 hover:bg-slate-700 border border-slate-600 transition"
            >
              <Stethoscope className="w-4 h-4" />
              <span>Launch Doctor Specialist Portal</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
