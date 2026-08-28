import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { MetricCard } from '../components/common/MetricCard';
import { MOCK_ANALYTICS } from '../data/mockData';
import { DemoDisclaimer } from '../components/common/DemoDisclaimer';
import {
  BarChart3,
  TrendingUp,
  Users,
  AlertTriangle,
  Sparkles,
  MapPin,
  PieChart,
  ShieldCheck,
  Calendar,
  Activity,
} from 'lucide-react';

export const AnalyticsPage = () => {
  const { t } = useLanguage();
  const { summary, severityDistribution, villageBreakdown, ageGroupRisk, monthlyTrend } =
    MOCK_ANALYTICS;

  return (
    <div className="space-y-6">
      {/* Subtle Demo Data Disclaimer */}
      <div>
        <DemoDisclaimer text="DEMO DATA — POPULATION HEALTH & SCREENING ANALYTICS" />
      </div>

      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-indigo-100 text-indigo-700">
              <BarChart3 className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-extrabold text-slate-900">{t('analyticsTitle')}</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">{t('analyticsSub')}</p>
        </div>

        <div className="flex items-center gap-2 text-xs font-bold text-slate-600 bg-white px-3.5 py-1.5 rounded-xl border border-slate-200 shadow-sm">
          <Calendar className="w-4 h-4 text-brand-600" />
          <span>FY 2026-27 Community Health Audit</span>
        </div>
      </div>

      {/* Top 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title={t('totalScreenedMetric')}
          value={summary.totalScreened.toLocaleString()}
          subtitle="Across 142 Gram Panchayats"
          icon={Users}
          trend="+14.2% MoM"
          trendPositive={true}
          variant="indigo"
        />
        <MetricCard
          title={t('positiveRateMetric')}
          value={summary.positiveRate}
          subtitle={`${summary.positiveDrCases.toLocaleString()} DR cases identified`}
          icon={Activity}
          variant="amber"
        />
        <MetricCard
          title={t('urgentReferralMetric')}
          value={summary.urgentReferrals.toLocaleString()}
          subtitle="Severe & PDR cases linked to surgery"
          icon={AlertTriangle}
          variant="rose"
        />
        <MetricCard
          title={t('modelConcordanceMetric')}
          value={summary.doctorConcordance}
          subtitle="Ophthalmologist-AI diagnostic parity"
          icon={ShieldCheck}
          variant="emerald"
        />
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* DR Severity Distribution (6 Cols) */}
        <div className="lg:col-span-6 bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              {t('chartDrDistribution')}
            </h3>
            <span className="text-xs font-bold text-slate-400">Total: 24,850</span>
          </div>

          <div className="space-y-4 pt-2">
            {severityDistribution.map((item, idx) => (
              <div key={idx} className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800">{item.label}</span>
                  <span className="text-slate-500 font-medium">
                    {item.count.toLocaleString()} ({item.percentage}%)
                  </span>
                </div>
                <div className="w-full h-3 rounded-full bg-slate-100 overflow-hidden p-0.5 border border-slate-200">
                  <div
                    className={`h-full rounded-full ${item.color} transition-all duration-500`}
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-2 mt-4">
            <Sparkles className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              <strong>Clinical Insight:</strong> 78.2% of rural community members screened had No DR, saving secondary hospital burden. 4.6% required high-priority specialist intervention.
            </p>
          </div>
        </div>

        {/* Monthly Screening Volume & Outreach Bar Visualizer (6 Cols) */}
        <div className="lg:col-span-6 bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Monthly Screening Camp Outreach (2026)
            </h3>
            <span className="text-xs font-bold text-brand-600">Growing Outreach</span>
          </div>

          {/* SVG/CSS Bar Chart */}
          <div className="h-48 flex items-end justify-between gap-2 pt-6 pb-2 px-2">
            {monthlyTrend.map((m, idx) => {
              const heightPct = Math.round((m.count / 3500) * 100);
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1 group">
                  <span className="text-[9px] font-bold text-slate-400 opacity-0 group-hover:opacity-100 transition">
                    {m.count}
                  </span>
                  <div className="w-full bg-slate-100 rounded-t-xl overflow-hidden flex flex-col justify-end h-32 relative">
                    <div
                      className="w-full bg-gradient-to-t from-brand-600 to-teal-400 rounded-t-lg transition-all group-hover:brightness-110"
                      style={{ height: `${heightPct}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-bold text-slate-600">{m.month}</span>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="p-3 rounded-2xl bg-brand-50 border border-brand-200 text-xs">
              <p className="text-[10px] font-bold text-brand-800 uppercase">Avg Screenings / Camp</p>
              <p className="text-base font-extrabold text-brand-950 mt-0.5">78.2 Patients</p>
            </div>
            <div className="p-3 rounded-2xl bg-teal-50 border border-teal-200 text-xs">
              <p className="text-[10px] font-bold text-teal-800 uppercase">District Camps Conducted</p>
              <p className="text-base font-extrabold text-teal-950 mt-0.5">318 Camps</p>
            </div>
          </div>
        </div>
      </div>

      {/* Village Performance Table & Age Group Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Village / Gram Panchayat Breakdown (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              {t('chartCampPerformance')}
            </h3>
            <span className="text-xs font-bold text-slate-400">By Sector</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-3">Gram Panchayat</th>
                  <th className="py-3 px-3 text-right">Screened</th>
                  <th className="py-3 px-3 text-right">DR Positive</th>
                  <th className="py-3 px-3 text-right">Urgent Referrals</th>
                  <th className="py-3 px-3 text-right">Prevalence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {villageBreakdown.map((v, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-3 font-bold text-slate-900 flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-brand-600 shrink-0" />
                      <span>{v.village}</span>
                    </td>
                    <td className="py-3 px-3 text-right">{v.screened.toLocaleString()}</td>
                    <td className="py-3 px-3 text-right font-bold text-amber-700">
                      {v.positive.toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right font-bold text-rose-700">{v.urgent}</td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-800 font-bold text-[11px]">
                        {v.rate}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Age Group Risk & AI Concordance Matrix (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-100">
              {t('chartAgePrevalence')}
            </h3>

            <div className="space-y-3">
              {ageGroupRisk.map((ag, idx) => (
                <div key={idx} className="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{ag.group}</span>
                    <span className="font-extrabold text-brand-700">{ag.rate} DR Rate</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>Screened: {ag.total.toLocaleString()}</span>
                    <span>Positive: {ag.drPositive.toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
