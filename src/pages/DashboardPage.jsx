import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { MetricCard } from '../components/common/MetricCard';
import { SeverityBadge, UrgencyBadge, DoctorReviewStatusBadge } from '../components/common/SeverityBadge';
import { AlertBanner } from '../components/common/ErrorAlert';
import {
  PlusCircle,
  UserPlus,
  Users,
  Eye,
  Calendar,
  AlertTriangle,
  FileCheck,
  Clock,
  Sparkles,
  WifiOff,
  ChevronRight,
  ArrowUpRight,
  MapPin,
} from 'lucide-react';
import { MOCK_UPCOMING_CAMPS } from '../data/mockData';

export const DashboardPage = () => {
  const { t, language } = useLanguage();
  const { patients, screenings, offlineSyncCount, isOnline, ruralMode, networkState } = useApp();
  const navigate = useNavigate();

  const todayScreenings = screenings.slice(0, 4);
  const urgentCount = screenings.filter((s) => s.referralUrgency === 'urgent').length;
  const pendingCount = screenings.filter((s) => s.doctorStatus === 'pending').length;
  const recaptureList = screenings.filter(
    (s) => s.doctorStatus === 'recapture_requested' || s.reviewStatus === 'IMAGE RE-CAPTURE REQUESTED'
  );
  const reportsReadyCount = screenings.filter(
    (s) => s.doctorStatus === 'verified' || s.reviewStatus === 'AI RESULT ACCEPTED' || s.reviewStatus === 'DOCTOR REVIEWED / MODIFIED'
  ).length;

  return (
    <div className="space-y-6">
      {/* Demo Data Disclaimer */}
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS</span>
      </div>

      {/* Re-capture Required High Visibility Banner */}
      {recaptureList.length > 0 && (
        <div className="p-5 sm:p-6 rounded-3xl bg-rose-50 border-2 border-rose-400 shadow-md space-y-3 animate-in fade-in duration-200">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-2xl bg-rose-600 text-white shrink-0 mt-0.5">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-extrabold text-rose-950 uppercase tracking-tight">
                    {t('dashRecaptureRequired')} ({recaptureList.length})
                  </h3>
                  <span className="px-2.5 py-0.5 rounded-full bg-rose-200 text-rose-900 text-xs font-bold">
                    Action Required
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-rose-900 font-medium">
                  {t('recaptureGuidancePrompt') || 'Doctor has requested a clearer fundus image. Please capture and upload a new image.'}
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {recaptureList.map((rec) => (
              <div
                key={rec.id}
                className="p-4 rounded-2xl bg-white border border-rose-300 shadow-sm flex items-center justify-between gap-3"
              >
                <div>
                  <p className="font-extrabold text-sm text-slate-900">{rec.patientName}</p>
                  <p className="text-xs text-rose-700 font-bold">
                    {rec.id} • Reason: {rec.doctorRemarks || 'Quality insufficient'}
                  </p>
                  <p className="text-[11px] text-slate-400 font-medium">
                    Previous AI: {rec.className || 'Moderate'} (Historical)
                  </p>
                </div>
                <Link
                  to="/screenings/new"
                  className="px-3.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shrink-0 shadow-sm transition"
                >
                  {t('btnRecaptureNow') || 'Retake Scan'}
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Offline Alert if connectivity is down */}
      {(!isOnline || networkState.status === 'offline') && (
        <AlertBanner
          type="warning"
          title="Rural Offline Mode Active"
          message={`Network connectivity is unavailable. ${offlineSyncCount} screenings are safely stored locally on this tablet and will automatically sync once connection is restored.`}
        />
      )}

      {/* Header Banner */}
      <div className="rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-brand-900 via-teal-900 to-slate-900 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 border border-brand-400/30 text-xs font-bold">
              <MapPin className="w-3.5 h-3.5 text-brand-400" />
              <span>Primary Health Center — Rampur Sector 4</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              {t('dashTitle')}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
              Conducting community Diabetic Retinopathy screening with real-time Grad-CAM explainability and tele-ophthalmology triage.
            </p>
          </div>

          {/* Direct CTA Buttons */}
          <div className="flex flex-wrap gap-3">
            <Link
              to="/screenings/new"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-2xl bg-brand-400 text-slate-950 font-extrabold text-sm hover:bg-brand-300 shadow-glow transition transform hover:-translate-y-0.5"
            >
              <PlusCircle className="w-5 h-5" />
              <span>{ruralMode ? (t('btnStartWizard') || 'Start Guided Screening') : t('btnQuickScreening')}</span>
            </Link>
            <Link
              to="/patients/register"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs border border-white/20 transition"
            >
              <UserPlus className="w-4 h-4" />
              <span>{t('btnRegisterPatient')}</span>
            </Link>
          </div>
        </div>

        {/* Decorative background circle */}
        <div className="absolute -right-16 -bottom-16 w-64 h-64 rounded-full bg-brand-500/10 blur-2xl pointer-events-none" />
      </div>

      {/* 5 Metric Cards in Rural Mode / 4 in Standard */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title={t('dashTodayScreenings') || "Today's Screenings"}
          value="18"
          subtitle="Target for today's camp: 30"
          icon={Eye}
          trend="+4 vs yesterday"
          trendPositive={true}
          variant="emerald"
        />
        <MetricCard
          title={t('dashPendingReviews') || "Pending Doctor Reviews"}
          value={pendingCount}
          subtitle="Awaiting District Hospital review"
          icon={Clock}
          variant="amber"
        />
        <MetricCard
          title={t('dashRecaptureRequired') || "Re-capture Required"}
          value={recaptureList.length}
          subtitle="Doctor requested new scan"
          icon={AlertTriangle}
          variant="rose"
        />
        <MetricCard
          title={t('dashReportsReady') || "Reports Ready"}
          value={reportsReadyCount}
          subtitle="Bilingual clinical reports"
          icon={FileCheck}
          variant="brand"
        />
        <MetricCard
          title={t('dashNetStatus') || "Network Status"}
          value={networkState.isOnline ? 'Online' : 'Offline'}
          subtitle={`${offlineSyncCount} offline records`}
          icon={networkState.isOnline ? Eye : WifiOff}
          variant="teal"
        />
      </div>

      {/* Main Grid: Recent Screenings & Upcoming Camps */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Screenings Table (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-3xl p-6 border border-slate-200/80 shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-extrabold text-slate-900">{t('recentScreenings')}</h2>
              <p className="text-xs text-slate-500">Latest fundus scans and automated DR classifications</p>
            </div>
            <Link
              to="/history"
              className="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1"
            >
              <span>{t('viewAll')}</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-y border-slate-100">
                <tr>
                  <th className="py-3 px-3">Patient</th>
                  <th className="py-3 px-3">DR Grade</th>
                  <th className="py-3 px-3">Urgency</th>
                  <th className="py-3 px-3">Doctor Status</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {screenings.slice(0, 5).map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3.5 px-3">
                      <div className="font-bold text-slate-900">{s.patientName}</div>
                      <div className="text-[11px] text-slate-400">
                        {s.village} • {s.screeningDate.split(' ')[0]}
                      </div>
                    </td>
                    <td className="py-3.5 px-3">
                      <SeverityBadge severity={s.overallSeverity} size="sm" />
                    </td>
                    <td className="py-3.5 px-3">
                      <UrgencyBadge urgency={s.referralUrgency} />
                    </td>
                    <td className="py-3.5 px-3">
                      <DoctorReviewStatusBadge
                        status={s.reviewStatus || (s.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : s.doctorStatus === 'recapture_requested' ? 'IMAGE RE-CAPTURE REQUESTED' : 'PENDING DOCTOR REVIEW')}
                        size="sm"
                      />
                    </td>
                    <td className="py-3.5 px-3 text-right space-x-1.5">
                      <Link
                        to={`/screenings/${s.id}/xai`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold text-[11px] transition"
                      >
                        <Sparkles className="w-3 h-3" />
                        <span>Grad-CAM</span>
                      </Link>
                      <Link
                        to={`/screenings/${s.id}/result`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] transition"
                      >
                        <span>Result</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Upcoming Screening Camps (4 Cols) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-extrabold text-slate-900">{t('upcomingCamps')}</h3>
              <Calendar className="w-4 h-4 text-brand-600" />
            </div>

            <div className="space-y-3">
              {MOCK_UPCOMING_CAMPS.map((camp) => (
                <div
                  key={camp.id}
                  className="p-4 rounded-2xl border border-slate-200/80 bg-slate-50 hover:bg-slate-100/80 transition space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-xs font-bold text-slate-900 leading-snug">{camp.name}</h4>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-brand-100 text-brand-800 shrink-0">
                      {camp.date.split('-').slice(1).join('/')}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-400" />
                    <span>{camp.venue}</span>
                  </p>
                  <div className="flex items-center justify-between text-[11px] text-slate-600 pt-1 border-t border-slate-200/60 font-medium">
                    <span>
                      Registered: <strong>{camp.registeredCount}</strong> / {camp.targetScreenings}
                    </span>
                    <span className="text-brand-600 font-bold">{camp.status}</span>
                  </div>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={() => navigate('/patients/register')}
              className="w-full py-2.5 rounded-xl border border-dashed border-brand-300 bg-brand-50/50 hover:bg-brand-100 text-xs font-bold text-brand-700 transition"
            >
              + Register Patients for Next Camp
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
