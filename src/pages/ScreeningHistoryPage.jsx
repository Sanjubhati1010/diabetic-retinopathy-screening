import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { SeverityBadge, UrgencyBadge } from '../components/common/SeverityBadge';
import { EmptyState } from '../components/common/EmptyState';
import {
  History,
  Search,
  Filter,
  Download,
  Eye,
  FileText,
  Sparkles,
  CheckCircle2,
  Clock,
  MapPin,
  Calendar,
  AlertTriangle,
} from 'lucide-react';

export const ScreeningHistoryPage = () => {
  const { t } = useLanguage();
  const { screenings } = useApp();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [copiedNotification, setCopiedNotification] = useState(false);

  const filteredScreenings = screenings.filter((s) => {
    const matchesSearch =
      s.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.village.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity = severityFilter === 'all' || s.overallSeverity === severityFilter;
    const matchesStatus = statusFilter === 'all' || s.doctorStatus === statusFilter;

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const handleExportCsv = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      ['ScreeningID,PatientName,Age,Village,Date,Severity,Confidence,DoctorStatus']
        .concat(
          filteredScreenings.map(
            (s) =>
              `${s.id},${s.patientName},${s.age},${s.village},${s.screeningDate},${s.overallSeverity},${s.confidence || 'Pending'},${s.doctorStatus}`
          )
        )
        .join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `DR_Screening_History_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setCopiedNotification(true);
    setTimeout(() => setCopiedNotification(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Demo Data Disclaimer */}
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">{t('historyTitle')}</h1>
          <p className="text-xs text-slate-500">{t('historySubtitle')}</p>
        </div>

        <button
          type="button"
          onClick={handleExportCsv}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold shadow-sm transition"
        >
          <Download className="w-4 h-4 text-slate-500" />
          <span>{copiedNotification ? 'Exporting CSV...' : t('btnExportCsv')}</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-slate-200 shadow-card space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          <div className="sm:col-span-6 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Patient Name, ID, or Village..."
              className="w-full pl-9 pr-4 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
            />
          </div>

          <div className="sm:col-span-3">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full py-2.5 px-3 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white font-medium text-slate-700"
            >
              <option value="all">{t('filterSeverity')}</option>
              <option value="dr0">DR 0 (No DR)</option>
              <option value="dr1">DR 1 (Mild NPDR)</option>
              <option value="dr2">DR 2 (Moderate NPDR)</option>
              <option value="dr3">DR 3 (Severe NPDR)</option>
              <option value="dr4">DR 4 (Proliferative DR)</option>
              <option value="drUncertain">AI model not connected yet</option>
            </select>
          </div>

          <div className="sm:col-span-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-2.5 px-3 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white font-medium text-slate-700"
            >
              <option value="all">{t('filterDoctorStatus')}</option>
              <option value="verified">{t('statusSignedOff')}</option>
              <option value="pending">{t('statusPending')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* History Table */}
      {filteredScreenings.length === 0 ? (
        <EmptyState
          icon={History}
          title={t('noDataFound')}
          description="No screening sessions match your selected filters."
          actionLabel="Reset Filters"
          onAction={() => {
            setSearchQuery('');
            setSeverityFilter('all');
            setStatusFilter('all');
          }}
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4">Screening ID & Date</th>
                  <th className="py-3.5 px-4">Patient & Village</th>
                  <th className="py-3.5 px-4">AI DR Classification</th>
                  <th className="py-3.5 px-4">Model Status</th>
                  <th className="py-3.5 px-4">Doctor Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {filteredScreenings.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50 transition">
                    <td className="py-4 px-4">
                      <div className="font-bold text-slate-900 font-mono">{s.id}</div>
                      <div className="text-[11px] text-slate-400">{s.screeningDate}</div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="font-bold text-slate-900">{s.patientName}</div>
                      <div className="text-[11px] text-slate-500">{s.village}</div>
                    </td>
                    <td className="py-4 px-4">
                      <SeverityBadge severity={s.overallSeverity} size="sm" />
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-[11px]">
                        {s.confidence ? `${s.confidence}%` : 'Model Awaiting Connection'}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                          s.doctorStatus === 'verified'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            : 'bg-amber-100 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {s.doctorStatus === 'verified' ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Signed Off</span>
                          </>
                        ) : (
                          <>
                            <Clock className="w-3 h-3 text-amber-600" />
                            <span>Pending Review</span>
                          </>
                        )}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right space-x-1.5 whitespace-nowrap">
                      <Link
                        to={`/screenings/${s.id}/xai`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold text-xs transition"
                      >
                        <Sparkles className="w-3 h-3" />
                        <span>Grad-CAM</span>
                      </Link>
                      <Link
                        to={`/screenings/${s.id}/report`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition"
                      >
                        <FileText className="w-3 h-3" />
                        <span>Report</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
