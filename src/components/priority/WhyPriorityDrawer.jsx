import React from 'react';
import {
  X,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  FileCheck,
  TrendingUp,
  Eye,
  Activity,
  Calendar,
  Clock,
  ExternalLink,
  ChevronRight,
  Info,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const WhyPriorityDrawer = ({ item, isOpen, onClose, onViewCase }) => {
  if (!isOpen || !item) return null;

  const {
    screening_id,
    patient_id,
    patient_name,
    dr_result,
    predicted_class,
    confidence_percentage,
    confidence_status,
    priority_level,
    priority_label,
    priority_score,
    score_label = 'Decision-support priority score',
    primary_reason,
    detailed_reasons = [],
    missing_factors = [],
    evidence_checklist = {},
    longitudinal_change_status,
    longitudinal_summary,
    previous_dr_result,
    previous_screening_date,
    recommended_action,
    algorithm_version = 'RCP-1.0',
    calculated_at,
    is_doctor_verified,
    doctor_reviewed_result,
    disclaimer = 'Priority is an AI-assisted triage recommendation and does not replace clinical judgment.',
  } = item;

  // Header styling based on priority level
  const getHeaderTheme = () => {
    switch (priority_level) {
      case 'P1':
        return {
          bg: 'bg-rose-500 text-white',
          badgeBg: 'bg-rose-900/30 text-rose-100 border border-rose-300/40',
          icon: AlertCircle,
          cardBorder: 'border-rose-200',
        };
      case 'P2':
        return {
          bg: 'bg-amber-500 text-white',
          badgeBg: 'bg-amber-900/30 text-amber-100 border border-amber-300/40',
          icon: AlertTriangle,
          cardBorder: 'border-amber-200',
        };
      case 'P3':
        return {
          bg: 'bg-emerald-600 text-white',
          badgeBg: 'bg-emerald-900/30 text-emerald-100 border border-emerald-300/40',
          icon: CheckCircle2,
          cardBorder: 'border-emerald-200',
        };
      case 'VERIFICATION_REQUIRED':
        return {
          bg: 'bg-amber-600 text-white',
          badgeBg: 'bg-amber-900/30 text-amber-100 border border-amber-300/40',
          icon: ShieldAlert,
          cardBorder: 'border-amber-300',
        };
      case 'RECAPTURE_REQUIRED':
        return {
          bg: 'bg-rose-600 text-white',
          badgeBg: 'bg-rose-900/30 text-rose-100 border border-rose-300/40',
          icon: AlertCircle,
          cardBorder: 'border-rose-300',
        };
      default:
        return {
          bg: 'bg-slate-800 text-white',
          badgeBg: 'bg-slate-700 text-slate-200',
          icon: Info,
          cardBorder: 'border-slate-200',
        };
    }
  };

  const theme = getHeaderTheme();
  const Icon = theme.icon;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 animate-fadeIn">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200/90 w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className={`${theme.bg} p-5 flex items-center justify-between shadow-sm shrink-0`}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-white/20 flex items-center justify-center text-white backdrop-blur-sm">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full ${theme.badgeBg}`}>
                  {priority_label}
                </span>
                <span className="text-[11px] text-white/80 font-mono">
                  {score_label}: <strong>{priority_score.toFixed(1)}</strong>
                </span>
              </div>
              <h2 className="text-lg font-black tracking-tight text-white mt-0.5">
                WHY {priority_label.toUpperCase()}?
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-white/80 hover:text-white hover:bg-white/10 transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Content */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-5 text-slate-800 text-xs">
          {/* Patient Quick Context Bar */}
          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-200/80">
            <div>
              <p className="font-extrabold text-slate-900 text-sm">{patient_name}</p>
              <p className="text-[11px] text-slate-500 font-mono">
                {patient_id} • Screening ID: {screening_id}
              </p>
            </div>
            {is_doctor_verified && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                Doctor Verified: {doctor_reviewed_result || 'Accepted'}
              </span>
            )}
          </div>

          {/* Primary Reason Callout Banner */}
          <div className="p-4 rounded-2xl bg-slate-900 text-white space-y-1.5 shadow-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-brand-300">
              PRIMARY TRIAGE EVIDENCE
            </p>
            <p className="text-sm font-semibold text-slate-100 leading-relaxed">
              "{primary_reason}"
            </p>
          </div>

          {/* Structured Evidence Checklist */}
          <div className="space-y-2.5">
            <h3 className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <FileCheck className="w-3.5 h-3.5 text-brand-600" />
              <span>Evidence Checklist</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 bg-slate-50 p-3.5 rounded-2xl border border-slate-200/80">
              {/* Current DR */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Current DR Classification</p>
                  <p className="font-extrabold text-slate-800 text-xs">{evidence_checklist.current_dr || dr_result}</p>
                </div>
              </div>

              {/* AI Confidence */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                {confidence_status === 'LOW' ? (
                  <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                )}
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">AI Model Confidence</p>
                  <p className="font-extrabold text-slate-800 text-xs">{evidence_checklist.ai_confidence || confidence_percentage}</p>
                </div>
              </div>

              {/* Previous DR */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                <Clock className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Previous Classification</p>
                  <p className="font-extrabold text-slate-800 text-xs">{evidence_checklist.previous_dr || 'Baseline visit'}</p>
                </div>
              </div>

              {/* Longitudinal Change */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                {longitudinal_change_status === 'WORSENED' ? (
                  <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                )}
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Longitudinal Trajectory</p>
                  <p className={`font-extrabold text-xs ${longitudinal_change_status === 'WORSENED' ? 'text-rose-700' : 'text-slate-800'}`}>
                    {longitudinal_summary || evidence_checklist.longitudinal_detail || 'No change'}
                  </p>
                </div>
              </div>

              {/* Image Quality Gate */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Image Quality Gate</p>
                  <p className="font-extrabold text-slate-800 text-xs">{evidence_checklist.image_quality || 'Cleared'}</p>
                </div>
              </div>

              {/* Visual Acuity */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                <Eye className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Visual Acuity</p>
                  <p className="font-extrabold text-slate-800 text-xs">{evidence_checklist.visual_acuity || 'Not recorded'}</p>
                </div>
              </div>

              {/* Diabetes Duration */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                <Activity className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Diabetes Duration</p>
                  <p className="font-extrabold text-slate-800 text-xs">{evidence_checklist.diabetes_duration || 'Not available'}</p>
                </div>
              </div>

              {/* Last HbA1c */}
              <div className="flex items-start gap-2 p-2 rounded-xl bg-white border border-slate-100">
                <Activity className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">HbA1c Level</p>
                  <p className="font-extrabold text-slate-800 text-xs">{evidence_checklist.last_hba1c || 'Not available'}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Machine-Readable Explanatory Factors */}
          {detailed_reasons && detailed_reasons.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500">
                Decision Factors
              </h3>
              <ul className="space-y-1.5 bg-slate-50 p-3 rounded-2xl border border-slate-200/80">
                {detailed_reasons.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-[11px] text-slate-700 leading-snug">
                    <span className="text-brand-500 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Factors Note if any */}
          {missing_factors && missing_factors.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-100 text-slate-600 text-[11px] space-y-1 border border-slate-200">
              <p className="font-bold text-slate-700">Excluded / Unavailable Factors:</p>
              <p className="text-slate-500">
                The following factors were unrecorded and safely excluded from calculation without artificial imputation:{' '}
                <strong>{missing_factors.join(', ')}</strong>.
              </p>
            </div>
          )}

          {/* Recommended Clinical Action Box */}
          <div className="p-4 rounded-2xl bg-brand-50 border border-brand-200 text-brand-900 space-y-1">
            <p className="text-[10px] font-extrabold uppercase tracking-wider text-brand-700">
              RECOMMENDED CLINICAL ACTION
            </p>
            <p className="text-xs font-bold leading-relaxed">{recommended_action}</p>
          </div>

          {/* Audit Metadata & Disclaimer */}
          <div className="pt-2 border-t border-slate-200 space-y-2 text-[10px] text-slate-400">
            <div className="flex flex-wrap items-center justify-between gap-2 font-mono">
              <span>Engine Version: <strong>{algorithm_version}</strong></span>
              <span>Calculated: {new Date(calculated_at).toLocaleString()}</span>
            </div>
            <p className="italic text-slate-500 leading-relaxed">
              ⚠️ <strong>Disclaimer:</strong> {disclaimer}
            </p>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between gap-3 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-200/70 transition"
          >
            Close Explanation
          </button>
          <div className="flex items-center gap-2">
            <Link
              to="/doctor"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 text-white font-bold text-xs hover:bg-slate-700 transition"
            >
              <span>Doctor Review</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
            {onViewCase && (
              <button
                onClick={() => {
                  onClose();
                  onViewCase(item);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 text-white font-extrabold text-xs hover:bg-brand-700 shadow-sm transition"
              >
                <span>View Full Case</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
