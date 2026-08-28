import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2, Users, RefreshCw, ShieldAlert } from 'lucide-react';

export const PriorityStatCards = ({ stats, loading, onRefresh }) => {
  const {
    total_screened = 0,
    urgent_count = 0,
    priority_count = 0,
    routine_count = 0,
    verification_required_count = 0,
    recapture_required_count = 0,
  } = stats || {};

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* TOTAL SCREENED */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-bold tracking-wider uppercase text-slate-500">TOTAL SCREENED</p>
            <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {loading ? '...' : total_screened}
            </span>
            <span className="text-xs text-slate-500 font-medium">Patients</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Database screening population</p>
        </div>

        {/* P1 — URGENT */}
        <div className="bg-gradient-to-br from-rose-50 to-white rounded-2xl p-4 border border-rose-200/80 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse" />
              <p className="text-[11px] font-extrabold tracking-wider uppercase text-rose-800">P1 — URGENT</p>
            </div>
            <div className="w-8 h-8 rounded-xl bg-rose-100 flex items-center justify-center text-rose-700">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-black text-rose-700 tracking-tight">
              {loading ? '...' : urgent_count}
            </span>
            <span className="text-xs text-rose-600 font-bold">Cases</span>
          </div>
          <p className="mt-1 text-[11px] text-rose-600 font-medium">Immediate specialist attention</p>
        </div>

        {/* P2 — PRIORITY */}
        <div className="bg-gradient-to-br from-amber-50 to-white rounded-2xl p-4 border border-amber-200/80 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <p className="text-[11px] font-extrabold tracking-wider uppercase text-amber-800">P2 — PRIORITY</p>
            </div>
            <div className="w-8 h-8 rounded-xl bg-amber-100 flex items-center justify-center text-amber-700">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-black text-amber-700 tracking-tight">
              {loading ? '...' : priority_count}
            </span>
            <span className="text-xs text-amber-600 font-bold">Cases</span>
          </div>
          <p className="mt-1 text-[11px] text-amber-600 font-medium">Moderate / secondary triage</p>
        </div>

        {/* P3 — ROUTINE */}
        <div className="bg-gradient-to-br from-emerald-50 to-white rounded-2xl p-4 border border-emerald-200/80 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <p className="text-[11px] font-extrabold tracking-wider uppercase text-emerald-800">P3 — ROUTINE</p>
            </div>
            <div className="w-8 h-8 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-700">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl sm:text-3xl font-black text-emerald-700 tracking-tight">
              {loading ? '...' : routine_count}
            </span>
            <span className="text-xs text-emerald-600 font-bold">Cases</span>
          </div>
          <p className="mt-1 text-[11px] text-emerald-600 font-medium">Standard follow-up schedule</p>
        </div>
      </div>

      {/* Auxiliary Alerts for Safety / Uncertainty */}
      {(verification_required_count > 0 || recapture_required_count > 0) && (
        <div className="flex flex-wrap items-center gap-3 pt-1">
          {verification_required_count > 0 && (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-100/80 border border-amber-300 text-amber-900 text-xs font-semibold">
              <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0" />
              <span>
                <strong>{verification_required_count}</strong> {verification_required_count === 1 ? 'case' : 'cases'} require human verification (AI uncertainty)
              </span>
            </div>
          )}
          {recapture_required_count > 0 && (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-100/80 border border-rose-300 text-rose-900 text-xs font-semibold">
              <AlertCircle className="w-4 h-4 text-rose-700 shrink-0" />
              <span>
                <strong>{recapture_required_count}</strong> {recapture_required_count === 1 ? 'case' : 'cases'} blocked by image quality safety gate (re-capture required)
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
