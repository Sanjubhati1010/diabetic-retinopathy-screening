import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ShieldCheck,
  CheckCircle2,
  FileText,
  Download,
  AlertCircle,
  Stethoscope,
  Eye,
  User,
  MapPin,
  Calendar,
  Clock,
  Sparkles,
  ArrowLeft,
  Loader2,
} from 'lucide-react';
import { getSecurePatientReportByToken } from '../services/api';

export const SecurePatientReportPage = () => {
  const { token } = useParams();
  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    if (!token) {
      setErrorMsg('No access token provided.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    getSecurePatientReportByToken(token)
      .then((res) => {
        setReportData(res);
        setErrorMsg(null);
      })
      .catch((err) => {
        setErrorMsg(err.message || 'Access Forbidden: This clinical report is not doctor-approved or token is invalid.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [token]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6 text-white space-y-4">
        <Loader2 className="w-10 h-10 text-teal-400 animate-spin" />
        <p className="text-sm font-bold text-teal-200">Verifying secure report access token...</p>
      </div>
    );
  }

  if (errorMsg || !reportData) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6 font-sans">
        <div className="max-w-md w-full bg-slate-800 border border-rose-500/40 rounded-3xl p-6 sm:p-8 text-center space-y-4 shadow-2xl">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-extrabold text-white">Access Restricted</h2>
          <p className="text-xs text-slate-300 leading-relaxed">{errorMsg}</p>
          <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-700 text-[11px] text-slate-400">
            For security and privacy, clinical reports are only accessible when reviewed and approved by a licensed ophthalmologist.
          </div>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold transition shadow-md"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Portal</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 py-8 px-4 sm:px-6 lg:px-8 font-sans text-slate-800">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Top Header Card */}
        <div className="bg-gradient-to-r from-teal-900 via-slate-900 to-teal-950 border border-teal-500/30 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-teal-500/20 border border-teal-400/30 rounded-xl">
                <Eye className="w-5 h-5 text-teal-300" />
              </div>
              <h1 className="text-lg sm:text-xl font-extrabold tracking-tight">
                Rural DR Screening — Clinical Report
              </h1>
            </div>
            <p className="text-xs text-teal-200/90 font-medium">
              Verified Tele-Ophthalmology Screening Report
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-bold text-emerald-300 bg-emerald-950/80 px-3.5 py-1.5 rounded-2xl border border-emerald-700/60 shrink-0">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Doctor Verified & Signed</span>
          </div>
        </div>

        {/* Demonstration Disclaimer Banner */}
        <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-950 text-xs font-semibold flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>DEMONSTRATION SYSTEM:</strong> This report was accessed via a simulated secure SMS link.
          </span>
        </div>

        {/* Patient & Screening Summary Strip */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-base">
                <User className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-slate-900">
                  {reportData.patient_name}
                </h2>
                <p className="text-xs text-slate-500 font-medium flex items-center gap-2 mt-0.5">
                  <span className="font-mono">ID: {reportData.patient_id}</span>
                  {reportData.age && <span>• {reportData.age} yrs</span>}
                  {reportData.gender && <span>• {reportData.gender}</span>}
                  {reportData.village && (
                    <span className="flex items-center gap-1">
                      • <MapPin className="w-3 h-3 text-slate-400 inline" /> {reportData.village}
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="text-left sm:text-right text-xs">
              <span className="text-slate-400 block font-medium">Screening Date</span>
              <span className="font-bold text-slate-800 flex items-center sm:justify-end gap-1 mt-0.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {reportData.screening_date}
              </span>
            </div>
          </div>

          {/* Clinical Findings Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Doctor-Verified Classification
              </span>
              <p className="text-base font-black text-slate-900">
                {reportData.final_dr_result}
              </p>
              <p className="text-xs text-slate-500 font-medium">
                Overall Severity: <strong>{reportData.overall_severity}</strong>
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Referral & Follow-up Urgency
              </span>
              <p className="text-sm font-extrabold text-teal-800">
                {reportData.referral_priority}
              </p>
              <p className="text-xs text-slate-600 font-medium">
                {reportData.recommendation}
              </p>
            </div>
          </div>

          {/* Specialist Sign-Off Box */}
          <div className="p-4 rounded-2xl bg-teal-50/70 border border-teal-200 text-xs space-y-2">
            <div className="flex items-center gap-2 text-teal-950 font-bold">
              <Stethoscope className="w-4 h-4 text-teal-700" />
              <span>Reviewing Specialist: {reportData.doctor_name}</span>
            </div>
            {reportData.doctor_notes && (
              <p className="text-slate-700 italic text-[11px] bg-white p-2.5 rounded-xl border border-teal-100">
                "{reportData.doctor_notes}"
              </p>
            )}
            <p className="text-[10px] text-teal-800 font-medium">
              Human-in-the-Loop review completed. Digitally verified for rural community care.
            </p>
          </div>

          {/* Download Report Actions */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <span className="text-[11px] text-slate-400 font-mono">
              Report Token: {reportData.token}
            </span>

            {reportData.pdf_download_url && (
              <a
                href={reportData.pdf_download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 transition"
              >
                <Download className="w-4 h-4" />
                <span>Download Official PDF Report</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecurePatientReportPage;
