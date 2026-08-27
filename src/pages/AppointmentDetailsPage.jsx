import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  getAppointmentById,
  updateAppointmentStatus as apiUpdateStatus,
  addDoctorConsultationNotes as apiAddNotes,
  getAppointmentMessages,
  sendAppointmentMessage,
} from '../services/api';
import {
  Calendar,
  Clock,
  Video,
  User,
  Building2,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  MessageSquare,
  Send,
  ShieldCheck,
  FileText,
  Sparkles,
  Eye,
  RotateCcw,
} from 'lucide-react';

const CalendarIcon = Calendar;
const ClockIcon = Clock;
const VideoCameraIcon = Video;
const UserIcon = User;
const BuildingOffice2Icon = Building2;
const CheckCircleIcon = CheckCircle2;
const XCircleIcon = XCircle;
const ArrowLeftIcon = ArrowLeft;
const ChatBubbleLeftRightIcon = MessageSquare;
const PaperAirplaneIcon = Send;
const ShieldCheckIcon = ShieldCheck;
const DocumentTextIcon = FileText;
const SparklesIcon = Sparkles;
const EyeIcon = Eye;
const ArrowPathIcon = RotateCcw;

export default function AppointmentDetailsPage() {
  const { id } = useParams();
  const { t, language } = useLanguage();
  const {
    getAppointmentById: getContextApt,
    updateAppointment: updateContextApt,
    getScreeningById,
    userRole,
    currentUser,
  } = useApp();
  const navigate = useNavigate();

  const [appointment, setAppointment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusFeedback, setStatusFeedback] = useState({ error: '', success: '' });

  // Doctor Note Form State
  const [doctorNotes, setDoctorNotes] = useState('');
  const [doctorRec, setDoctorRec] = useState('');
  const [followUpDate, setFollowUpDate] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);

  // Chat State
  const [messages, setMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sendingMsg, setSendingMsg] = useState(false);

  // Load appointment and messages
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        let apt = await getAppointmentById(id);
        if (!apt) {
          apt = getContextApt(id);
        }
        setAppointment(apt);

        if (apt) {
          const msgs = await getAppointmentMessages(id);
          setMessages(msgs);
        }
      } catch (err) {
        console.warn('Failed to fetch appointment details from server, using local store:', err);
        const apt = getContextApt(id);
        setAppointment(apt);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id, getContextApt]);

  const handleStatusChange = async (targetStatus, reasonComment = '') => {
    setActionLoading(true);
    setStatusFeedback({ error: '', success: '' });
    try {
      const callerRole = userRole || 'health_worker';
      const res = await apiUpdateStatus(id, {
        status: targetStatus,
        caller_role: callerRole,
        reason_or_comment: reasonComment || `Status updated to ${targetStatus} by ${callerRole}`,
      });
      setAppointment(res);
      updateContextApt(id, res);
      setStatusFeedback({
        error: '',
        success: `Appointment status updated to ${targetStatus}.`,
      });
    } catch (err) {
      setStatusFeedback({ error: err.message || 'Failed to update status.', success: '' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveNotes = async (e) => {
    e.preventDefault();
    if (!doctorNotes.trim() || !doctorRec.trim()) {
      setStatusFeedback({
        error: language === 'hi' ? 'कृपया परामर्श नोट्स और सिफारिशें दर्ज करें।' : 'Please enter clinical notes and recommendations.',
        success: '',
      });
      return;
    }

    setSavingNotes(true);
    setStatusFeedback({ error: '', success: '' });
    try {
      const res = await apiAddNotes(id, {
        doctor_id: currentUser?.id || appointment?.doctor_id || 'DOC-SWAMINATHAN',
        doctor_notes: doctorNotes.trim(),
        doctor_recommendation: doctorRec.trim(),
        follow_up_date: followUpDate || null,
      });
      setAppointment(res);
      updateContextApt(id, res);
      setStatusFeedback({
        error: '',
        success: language === 'hi' ? 'डॉक्टर परामर्श नोट्स सफलतापूर्वक सहेजे गए।' : 'Doctor consultation notes recorded with proper clinical attribution.',
      });
      setDoctorNotes('');
      setDoctorRec('');
    } catch (err) {
      setStatusFeedback({ error: err.message || 'Failed to record consultation notes.', success: '' });
    } finally {
      setSavingNotes(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    setSendingMsg(true);
    try {
      const role = userRole || 'health_worker';
      const senderName = currentUser?.name || (role === 'doctor' ? 'Dr. Swaminathan' : 'Pooja Sharma (ASHA)');
      const senderId = currentUser?.id || (role === 'doctor' ? 'DOC-SWAMINATHAN' : 'HW-RAMPUR-01');

      const newMsg = await sendAppointmentMessage(id, {
        sender_id: senderId,
        sender_name: senderName,
        sender_role: role,
        message: chatInput.trim(),
      });
      setMessages((prev) => [...prev, newMsg]);
      setChatInput('');
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSendingMsg(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-16 text-center text-slate-400 animate-pulse">
        Loading appointment details...
      </div>
    );
  }

  if (!appointment) {
    return (
      <div className="max-w-3xl mx-auto py-16 text-center">
        <XCircleIcon className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h2 className="text-xl font-bold text-white">Appointment Not Found</h2>
        <p className="text-sm text-slate-400 mt-1">
          The requested tele-ophthalmology appointment #{id} does not exist or has been removed.
        </p>
        <Link
          to="/appointments"
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs font-semibold hover:bg-slate-700"
        >
          <ArrowLeftIcon className="w-4 h-4" /> Back to Appointments
        </Link>
      </div>
    );
  }

  const linkedScreening = appointment.screening_id ? getScreeningById(appointment.screening_id) : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-16">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/appointments"
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeftIcon className="w-4 h-4" /> Back to Appointments
        </Link>

        {appointment.status === 'CONFIRMED' && (
          <Link
            to={`/appointments/${appointment.id}/video`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-900/30 transition-all active:scale-95"
          >
            <VideoCameraIcon className="w-4 h-4" />
            {t('joinVideoBtn')}
          </Link>
        )}
      </div>

      {/* Status Notifications */}
      {statusFeedback.error && (
        <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
          <XCircleIcon className="w-4 h-4 shrink-0" />
          <span>{statusFeedback.error}</span>
        </div>
      )}
      {statusFeedback.success && (
        <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircleIcon className="w-4 h-4 shrink-0" />
          <span>{statusFeedback.success}</span>
        </div>
      )}

      {/* Main Appointment Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/80 border border-indigo-500/30 px-2.5 py-0.5 rounded-full">
                #{appointment.id}
              </span>
              <span className="text-xs font-semibold px-3 py-0.5 rounded-full bg-slate-800 text-slate-200 border border-slate-700">
                {appointment.status}
              </span>
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight">
              {appointment.patient_name || appointment.patientName}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Age: {appointment.patient_age}y • Gender: {appointment.patient_gender} • Village: {appointment.village}
            </p>
          </div>

          {/* Scheduled Date & Time Badge */}
          <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 flex items-center gap-4 text-xs">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center font-bold">
              <CalendarIcon className="w-5 h-5" />
            </div>
            <div>
              <span className="text-slate-400 block">Consultation Schedule:</span>
              <span className="text-white font-bold text-sm">{appointment.date}</span>
              <span className="text-slate-400 block font-mono">
                {appointment.start_time} - {appointment.end_time}
              </span>
            </div>
          </div>
        </div>

        {/* Doctor & Health Worker Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800/80">
            <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wide block mb-1">
              Assigned Specialist
            </span>
            <div className="flex items-center justify-between">
              <div className="text-sm font-bold text-white">
                {appointment.doctor_name || appointment.doctorName}
              </div>
              <span className="inline-flex items-center gap-1 text-[11px] text-indigo-300 font-semibold bg-indigo-950/80 border border-indigo-500/30 px-2 py-0.5 rounded-full">
                <ShieldCheckIcon className="w-3 h-3" />
                {t('demoDoctorBadge')}
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-1">
              ID: <span className="font-mono text-slate-300">{appointment.doctor_id}</span>
            </div>
          </div>

          <div className="p-4 bg-slate-950/70 rounded-xl border border-slate-800/80">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide block mb-1">
              Referring Health Worker
            </span>
            <div className="text-sm font-bold text-white">
              {appointment.health_worker_name || appointment.healthWorkerName}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Email: <span className="text-slate-300">{appointment.health_worker_email || 'asha.rampur@phc.in'}</span>
            </div>
          </div>
        </div>

        {/* Consultation Reason */}
        <div className="p-4 bg-slate-950/40 rounded-xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-300 block mb-1">
            Reason for Consultation:
          </span>
          <p className="text-xs text-slate-300 leading-relaxed italic">
            &quot;{appointment.reason}&quot;
          </p>
        </div>

        {/* Doctor Action Controls (Accept, Decline, Reschedule, Cancel) */}
        <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-semibold text-slate-300">
            Appointment Status Workflow:
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {appointment.status === 'PENDING' && (
              <>
                <button
                  disabled={actionLoading}
                  onClick={() => handleStatusChange('CONFIRMED')}
                  className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-all"
                >
                  {t('acceptAppointmentBtn')}
                </button>
                <button
                  disabled={actionLoading}
                  onClick={() => handleStatusChange('DECLINED', 'Doctor unavailable for requested slot.')}
                  className="px-3 py-1.5 rounded-xl bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 text-xs font-semibold transition-all"
                >
                  {t('declineAppointmentBtn')}
                </button>
              </>
            )}

            {appointment.status === 'CONFIRMED' && (
              <button
                disabled={actionLoading}
                onClick={() => handleStatusChange('CANCELLED', 'Cancelled by health worker/patient request.')}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              >
                {t('cancelAppointmentBtn')}
              </button>
            )}
          </div>
        </div>

        {/* Doctor Clinical Notes (Recorded or Entry Form) */}
        {appointment.doctor_notes ? (
          <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
              <DocumentTextIcon className="w-4 h-4" />
              {t('doctorEnteredNote')}
            </div>
            <p className="text-xs text-emerald-200 leading-relaxed font-medium">
              {appointment.doctor_notes}
            </p>
            {appointment.doctor_recommendation && (
              <div className="text-xs text-slate-300 pt-2 border-t border-emerald-900/40">
                <span className="text-slate-400 font-semibold">Recommendation:</span> {appointment.doctor_recommendation}
              </div>
            )}
            {appointment.follow_up_date && (
              <div className="text-xs text-slate-400">
                <span>Follow-up Date:</span> <span className="font-semibold text-white">{appointment.follow_up_date}</span>
              </div>
            )}
          </div>
        ) : (
          (userRole === 'doctor' || appointment.status === 'CONFIRMED') && (
            <form onSubmit={handleSaveNotes} className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-wider">
                <DocumentTextIcon className="w-4 h-4" />
                {t('addConsultationNotes')}
              </div>
              <p className="text-[11px] text-slate-400">
                Clinical observations entered below will be permanently tagged as &apos;Doctor-entered consultation note&apos;.
              </p>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Clinical Consultation Notes *
                </label>
                <textarea
                  rows={3}
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                  placeholder="Enter fundus observations, DR staging confirmation, and clinical assessment..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    {t('doctorRecommendation')} *
                  </label>
                  <input
                    type="text"
                    value={doctorRec}
                    onChange={(e) => setDoctorRec(e.target.value)}
                    placeholder="e.g., Tighter glycemic control, rescreen in 6 months"
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    {t('followUpDateLabel')}
                  </label>
                  <input
                    type="date"
                    value={followUpDate}
                    onChange={(e) => setFollowUpDate(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={savingNotes}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/30"
                >
                  {savingNotes ? <ArrowPathIcon className="w-3.5 h-3.5 animate-spin" /> : null}
                  {t('saveNotesBtn')}
                </button>
              </div>
            </form>
          )
        )}
      </div>

      {/* Attached Screening Preview (Dual-Eye & Grad-CAM) */}
      {linkedScreening && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <EyeIcon className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-white">
                {t('screeningAttachment')} (#{linkedScreening.id})
              </h2>
            </div>
            <Link
              to={`/screenings/${linkedScreening.id}/report`}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
            >
              Open Full Clinical Report →
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* OD */}
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-xs font-semibold text-slate-300 block mb-2">
                Right Eye (OD): {linkedScreening.drSeverityOD || linkedScreening.overallSeverity || 'Graded'}
              </span>
              <img
                src={linkedScreening.imageOD || linkedScreening.image_od || '/samples/eyes.png'}
                alt="OD Retinal Scan"
                className="w-full h-44 object-cover rounded-lg border border-slate-800"
              />
            </div>
            {/* OS */}
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-xs font-semibold text-slate-300 block mb-2">
                Left Eye (OS): {linkedScreening.drSeverityOS || linkedScreening.overallSeverity || 'Graded'}
              </span>
              <img
                src={linkedScreening.imageOS || linkedScreening.image_os || '/samples/eyes_os.png'}
                alt="OS Retinal Scan"
                className="w-full h-44 object-cover rounded-lg border border-slate-800"
              />
            </div>
          </div>
        </div>
      )}

      {/* Appointment Scoped Coordination Chat */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl shadow-xl space-y-4">
        <div className="flex items-center gap-2">
          <ChatBubbleLeftRightIcon className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-bold text-white">
            {t('appointmentChatTitle')}
          </h2>
        </div>

        {/* Message Log */}
        <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 max-h-60 overflow-y-auto space-y-3">
          {messages.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-4">
              No chat messages yet. Health worker and specialist can coordinate details here.
            </p>
          ) : (
            messages.map((m) => {
              const isMe = m.sender_role === userRole || m.sender_id === currentUser?.id;
              return (
                <div
                  key={m.id}
                  className={`flex flex-col ${isMe ? 'items-end' : 'items-start'}`}
                >
                  <span className="text-[10px] text-slate-500 font-mono mb-0.5">
                    {m.sender_name} ({m.sender_role})
                  </span>
                  <div
                    className={`max-w-md p-2.5 rounded-xl text-xs ${
                      isMe
                        ? 'bg-indigo-600 text-white rounded-br-none'
                        : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700'
                    }`}
                  >
                    {m.message}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Chat Input */}
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder={t('typeMessagePlaceholder')}
            className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-xs text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={sendingMsg || !chatInput.trim()}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
          >
            <PaperAirplaneIcon className="w-3.5 h-3.5" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
