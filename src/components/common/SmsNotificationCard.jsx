import React, { useState, useEffect } from 'react';
import {
  Smartphone,
  CheckCircle2,
  AlertCircle,
  Clock,
  Send,
  Loader2,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  Eye,
  ShieldCheck,
  FileText,
  X,
  AlertTriangle,
} from 'lucide-react';
import {
  getSmsNotificationStatus,
  previewSmsNotification,
  simulateSmsNotification,
} from '../../services/api';

export const SmsNotificationCard = ({
  screeningId,
  doctorReviewStatus = 'PENDING DOCTOR REVIEW',
  patient = {},
  onNotificationSimulated = null,
  compact = false,
}) => {
  const [smsStatus, setSmsStatus] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [successToast, setSuccessToast] = useState(null);
  const [errorToast, setErrorToast] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  const fetchStatus = async () => {
    if (!screeningId) return;
    setIsLoading(true);
    try {
      const res = await getSmsNotificationStatus(screeningId);
      if (res) {
        setSmsStatus(res);
      }
    } catch (err) {
      console.warn('Failed to load SMS notification status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [screeningId, doctorReviewStatus]);

  const handleOpenPreview = async () => {
    setIsLoading(true);
    setErrorToast(null);
    try {
      const preview = await previewSmsNotification(screeningId);
      setPreviewData(preview);
      setIsPreviewModalOpen(true);
    } catch (err) {
      setErrorToast(err.message || 'Failed to generate SMS preview.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmSimulation = async (forceRegenerate = false) => {
    setIsSimulating(true);
    setErrorToast(null);
    try {
      const record = await simulateSmsNotification(screeningId, {
        force_regenerate: forceRegenerate,
      });
      setSelectedRecord(record);
      setIsPreviewModalOpen(false);
      setIsDetailModalOpen(true);
      setSuccessToast(`SMS Simulated Successfully! Message ID: ${record.notification_id}`);
      await fetchStatus();
      if (onNotificationSimulated) {
        onNotificationSimulated(record);
      }
    } catch (err) {
      setErrorToast(err.message || 'Simulation failed.');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleCopyLink = (url) => {
    if (!url) return;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  const maskedPhone =
    smsStatus?.recipient_mobile_masked ||
    (patient?.phone ? `${patient.phone.slice(0, 2)}******${patient.phone.slice(-2)}` : null);

  const isApproved =
    smsStatus?.can_notify ||
    doctorReviewStatus === 'AI RESULT ACCEPTED' ||
    doctorReviewStatus === 'DOCTOR REVIEWED / MODIFIED' ||
    doctorReviewStatus === 'verified';

  const isRecapture =
    doctorReviewStatus === 'IMAGE RE-CAPTURE REQUESTED' ||
    doctorReviewStatus === 'recapture_requested';

  const isSimulated = smsStatus?.status === 'SIMULATED' || Boolean(smsStatus?.notification_record);

  return (
    <div className="rounded-2xl border border-teal-200 bg-gradient-to-r from-teal-50/80 via-emerald-50/40 to-white p-4 sm:p-5 shadow-sm space-y-4 font-sans text-slate-800 transition">
      {/* Toast Messages */}
      {successToast && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-950 text-xs font-semibold animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successToast}</span>
        </div>
      )}
      {errorToast && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-100 border border-rose-300 text-rose-950 text-xs font-semibold animate-fade-in">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorToast}</span>
        </div>
      )}

      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-teal-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold shadow-md shadow-teal-600/20 shrink-0">
            <Smartphone className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs sm:text-sm font-extrabold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                <span>📱 Patient Notification</span>
              </h3>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider uppercase border ${
                  isSimulated
                    ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                    : isApproved && maskedPhone
                    ? 'bg-teal-100 text-teal-800 border-teal-300'
                    : isRecapture
                    ? 'bg-rose-100 text-rose-800 border-rose-300'
                    : 'bg-amber-100 text-amber-800 border-amber-300'
                }`}
              >
                Status:{' '}
                {isSimulated
                  ? 'SIMULATED'
                  : isApproved && maskedPhone
                  ? 'READY TO NOTIFY'
                  : isRecapture
                  ? 'REJECTED / BLOCKED'
                  : 'PENDING DOCTOR REVIEW'}
              </span>
            </div>
            <p className="text-[11px] text-slate-600 font-medium mt-0.5">
              Recipient:{' '}
              {maskedPhone ? (
                <span className="font-mono font-bold text-slate-900 bg-white/80 px-2 py-0.5 rounded border border-slate-200">
                  {maskedPhone}
                </span>
              ) : (
                <span className="text-rose-600 italic">Patient mobile number not available</span>
              )}
              <span className="mx-2 text-slate-300">•</span>
              Message Type: <span className="font-semibold text-slate-700">Doctor-reviewed report</span>
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 self-end sm:self-center">
          {isSimulated && (
            <button
              type="button"
              onClick={() => {
                setSelectedRecord(smsStatus?.notification_record);
                setIsDetailModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-teal-300 bg-white hover:bg-teal-50 text-teal-800 text-xs font-bold transition shadow-xs"
            >
              <Eye className="w-3.5 h-3.5" />
              <span>View Notification</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => handleOpenPreview()}
            disabled={isLoading || !isApproved || !maskedPhone}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition ${
              !isApproved || !maskedPhone
                ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                : isSimulated
                ? 'bg-teal-700 hover:bg-teal-800 text-white shadow-teal-600/20'
                : 'bg-teal-600 hover:bg-teal-700 text-white shadow-teal-500/20'
            }`}
            title={
              !isApproved
                ? 'Doctor review must be approved before notification'
                : !maskedPhone
                ? 'Patient mobile number is required'
                : 'Generate SMS Notification'
            }
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Smartphone className="w-4 h-4" />
            )}
            <span>{isSimulated ? 'Generate Again' : 'Generate SMS Notification'}</span>
          </button>
        </div>
      </div>

      {/* Clinical Safety & Readiness Checklist */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-medium text-slate-700">
        <div className="flex items-center gap-1.5 p-2 rounded-xl bg-white/70 border border-teal-100">
          <CheckCircle2
            className={`w-4 h-4 ${isApproved ? 'text-emerald-600' : 'text-slate-300'}`}
          />
          <span className={isApproved ? 'font-bold text-emerald-950' : 'text-slate-400'}>
            Report Verified
          </span>
        </div>

        <div className="flex items-center gap-1.5 p-2 rounded-xl bg-white/70 border border-teal-100">
          <CheckCircle2
            className={`w-4 h-4 ${maskedPhone ? 'text-emerald-600' : 'text-slate-300'}`}
          />
          <span className={maskedPhone ? 'font-bold text-emerald-950' : 'text-slate-400'}>
            Mobile Confirmed
          </span>
        </div>

        <div className="flex items-center gap-1.5 p-2 rounded-xl bg-white/70 border border-teal-100">
          <CheckCircle2
            className={`w-4 h-4 ${
              smsStatus?.notification_record || isApproved ? 'text-emerald-600' : 'text-slate-300'
            }`}
          />
          <span
            className={
              smsStatus?.notification_record || isApproved
                ? 'font-bold text-emerald-950'
                : 'text-slate-400'
            }
          >
            Secure Link Generated
          </span>
        </div>

        <div className="flex items-center gap-1.5 p-2 rounded-xl bg-white/70 border border-teal-100">
          <CheckCircle2
            className={`w-4 h-4 ${isSimulated ? 'text-emerald-600' : 'text-slate-300'}`}
          />
          <span className={isSimulated ? 'font-bold text-emerald-950' : 'text-slate-400'}>
            SMS Notification Prepared
          </span>
        </div>
      </div>

      {/* Duplicate Protection Notice */}
      {isSimulated && (
        <div className="p-3 rounded-xl bg-teal-100/70 border border-teal-200 text-teal-900 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-teal-700 shrink-0" />
            <span>
              <strong>Notification already generated</strong> (Message ID:{' '}
              <code className="font-mono font-bold text-teal-950">
                {smsStatus.notification_record?.notification_id}
              </code>
              ).
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleConfirmSimulation(true)}
              disabled={isSimulating}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-[11px] font-bold shadow-xs transition"
            >
              {isSimulating ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
              <span>Generate Again</span>
            </button>
            <button
              type="button"
              onClick={() => setShowHistory(!showHistory)}
              className="text-[11px] font-bold text-teal-800 hover:underline"
            >
              {showHistory ? 'Hide Log' : 'History Log'}
            </button>
          </div>
        </div>
      )}

      {/* Historical Notification Log */}
      {showHistory && smsStatus?.notification_history?.length > 0 && (
        <div className="p-3 rounded-xl bg-white border border-teal-200 text-xs space-y-2">
          <h4 className="font-bold text-slate-900 text-[11px] uppercase tracking-wider">
            Simulated Notification Log
          </h4>
          <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            {smsStatus.notification_history.map((item, idx) => (
              <div
                key={idx}
                className="p-2 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-[11px]"
              >
                <div>
                  <span className="font-mono font-bold text-teal-900">{item.notification_id}</span>
                  <span className="text-slate-500 ml-2">To: {item.recipient_mobile_masked}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">
                    SIMULATED
                  </span>
                  <span className="text-slate-400 font-mono text-[10px]">
                    {new Date(item.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 1. SMS PREVIEW MODAL */}
      {isPreviewModalOpen && previewData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs no-print animate-fade-in">
          <div className="w-full max-w-lg bg-white rounded-3xl p-6 sm:p-7 shadow-2xl border border-slate-100 space-y-5 font-sans">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold shadow-md">
                  <Smartphone className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-extrabold text-slate-900">📱 SMS PREVIEW</h3>
                  <p className="text-[11px] text-slate-500">
                    Demonstration Patient Screening Notification
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsPreviewModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500 font-medium">To (Recipient):</span>
                <span className="font-mono font-bold text-slate-900">
                  {previewData.recipient_mobile_masked}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500 font-medium">Patient:</span>
                <span className="font-bold text-slate-900">{previewData.patient_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500 font-medium">Doctor Review Status:</span>
                <span className="font-bold text-emerald-700">
                  {previewData.doctor_review_status}
                </span>
              </div>
              <div className="space-y-1.5 pt-1">
                <span className="text-slate-500 font-medium">Message Body:</span>
                <div className="p-3 rounded-xl bg-white border border-teal-200 font-mono text-slate-800 text-[11px] whitespace-pre-wrap leading-relaxed shadow-inner">
                  {previewData.message_preview}
                </div>
              </div>
            </div>

            {/* Disclaimer notice */}
            <div className="p-3 rounded-xl bg-teal-50 border border-teal-200 text-teal-900 text-[11px] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
              <span>{previewData.disclaimer}</span>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-1">
              <button
                type="button"
                onClick={() => setIsPreviewModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleConfirmSimulation(false)}
                disabled={isSimulating}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 transition disabled:opacity-50"
              >
                {isSimulating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                <span>Confirm Demo Notification</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. SIMULATED SUCCESSFUL DELIVERY DETAIL MODAL */}
      {isDetailModalOpen && selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs no-print animate-fade-in">
          <div className="w-full max-w-lg bg-white rounded-3xl p-6 sm:p-7 shadow-2xl border border-slate-100 space-y-5 font-sans">
            <div className="flex items-center justify-between pb-3 border-b border-emerald-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold shadow-md">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-extrabold text-slate-900">
                    SMS SIMULATED SUCCESSFULLY
                  </h3>
                  <p className="text-[11px] text-emerald-700 font-bold">
                    Status: SIMULATED (Demonstration)
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsDetailModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Status:</span>
                <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 font-extrabold uppercase">
                  {selectedRecord.status}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Recipient:</span>
                <span className="font-mono font-bold text-slate-900">
                  {selectedRecord.recipient_mobile_masked}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Message ID:</span>
                <span className="font-mono font-bold text-teal-900">
                  {selectedRecord.notification_id}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Generated At:</span>
                <span className="font-mono text-slate-700">
                  {new Date(selectedRecord.created_at).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Report:</span>
                <span className="font-mono font-bold text-slate-900">
                  {selectedRecord.screening_id}
                </span>
              </div>
              <div className="space-y-1 pt-1">
                <span className="text-slate-500">Secure Report Link:</span>
                <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-teal-200 font-mono text-[11px] text-teal-950 break-all">
                  <span className="flex-1">{selectedRecord.secure_report_url}</span>
                  <button
                    type="button"
                    onClick={() => handleCopyLink(selectedRecord.secure_report_url)}
                    className="p-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 shrink-0 transition"
                    title="Copy report link"
                  >
                    {copiedLink ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Highlighted Disclaimer Alert */}
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-950 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
              <span>{selectedRecord.disclaimer}</span>
            </div>

            <div className="flex items-center justify-between pt-1">
              <a
                href={
                  selectedRecord.secure_report_token
                    ? `/patient-report/${selectedRecord.secure_report_token}`
                    : '#'
                }
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 transition"
              >
                <ExternalLink className="w-4 h-4" />
                <span>Open Secure Report Page</span>
              </a>

              <button
                type="button"
                onClick={() => setIsDetailModalOpen(false)}
                className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-md transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmsNotificationCard;
