import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { MetricCard } from '../components/common/MetricCard';
import { SeverityBadge, UrgencyBadge, DoctorReviewStatusBadge } from '../components/common/SeverityBadge';
import { AlertBanner } from '../components/common/ErrorAlert';
import { DemoDisclaimer } from '../components/common/DemoDisclaimer';
import { WhyPriorityDrawer } from '../components/priority/WhyPriorityDrawer';
import { PriorityCaseDetailModal } from '../components/priority/PriorityCaseDetailModal';
import { getPriorityQueue, getPriorityStats } from '../services/api';
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
  ArrowRight,
  MapPin,
  Video,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  Activity,
  HelpCircle,
} from 'lucide-react';
import { MOCK_UPCOMING_CAMPS } from '../data/mockData';

export const DashboardPage = () => {
  const { t, language } = useLanguage();
  const { patients, screenings, appointments = [], offlineSyncCount, isOnline, ruralMode, networkState } = useApp();
  const navigate = useNavigate();

  const [priorityStats, setPriorityStats] = useState({
    total_screened: 0,
    urgent_count: 0,
    priority_count: 0,
    routine_count: 0,
    verification_required_count: 0,
    recapture_required_count: 0,
  });
  const [priorityQueue, setPriorityQueue] = useState([]);
  const [priorityLoading, setPriorityLoading] = useState(true);
  const [selectedWhyItem, setSelectedWhyItem] = useState(null);
  const [selectedCaseItem, setSelectedCaseItem] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function loadPriority() {
      try {
        const res = await getPriorityQueue({ sort_by: 'priority' });
        if (isMounted && res) {
          setPriorityQueue(res.queue || []);
          setPriorityStats({
            total_screened: res.total || res.queue?.length || 0,
            urgent_count: res.urgent_count || 0,
            priority_count: res.priority_count || 0,
            routine_count: res.routine_count || 0,
            verification_required_count: res.verification_required_count || 0,
            recapture_required_count: res.recapture_required_count || 0,
          });
        }
      } catch (e) {
        console.error('Error loading priority on dashboard:', e);
      } finally {
        if (isMounted) setPriorityLoading(false);
      }
    }
    loadPriority();
    return () => { isMounted = false; };
  }, [screenings]);

  const todayScreenings = screenings.slice(0, 4);
  const urgentCount = screenings.filter((s) => s.referralUrgency === 'urgent' || s.overallSeverity === 'severe' || s.overallSeverity === 'proliferative').length;
  const pendingCount = screenings.filter((s) => s.doctorStatus === 'pending').length;
  const reportsReadyCount = screenings.filter(
    (s) => s.doctorStatus === 'verified' || s.reviewStatus === 'AI RESULT ACCEPTED' || s.reviewStatus === 'DOCTOR REVIEWED / MODIFIED'
  ).length;

  return (
    <div className="space-y-6">
      {/* Subtle Compact Demo Data Notice */}
      <div className="flex items-center justify-between">
        <DemoDisclaimer text="DEMO DATA — CLINICAL DECISION SUPPORT DEMONSTRATION" />
      </div>

      {/* Offline Alert if connectivity is down */}
      {(!isOnline || networkState.status === 'offline') && (
        <AlertBanner
          type="warning"
          title="Rural Offline Mode Active"
          message={`Network connectivity is unavailable. ${offlineSyncCount} screenings are safely stored locally on this tablet and will automatically sync once connection is restored.`}
        />
      )}

      {/* Header Banner */}
      <div className="rounded-3xl p-6 sm:p-7 bg-gradient-to-r from-brand-900 via-teal-900 to-slate-900 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-400/30 text-xs font-bold">
              <MapPin className="w-3.5 h-3.5 text-brand-400" />
              <span>Primary Health Center — Rampur Sector 4</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight">
              {t('dashTitle')}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-xl leading-relaxed">
              Conducting community Diabetic Retinopathy screening with real-time Grad-CAM explainability and tele-ophthalmology triage.
            </p>
          </div>

          {/* Direct CTA Buttons */}
          <div className="flex flex-wrap gap-2.5">
            <Link
              to="/screenings/new"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-400 text-slate-950 font-extrabold text-xs sm:text-sm hover:bg-brand-300 shadow-glow transition transform hover:-translate-y-0.5"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{ruralMode ? (t('btnStartWizard') || 'Start Guided Screening') : t('btnQuickScreening')}</span>
            </Link>
            <Link
              to="/patients/register"
              className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs border border-white/20 transition"
            >
              <UserPlus className="w-4 h-4" />
              <span>{t('btnRegisterPatient')}</span>
            </Link>
          </div>
        </div>

        {/* Decorative background circle */}
        <div className="absolute -right-16 -bottom-16 w-64 h-64 rounded-full bg-brand-500/10 blur-2xl pointer-events-none" />
      </div>

      {/* Clean 4 Compact Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
          title={t('dashPendingReviews') || "Pending Review"}
          value={pendingCount}
          subtitle="Awaiting specialist review"
          icon={Clock}
          variant="amber"
        />
        <MetricCard
          title={t('dashReportsReady') || "Verified"}
          value={reportsReadyCount}
          subtitle="Accepted clinical reports"
          icon={CheckCircle2}
          variant="teal"
        />
        <MetricCard
          title={t('dashReferrals') || "Referrals"}
          value={urgentCount}
          subtitle="High risk / urgent referrals"
          icon={AlertCircle}
          variant="rose"
        />
      </div>

      {/* RURAL CARE PRIORITY ENGINE DASHBOARD SECTION */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-card space-y-5">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-100">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
              <h2 className="text-lg font-black tracking-tight text-slate-900">
                Rural Care Priority Engine
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-brand-50 text-brand-700 border border-brand-200">
                Clinical Decision Support
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Prioritizing specialist attention using explainable screening evidence.
            </p>
          </div>

          <Link
            to="/priority"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-brand-600 text-white font-extrabold text-xs shadow-sm transition"
          >
            <span>Open Full Priority Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* 4 Priority Summary Cards (Real database data) */}
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* TOTAL SCREENED */}
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/70">
            <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">TOTAL SCREENED</p>
            <p className="text-2xl sm:text-3xl font-black text-slate-900 mt-1">
              {priorityLoading ? '...' : priorityStats.total_screened}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">Screened cohort</p>
          </div>

          {/* URGENT (P1) */}
          <div className="bg-rose-50/70 rounded-2xl p-4 border border-rose-200">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse" />
              <p className="text-[10px] font-black uppercase tracking-wider text-rose-800">URGENT (P1)</p>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-rose-700 mt-1">
              {priorityLoading ? '...' : priorityStats.urgent_count}
            </p>
            <p className="text-[11px] text-rose-600 font-medium mt-0.5">Immediate specialist review</p>
          </div>

          {/* PRIORITY (P2) */}
          <div className="bg-amber-50/70 rounded-2xl p-4 border border-amber-200">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
              <p className="text-[10px] font-black uppercase tracking-wider text-amber-800">PRIORITY (P2)</p>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-amber-700 mt-1">
              {priorityLoading ? '...' : priorityStats.priority_count}
            </p>
            <p className="text-[11px] text-amber-600 font-medium mt-0.5">Secondary attention</p>
          </div>

          {/* ROUTINE (P3) */}
          <div className="bg-emerald-50/70 rounded-2xl p-4 border border-emerald-200">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
              <p className="text-[10px] font-black uppercase tracking-wider text-emerald-800">ROUTINE (P3)</p>
            </div>
            <p className="text-2xl sm:text-3xl font-black text-emerald-700 mt-1">
              {priorityLoading ? '...' : priorityStats.routine_count}
            </p>
            <p className="text-[11px] text-emerald-600 font-medium mt-0.5">Annual follow-up</p>
          </div>
        </div>

        {/* Priority Triage Queue Preview */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">
              Top Priority Specialist Queue
            </h3>
            <span className="text-[11px] text-slate-400">
              Sorted by explainable risk severity
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-y border-slate-100 text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Patient</th>
                  <th className="py-2.5 px-3">DR Result</th>
                  <th className="py-2.5 px-3">AI Confidence</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Reason</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {priorityLoading ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-slate-400 text-xs">
                      Loading prioritized patient records...
                    </td>
                  </tr>
                ) : priorityQueue.slice(0, 4).map((item) => (
                  <tr key={item.screening_id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-3">
                      <div className="font-bold text-slate-900">{item.patient_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {item.patient_id} • {item.village || 'Rampur'}
                      </div>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className="font-extrabold text-slate-900">{item.dr_result}</span>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className="font-bold text-slate-800">{item.confidence_percentage}</span>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-black border ${
                          item.priority_level === 'P1'
                            ? 'bg-rose-100 text-rose-800 border-rose-300'
                            : item.priority_level === 'P2'
                            ? 'bg-amber-100 text-amber-800 border-amber-300'
                            : item.priority_level === 'P3'
                            ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                            : 'bg-amber-100 text-amber-900 border-amber-300'
                        }`}
                      >
                        {item.priority_label}
                      </span>
                    </td>
                    <td className="py-3 px-3 max-w-xs truncate text-[11px] text-slate-700 font-medium">
                      {item.primary_reason}
                    </td>
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          onClick={() => setSelectedWhyItem(item)}
                          className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-[11px] transition"
                        >
                          Why this priority?
                        </button>
                        <button
                          onClick={() => setSelectedCaseItem(item)}
                          className="px-2.5 py-1 rounded-lg bg-slate-900 text-white hover:bg-brand-600 font-bold text-[11px] shadow-sm transition"
                        >
                          View Case
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Main Grid: Recent Screenings & Upcoming Camps */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
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
                    <td className="py-3.5 px-3 text-right whitespace-nowrap">
                      <div className="inline-flex items-center justify-end gap-1.5">
                        <Link
                          to={`/screenings/${s.id}/xai`}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold text-[11px] transition"
                        >
                          <Sparkles className="w-3 h-3" />
                          <span>Grad-CAM</span>
                        </Link>
                        <Link
                          to={`/screenings/${s.id}/result`}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] transition"
                        >
                          <span>Result</span>
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Tele-Ophthalmology & Upcoming Screening Camps (4 Cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Phase 11: Upcoming Tele-Consultations Widget */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-extrabold text-slate-900">
                  {t('teleOphthalmologyTitle') || 'Tele-Consultations'}
                </h3>
              </div>
              <Link
                to="/appointments"
                className="text-[11px] font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                <span>{t('viewAll')}</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {appointments.slice(0, 3).map((apt) => (
                <div
                  key={apt.id}
                  className="p-3.5 rounded-2xl border border-slate-200/80 bg-indigo-50/30 hover:bg-indigo-50/70 transition space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900 leading-snug">
                        {apt.patient_name || apt.patientName}
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        {apt.doctor_name || apt.doctorName}
                      </p>
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold shrink-0 ${
                        apt.status === 'CONFIRMED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : apt.status === 'PENDING'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {apt.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-600 pt-1 border-t border-indigo-100/60 font-medium">
                    <span className="font-mono">
                      📅 {apt.date} ({apt.start_time})
                    </span>
                    {apt.status === 'CONFIRMED' ? (
                      <Link
                        to={`/appointments/${apt.id}/video`}
                        className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
                      >
                        <Video className="w-3.5 h-3.5" />
                        Join Call
                      </Link>
                    ) : (
                      <Link
                        to={`/appointments/${apt.id}`}
                        className="text-xs font-semibold text-indigo-600 hover:text-indigo-700"
                      >
                        Details →
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <Link
              to="/appointments"
              className="w-full py-2.5 rounded-xl border border-indigo-200 bg-indigo-50/50 hover:bg-indigo-100 text-xs font-bold text-indigo-700 transition block text-center"
            >
              + {t('scheduleConsultation') || 'Schedule Tele-Consultation'}
            </Link>
          </div>

          {/* Phase 12: WhatsApp Report Delivery Widget */}
          <div className="bg-white rounded-3xl p-6 border border-emerald-200 shadow-card space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-extrabold text-slate-900">
                  {t('whatsappReportTitle') || 'WhatsApp Reports'}
                </h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                Verified Opt-in
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-gradient-to-r from-emerald-50/80 to-teal-50/50 border border-emerald-100 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-600 font-medium">Health Worker:</span>
                <span className="font-bold text-slate-900">Pooja Sharma (ASHA)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600 font-medium">Recipient Mobile:</span>
                <span className="font-mono font-bold text-emerald-800">+91 98765 43210</span>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-emerald-200/60">
                <span className="text-slate-600 font-medium">Doctor Verified Reports:</span>
                <span className="font-extrabold text-emerald-700">{reportsReadyCount} Ready</span>
              </div>
            </div>

            <Link
              to="/patients"
              className="w-full py-2.5 rounded-xl border border-emerald-200 bg-emerald-50/50 hover:bg-emerald-100 text-xs font-bold text-emerald-800 transition block text-center"
            >
              View Reports & WhatsApp Dispatch →
            </Link>
          </div>

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

      {/* "Why This Priority?" Explanation Drawer */}
      <WhyPriorityDrawer
        item={selectedWhyItem}
        isOpen={Boolean(selectedWhyItem)}
        onClose={() => setSelectedWhyItem(null)}
        onViewCase={(item) => setSelectedCaseItem(item)}
      />

      {/* Priority Patient Case Detail Modal */}
      <PriorityCaseDetailModal
        item={selectedCaseItem}
        isOpen={Boolean(selectedCaseItem)}
        onClose={() => setSelectedCaseItem(null)}
        onOpenWhyPriority={(item) => setSelectedWhyItem(item)}
      />
    </div>
  );
};
