import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { SeverityBadge, UrgencyBadge } from '../components/common/SeverityBadge';
import {
  User,
  Activity,
  Calendar,
  Eye,
  FileText,
  PlusCircle,
  Phone,
  MapPin,
  Clock,
  Sparkles,
  ChevronLeft,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

export const PatientProfilePage = () => {
  const { id } = useParams();
  const { t } = useLanguage();
  const { getPatientById, screenings, setActiveScreening } = useApp();
  const navigate = useNavigate();

  const patient = getPatientById(id);
  const patientScreenings = screenings.filter((s) => s.patientId === patient.id);

  const handleStartScreening = () => {
    setActiveScreening((prev) => ({
      ...prev,
      patientId: patient.id,
      patientName: patient.name,
    }));
    navigate('/screenings/upload');
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Demo Data Disclaimer */}
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <User className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS</span>
      </div>

      {/* Back button & Title */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/patients')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Back to Patient Directory</span>
        </button>

        <button
          onClick={handleStartScreening}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-glow transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>{t('btnNewScanForPatient')}</span>
        </button>
      </div>

      {/* Patient Header Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xl shrink-0">
              <User className="w-7 h-7" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">{patient.name}</h1>
                <SeverityBadge severity={patient.latestStatus} />
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                <span className="font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-700 font-semibold">
                  ABHA: {patient.abhaId || patient.id}
                </span>
                <span>•</span>
                <span className="capitalize">
                  {patient.age} Years • {patient.gender}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Phone className="w-3.5 h-3.5" />
                  {patient.phone}
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:items-end gap-1.5 text-xs">
            <span className="text-slate-400">Referral Urgency:</span>
            <UrgencyBadge urgency={patient.referralUrgency} />
          </div>
        </div>

        {/* Clinical Summary Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6">
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <p className="text-[11px] font-bold text-slate-400 uppercase">Diabetes History</p>
            <p className="text-sm font-extrabold text-slate-900 mt-1">
              {patient.diabetesDuration} Years Known
            </p>
            <p className="text-[11px] text-slate-500">
              {patient.insulinUse ? 'On Insulin Therapy' : 'Oral Medications'}
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <p className="text-[11px] font-bold text-slate-400 uppercase">Last Glycemic Index</p>
            <p className="text-sm font-extrabold text-amber-700 mt-1">HbA1c: {patient.lastHba1c}%</p>
            <p className="text-[11px] text-slate-500">High Microvascular Risk</p>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <p className="text-[11px] font-bold text-slate-400 uppercase">Visual Acuity (OD / OS)</p>
            <p className="text-sm font-extrabold text-slate-900 mt-1">
              OD: {patient.visualAcuityOD} | OS: {patient.visualAcuityOS}
            </p>
            <p className="text-[11px] text-slate-500">Snellen Chart Rating</p>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <p className="text-[11px] font-bold text-slate-400 uppercase">Community Location</p>
            <p className="text-xs font-extrabold text-slate-900 mt-1 truncate">{patient.village}</p>
            <p className="text-[11px] text-slate-500">{patient.district} District</p>
          </div>
        </div>
      </div>

      {/* Retinal Screening Timeline */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-extrabold text-slate-900">{t('screeningTimeline')}</h2>
            <p className="text-xs text-slate-500">Longitudinal fundus examinations and AI explainability records</p>
          </div>
          <span className="text-xs font-bold text-slate-400">
            {patientScreenings.length} Examination(s)
          </span>
        </div>

        {patientScreenings.length === 0 ? (
          <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-slate-500 text-xs">
            {t('noPreviousScans')}
          </div>
        ) : (
          <div className="space-y-6">
            {patientScreenings.map((screening) => (
              <div
                key={screening.id}
                className="p-5 rounded-2xl border border-slate-200 bg-slate-50/60 hover:bg-slate-50 transition space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/60">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs">
                      <Eye className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{screening.campName}</h4>
                      <p className="text-[11px] text-slate-400">
                        {screening.screeningDate} • Camera: {screening.cameraModel}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={screening.overallSeverity} />
                    <UrgencyBadge urgency={screening.referralUrgency} />
                  </div>
                </div>

                {/* Scans & GradCAM Preview */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* OD Scan */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-white border border-slate-200">
                    <div className="w-16 h-16 rounded-lg bg-black overflow-hidden shrink-0 border border-slate-800">
                      <img
                        src={screening.imageOD}
                        alt="OD Scan"
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-slate-800">OD (Right Eye)</p>
                      <p className="text-[11px] text-slate-500">
                        Severity: <SeverityBadge severity={screening.drSeverityOD} size="sm" />
                      </p>
                    </div>
                  </div>

                  {/* OS Scan */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-white border border-slate-200">
                    <div className="w-16 h-16 rounded-lg bg-black overflow-hidden shrink-0 border border-slate-800">
                      <img
                        src={screening.imageOS}
                        alt="OS Scan"
                        className="w-full h-full object-contain"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-slate-800">OS (Left Eye)</p>
                      <p className="text-[11px] text-slate-500">
                        Severity: <SeverityBadge severity={screening.drSeverityOS} size="sm" />
                      </p>
                    </div>
                  </div>
                </div>

                {/* Clinical Biomarkers */}
                {screening.biomarkers && (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] font-bold text-slate-400">Biomarkers:</span>
                    {screening.biomarkers.map((b, idx) => (
                      <span
                        key={idx}
                        className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 font-medium"
                      >
                        {b}
                      </span>
                    ))}
                  </div>
                )}

                {/* Action Links */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 text-xs">
                  <div className="text-[11px] text-slate-500">
                    Screener: <strong>{screening.screenerName}</strong>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/screenings/${screening.id}/xai`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-brand-50 hover:bg-brand-100 text-brand-700 font-bold transition"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Grad-CAM XAI</span>
                    </Link>
                    <Link
                      to={`/screenings/${screening.id}/report`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Clinical Report</span>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
