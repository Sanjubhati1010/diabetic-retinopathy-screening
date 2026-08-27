import React from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import { SeverityBadge, DoctorReviewStatusBadge } from '../common/SeverityBadge';
import { formatConfidence } from '../../services/api';
import {
  History,
  Calendar,
  Eye,
  Sparkles,
  ArrowRight,
  FileText,
  Clock,
  ChevronRight,
  CheckCircle2,
} from 'lucide-react';

export const PatientScreeningHistoryTimeline = ({
  patientId,
  currentScreeningId,
  onCompareWith,
  className = '',
}) => {
  const { t } = useLanguage();
  const { getPatientScreenings, getPatientById } = useApp();

  const screenings = getPatientScreenings(patientId);
  const patient = getPatientById(patientId);

  if (!screenings || screenings.length === 0) {
    return (
      <div className={`p-6 rounded-3xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500 ${className}`}>
        <History className="w-6 h-6 text-slate-400 mx-auto mb-2" />
        <p className="font-bold">{t('statusHistoryUnavailable') || 'History Unavailable'}</p>
        <p className="text-[11px] text-slate-400">No prior screening visits recorded for this patient.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-teal-600" />
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            {t('screeningHistoryTitle') || 'Patient Screening History'} ({screenings.length})
          </h4>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          {patient?.name || 'Patient'}
        </span>
      </div>

      <div className="space-y-2.5">
        {screenings.map((scr, idx) => {
          const isCurrent = (scr.id || scr.screening_id) === currentScreeningId;
          const isFirst = idx === 0;

          return (
            <div
              key={scr.id || scr.screening_id || idx}
              className={`p-3.5 rounded-2xl border transition-all ${
                isCurrent
                  ? 'bg-teal-50/80 border-teal-400 ring-2 ring-teal-400/20'
                  : 'bg-white border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900">
                      {scr.screeningDate || scr.date}
                    </span>
                    {isCurrent && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-teal-600 text-white uppercase">
                        Current Visit
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-slate-400 block">
                    {scr.id || scr.screening_id}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <SeverityBadge severity={scr.overallSeverity || scr.drSeverityOD || 'drUncertain'} size="sm" />
                </div>
              </div>

              <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-100 text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-mono">
                    {scr.confidence !== null && scr.confidence !== undefined
                      ? formatConfidence(scr.confidence)
                      : '85.0% Conf.'}
                  </span>
                  <DoctorReviewStatusBadge
                    status={scr.reviewStatus || (scr.doctorStatus === 'verified' ? 'AI RESULT ACCEPTED' : scr.doctorStatus === 'recapture_requested' ? 'IMAGE RE-CAPTURE REQUESTED' : 'PENDING DOCTOR REVIEW')}
                    size="sm"
                  />
                </div>

                {!isCurrent && onCompareWith && (
                  <button
                    type="button"
                    onClick={() => onCompareWith(scr.id || scr.screening_id)}
                    className="inline-flex items-center gap-1 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg transition"
                  >
                    <span>{t('compareResults') || 'Compare'}</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
