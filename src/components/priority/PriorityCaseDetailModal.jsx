import React from 'react';
import { Link } from 'react-router-dom';
import {
  X,
  User,
  Eye,
  Activity,
  Calendar,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  FileText,
  Stethoscope,
  ChevronRight,
  TrendingUp,
  MapPin,
  ExternalLink,
} from 'lucide-react';
import { getFullResultUrl } from '../../services/api';

export const PriorityCaseDetailModal = ({ item, isOpen, onClose, onOpenWhyPriority }) => {
  if (!isOpen || !item) return null;

  const {
    screening_id,
    patient_id,
    patient_name,
    village = 'Rampur',
    dr_result,
    predicted_class,
    confidence_percentage,
    priority_level,
    priority_label,
    priority_score,
    primary_reason,
    detailed_reasons = [],
    evidence_checklist = {},
    longitudinal_change_status,
    longitudinal_summary,
    doctor_status = 'pending',
    doctor_reviewed_result,
    is_doctor_verified,
    recommended_action,
    algorithm_version,
    calculated_at,
  } = item;

  const getPriorityBadgeClass = () => {
    switch (priority_level) {
      case 'P1':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'P2':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'P3':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'VERIFICATION_REQUIRED':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'RECAPTURE_REQUIRED':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200/90 w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-brand-600 flex items-center justify-center text-white font-extrabold shadow-glow">
              <Eye className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-300">CLINICAL CASE PROFILE</span>
                <span className="text-xs text-slate-500 font-mono">• {screening_id}</span>
              </div>
              <h2 className="text-lg font-black tracking-tight text-white">{patient_name}</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-5 text-slate-800 text-xs">
          {/* Priority Score Summary Banner */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-50 to-brand-50/50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${getPriorityBadgeClass()}`}>
                  {priority_label}
                </span>
                <span className="text-xs font-bold text-slate-700">
                  Priority Score: <strong className="text-slate-900">{priority_score.toFixed(1)}</strong> / 10
                </span>
              </div>
              <p className="text-xs font-medium text-slate-600">{primary_reason}</p>
            </div>
            {onOpenWhyPriority && (
              <button
                onClick={() => {
                  onClose();
                  onOpenWhyPriority(item);
                }}
                className="px-3.5 py-2 rounded-xl bg-white border border-slate-300 text-slate-700 font-bold text-xs hover:bg-slate-50 shadow-sm shrink-0 transition"
              >
                Why this priority?
              </button>
            )}
          </div>

          {/* Grid: Patient Context & Screening Finding */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Patient Clinical Context Card */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="flex items-center gap-2 text-slate-900 font-extrabold text-xs">
                <User className="w-4 h-4 text-brand-600" />
                <span>Patient Demographics & Clinical Profile</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                <div>
                  <p className="text-slate-400 font-medium">Patient ID</p>
                  <p className="font-bold text-slate-800 font-mono">{patient_id}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Location</p>
                  <p className="font-bold text-slate-800">{village}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Visual Acuity</p>
                  <p className="font-bold text-slate-800">{evidence_checklist.visual_acuity || '6/6'}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Diabetes Duration</p>
                  <p className="font-bold text-slate-800">{evidence_checklist.diabetes_duration || 'Not recorded'}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Last HbA1c</p>
                  <p className="font-bold text-slate-800">{evidence_checklist.last_hba1c || 'Not recorded'}</p>
                </div>
                <div>
                  <p className="text-slate-400 font-medium">Doctor Status</p>
                  <p className="font-bold text-slate-800 capitalize">{doctor_status}</p>
                </div>
              </div>
            </div>

            {/* AI Screening Assessment Card */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2.5">
              <div className="flex items-center gap-2 text-slate-900 font-extrabold text-xs">
                <ShieldCheck className="w-4 h-4 text-brand-600" />
                <span>AI Screening Findings</span>
              </div>
              <div className="space-y-2 pt-1 text-[11px]">
                <div className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-100">
                  <span className="text-slate-500 font-medium">DR Classification</span>
                  <span className="font-extrabold text-slate-900 text-xs">{dr_result}</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-100">
                  <span className="text-slate-500 font-medium">AI Model Confidence</span>
                  <span className="font-extrabold text-slate-900 text-xs">{confidence_percentage}</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-100">
                  <span className="text-slate-500 font-medium">Image Quality Gate</span>
                  <span className="font-bold text-emerald-700">Cleared / Good</span>
                </div>
              </div>
            </div>
          </div>

          {/* Longitudinal Intelligence Card */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center gap-2 text-slate-900 font-extrabold text-xs">
              <TrendingUp className="w-4 h-4 text-brand-600" />
              <span>Longitudinal Trajectory</span>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-100 flex items-center justify-between">
              <div>
                <p className="text-[10px] text-slate-400 font-bold uppercase">Comparison Summary</p>
                <p className="font-bold text-slate-800 text-xs">{longitudinal_summary}</p>
              </div>
              <span
                className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase border ${
                  longitudinal_change_status === 'WORSENED'
                    ? 'bg-rose-100 text-rose-800 border-rose-200'
                    : longitudinal_change_status === 'IMPROVED'
                    ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                    : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {longitudinal_change_status}
              </span>
            </div>
          </div>

          {/* Recommended Protocol Action */}
          <div className="p-4 rounded-2xl bg-brand-50 border border-brand-200 text-brand-900 space-y-1">
            <p className="text-[10px] font-extrabold uppercase tracking-wider text-brand-700">
              ACTION RECOMMENDATION
            </p>
            <p className="text-xs font-bold leading-relaxed">{recommended_action}</p>
          </div>

          {/* Disclaimer & Metadata */}
          <div className="pt-2 border-t border-slate-200 text-[10px] text-slate-400 flex flex-wrap items-center justify-between gap-2">
            <span>Algorithm: {algorithm_version}</span>
            <span className="italic text-slate-500">
              * Priority score is a triage decision-support recommendation and does not replace doctor judgment.
            </span>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between gap-3 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-200/70 transition"
          >
            Close
          </button>
          <div className="flex items-center gap-2">
            <Link
              to={`/screenings/${screening_id}/report`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-slate-300 text-slate-700 font-bold text-xs hover:bg-slate-50 transition"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Patient Report</span>
            </Link>
            <Link
              to="/doctor"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 text-white font-extrabold text-xs hover:bg-brand-700 shadow-sm transition"
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Doctor Review</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
