import React from 'react';
import {
  Search,
  ArrowUpDown,
  Filter,
  Eye,
  HelpCircle,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ChevronRight,
  User,
  Activity,
  Calendar,
} from 'lucide-react';

export const PriorityQueueTable = ({
  queue = [],
  loading = false,
  filterLevel = 'all',
  onFilterChange,
  sortBy = 'priority',
  onSortChange,
  searchQuery = '',
  onSearchChange,
  onOpenWhyPriority,
  onViewCase,
}) => {
  const filterTabs = [
    { key: 'all', label: 'All Cases' },
    { key: 'P1', label: 'P1 Urgent', badgeClass: 'bg-rose-100 text-rose-800' },
    { key: 'P2', label: 'P2 Priority', badgeClass: 'bg-amber-100 text-amber-800' },
    { key: 'P3', label: 'P3 Routine', badgeClass: 'bg-emerald-100 text-emerald-800' },
    { key: 'VERIFICATION_REQUIRED', label: 'Verification Required', badgeClass: 'bg-amber-100 text-amber-800' },
    { key: 'RECAPTURE_REQUIRED', label: 'Re-capture Required', badgeClass: 'bg-rose-100 text-rose-800' },
  ];

  const getPriorityBadge = (level, label) => {
    switch (level) {
      case 'P1':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-black bg-rose-100 text-rose-800 border border-rose-300">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse" />
            {label}
          </span>
        );
      case 'P2':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-extrabold bg-amber-100 text-amber-800 border border-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
            {label}
          </span>
        );
      case 'P3':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
            {label}
          </span>
        );
      case 'VERIFICATION_REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-400">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
            {label}
          </span>
        );
      case 'RECAPTURE_REQUIRED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-900 border border-rose-400">
            <AlertCircle className="w-3.5 h-3.5 text-rose-700" />
            {label}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-800">
            {label}
          </span>
        );
    }
  };

  const getSeverityBadge = (drResult, predictedClass) => {
    switch (predictedClass) {
      case 0:
        return <span className="px-2 py-0.5 rounded-lg bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">No DR</span>;
      case 1:
        return <span className="px-2 py-0.5 rounded-lg bg-blue-50 text-blue-700 font-bold border border-blue-200">Mild NPDR</span>;
      case 2:
        return <span className="px-2 py-0.5 rounded-lg bg-amber-50 text-amber-800 font-bold border border-amber-200">Moderate NPDR</span>;
      case 3:
        return <span className="px-2 py-0.5 rounded-lg bg-orange-50 text-orange-800 font-bold border border-orange-200">Severe NPDR</span>;
      case 4:
        return <span className="px-2 py-0.5 rounded-lg bg-rose-50 text-rose-800 font-bold border border-rose-200">Proliferative DR</span>;
      default:
        return <span className="px-2 py-0.5 rounded-lg bg-slate-100 text-slate-700 font-bold">{drResult || 'Assessed'}</span>;
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 shadow-card overflow-hidden space-y-4">
      {/* Table Controls Bar */}
      <div className="p-4 sm:p-5 border-b border-slate-100 space-y-3.5">
        {/* Search & Sort Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search by patient name, ID, village, or DR result..."
              className="w-full pl-9 pr-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition"
            />
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-bold text-slate-500 flex items-center gap-1">
              <ArrowUpDown className="w-3.5 h-3.5" />
              <span>Sort by:</span>
            </span>
            <select
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value)}
              className="text-xs font-bold text-slate-800 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              <option value="priority">Priority (Highest first)</option>
              <option value="severity">DR Severity</option>
              <option value="confidence">AI Confidence</option>
              <option value="date">Latest Screening</option>
            </select>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {filterTabs.map((tab) => {
            const active = filterLevel === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => onFilterChange(tab.key)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                  active
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200/70'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Priority Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50/80 text-[11px] font-extrabold uppercase tracking-wider text-slate-400 border-b border-slate-100">
              <th className="py-3 px-4 sm:px-6">Patient</th>
              <th className="py-3 px-4">DR Result</th>
              <th className="py-3 px-4">AI Confidence</th>
              <th className="py-3 px-4">Priority Level</th>
              <th className="py-3 px-4">Primary Reason</th>
              <th className="py-3 px-4 sm:px-6 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {loading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400 text-xs">
                  Calculating real-time priority scores from clinical evidence...
                </td>
              </tr>
            ) : queue.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400 text-xs">
                  No screened patients matching the selected filter criteria.
                </td>
              </tr>
            ) : (
              queue.map((item) => (
                <tr
                  key={item.screening_id}
                  className="hover:bg-slate-50/80 transition group"
                >
                  {/* PATIENT */}
                  <td className="py-3.5 px-4 sm:px-6">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-xl bg-brand-50 text-brand-700 font-extrabold text-xs flex items-center justify-center shrink-0 border border-brand-100">
                        {item.patient_name ? item.patient_name.charAt(0) : 'P'}
                      </div>
                      <div className="min-w-0">
                        <p className="font-extrabold text-slate-900 truncate text-xs sm:text-sm">
                          {item.patient_name}
                        </p>
                        <p className="text-[11px] text-slate-400 font-mono">
                          {item.patient_id} • {item.village || 'Rampur'}
                        </p>
                      </div>
                    </div>
                  </td>

                  {/* DR RESULT */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {getSeverityBadge(item.dr_result, item.predicted_class)}
                  </td>

                  {/* AI CONFIDENCE */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {item.is_low_confidence ? (
                      <span className="inline-flex items-center gap-1 font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-lg border border-amber-200">
                        <AlertTriangle className="w-3 h-3" />
                        {item.confidence_percentage} (Low)
                      </span>
                    ) : (
                      <span className="font-extrabold text-slate-800">
                        {item.confidence_percentage}
                      </span>
                    )}
                  </td>

                  {/* PRIORITY */}
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {getPriorityBadge(item.priority_level, item.priority_label)}
                  </td>

                  {/* REASON */}
                  <td className="py-3.5 px-4 max-w-xs">
                    <p className="text-xs font-semibold text-slate-800 line-clamp-2 leading-snug">
                      {item.primary_reason}
                    </p>
                  </td>

                  {/* ACTIONS */}
                  <td className="py-3.5 px-4 sm:px-6 text-right whitespace-nowrap">
                    <div className="inline-flex items-center gap-2">
                      <button
                        onClick={() => onOpenWhyPriority(item)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-[11px] transition"
                        title="Explain Priority Calculation"
                      >
                        <HelpCircle className="w-3.5 h-3.5 text-brand-600" />
                        <span>Why this priority?</span>
                      </button>

                      <button
                        onClick={() => onViewCase(item)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-900 text-white hover:bg-brand-600 font-extrabold text-[11px] shadow-sm transition"
                      >
                        <span>View Case</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
