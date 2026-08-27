import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  getDoctors,
  getDoctorAvailability,
  bookAppointment as apiBookAppointment,
} from '../services/api';
import {
  Calendar,
  Clock,
  Video,
  User,
  Building2,
  CheckCircle2,
  XCircle,
  Filter,
  Plus,
  MessageSquare,
  ShieldCheck,
  Info,
  RotateCcw,
  Sparkles,
} from 'lucide-react';

const CalendarIcon = Calendar;
const ClockIcon = Clock;
const VideoCameraIcon = Video;
const UserIcon = User;
const BuildingOffice2Icon = Building2;
const CheckCircleIcon = CheckCircle2;
const XCircleIcon = XCircle;
const FunnelIcon = Filter;
const PlusIcon = Plus;
const ChatBubbleLeftRightIcon = MessageSquare;
const ShieldCheckIcon = ShieldCheck;
const InformationCircleIcon = Info;
const ArrowPathIcon = RotateCcw;
const SparklesIcon = Sparkles;

export default function AppointmentsPage() {
  const { t, language } = useLanguage();
  const {
    patients,
    screenings,
    appointments,
    addAppointment,
    userRole,
    currentUser,
    ruralMode,
  } = useApp();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('directory'); // 'directory' | 'appointments'
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [doctorsList, setDoctorsList] = useState([]);
  const [loadingDoctors, setLoadingDoctors] = useState(true);

  // Booking Modal State
  const [isBookingModalOpen, setIsBookingModalOpen] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [selectedScreeningId, setSelectedScreeningId] = useState('');
  const [selectedDate, setSelectedDate] = useState(() => {
    // Tomorrow by default
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  });
  const [selectedTimeSlot, setSelectedTimeSlot] = useState('');
  const [consultReason, setConsultReason] = useState('');
  const [availableSlots, setAvailableSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotMessage, setSlotMessage] = useState('');
  const [bookingSubmitting, setBookingSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState('');

  // Fetch doctors on mount
  useEffect(() => {
    async function loadDocs() {
      setLoadingDoctors(true);
      try {
        const docs = await getDoctors();
        setDoctorsList(docs);
      } catch (err) {
        console.error('Error fetching doctors:', err);
      } finally {
        setLoadingDoctors(false);
      }
    }
    loadDocs();
  }, []);

  // Fetch slots whenever selected doctor or date changes in booking modal
  useEffect(() => {
    if (!isBookingModalOpen || !selectedDoctor || !selectedDate) return;

    async function loadSlots() {
      setLoadingSlots(true);
      setSlotMessage('');
      try {
        const data = await getDoctorAvailability(selectedDoctor.id, selectedDate);
        setAvailableSlots(data.slots || []);
        if (data.message) {
          setSlotMessage(data.message);
        } else if (!data.is_working_day) {
          setSlotMessage(t('notWorkingDay') || 'Doctor is not scheduled on this day.');
        } else if (data.available_slots_count === 0) {
          setSlotMessage(t('noSlotsAvailable') || 'No slots available on this date.');
        }
      } catch (err) {
        console.warn('Error loading slots:', err);
        setSlotMessage(err.message || 'Unable to retrieve time slots');
      } finally {
        setLoadingSlots(false);
      }
    }

    loadSlots();
  }, [isBookingModalOpen, selectedDoctor, selectedDate, t]);

  const handleOpenBooking = (doc) => {
    setSelectedDoctor(doc);
    setSelectedPatientId(patients?.[0]?.id || '');
    setSelectedScreeningId('');
    setSelectedTimeSlot('');
    setConsultReason(
      language === 'hi'
        ? 'मरीज़ को डायबिटिक रेटिनोपैथी टेली-परामर्श की आवश्यकता है।'
        : 'AI screening follow-up tele-ophthalmology consultation requested for rural patient.'
    );
    setBookingError('');
    setBookingSuccess('');
    setIsBookingModalOpen(true);
  };

  const handleConfirmBooking = async (e) => {
    e.preventDefault();
    if (!selectedDoctor || !selectedPatientId || !selectedDate || !selectedTimeSlot || !consultReason.trim()) {
      setBookingError(language === 'hi' ? 'कृपया सभी अनिवार्य फ़ील्ड भरें।' : 'Please fill all required fields.');
      return;
    }

    setBookingSubmitting(true);
    setBookingError('');

    const patient = patients.find((p) => p.id === selectedPatientId) || { name: 'Patient', age: 50, gender: 'unknown', village: 'Rampur' };
    const screening = screenings.find((s) => s.id === selectedScreeningId);

    const payload = {
      doctor_id: selectedDoctor.id,
      health_worker_id: currentUser?.id || 'HW-RAMPUR-01',
      health_worker_name: currentUser?.name || 'Pooja Sharma (ASHA Worker)',
      health_worker_email: currentUser?.email || 'asha.rampur@phc.in',
      patient_id: patient.id,
      patient_name: patient.name,
      patient_age: patient.age || 50,
      patient_gender: patient.gender || 'unknown',
      village: patient.village || 'Rampur Gram Panchayat',
      screening_id: screening?.id || null,
      screening_summary: screening ? `${screening.overallSeverity || screening.predicted_class_name || 'AI Screened'} (Confidence ${(screening.confidence ? screening.confidence * 100 : 85).toFixed(1)}%)` : null,
      date: selectedDate,
      start_time: selectedTimeSlot,
      reason: consultReason.trim(),
    };

    try {
      const res = await apiBookAppointment(payload);
      addAppointment(res);
      setBookingSuccess(
        language === 'hi'
          ? `अपॉइंटमेंट #${res.id} सफलतापूर्वक बुक हो गई है!`
          : `Appointment #${res.id} booked successfully!`
      );
      setTimeout(() => {
        setIsBookingModalOpen(false);
        setActiveTab('appointments');
      }, 1500);
    } catch (err) {
      setBookingError(err.message || 'Failed to book appointment.');
    } finally {
      setBookingSubmitting(false);
    }
  };

  const filteredAppointments = appointments.filter((apt) => {
    if (statusFilter === 'ALL') return true;
    return apt.status === statusFilter;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'CONFIRMED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-500/40">
            <CheckCircleIcon className="w-3.5 h-3.5" />
            {t('appointmentStatusConfirmed')}
          </span>
        );
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-500/40">
            <ClockIcon className="w-3.5 h-3.5" />
            {t('appointmentStatusPending')}
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-950/80 text-blue-300 border border-blue-500/40">
            <CheckCircleIcon className="w-3.5 h-3.5" />
            {t('appointmentStatusCompleted')}
          </span>
        );
      case 'DECLINED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-500/40">
            <XCircleIcon className="w-3.5 h-3.5" />
            {t('appointmentStatusDeclined')}
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <XCircleIcon className="w-3.5 h-3.5" />
            {t('appointmentStatusCancelled')}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 rounded-2xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-400/30 text-indigo-300 text-xs font-semibold tracking-wide uppercase mb-3">
              <SparklesIcon className="w-3.5 h-3.5" />
              Phase 11 Tele-Ophthalmology
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {t('teleOphthalmologyTitle')}
            </h1>
            <p className="text-slate-400 text-sm sm:text-base mt-1.5 max-w-2xl">
              {t('teleOphthalmologySub')}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (doctorsList.length > 0) handleOpenBooking(doctorsList[0]);
              }}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all active:scale-95"
            >
              <PlusIcon className="w-4 h-4" />
              {t('bookAppointmentBtn')}
            </button>
          </div>
        </div>

        {/* Rural Notice */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-start gap-2.5 text-xs text-indigo-200/80">
          <InformationCircleIcon className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <span>{t('ruralTeleNotice')}</span>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center justify-between border-b border-slate-800">
        <div className="flex gap-4 sm:gap-8">
          <button
            onClick={() => setActiveTab('directory')}
            className={`pb-3 text-sm font-semibold transition-all relative ${
              activeTab === 'directory'
                ? 'text-indigo-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t('findDoctorTab')}
            {activeTab === 'directory' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 shadow-sm" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('appointments')}
            className={`pb-3 text-sm font-semibold transition-all relative flex items-center gap-2 ${
              activeTab === 'appointments'
                ? 'text-indigo-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t('myAppointmentsTab')}
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 text-xs font-mono">
              {appointments.length}
            </span>
            {activeTab === 'appointments' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 shadow-sm" />
            )}
          </button>
        </div>

        {activeTab === 'appointments' && (
          <div className="flex items-center gap-2 pb-2">
            <FunnelIcon className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter appointments by status"
              className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
              <option value="DECLINED">Declined</option>
            </select>
          </div>
        )}
      </div>

      {/* TAB 1: Doctor Directory */}
      {activeTab === 'directory' && (
        <div>
          {loadingDoctors ? (
            <div className="p-12 text-center text-slate-400 animate-pulse">
              Loading doctor directory...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {doctorsList.map((doc) => (
                <div
                  key={doc.id}
                  className="bg-slate-900/90 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-6 flex flex-col justify-between transition-all duration-200 hover:shadow-xl hover:shadow-indigo-950/20 group"
                >
                  <div>
                    {/* Top Row: Avatar Badge & Demo Tag */}
                    <div className="flex items-start justify-between gap-3 mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-900 text-white font-bold text-base flex items-center justify-center shadow-md">
                          {doc.avatar_badge || 'DR'}
                        </div>
                        <div>
                          <h2 className="text-white font-bold text-base group-hover:text-indigo-300 transition-colors">
                            {doc.name}
                          </h2>
                          <p className="text-xs text-indigo-400 font-medium">
                            {doc.title}
                          </p>
                        </div>
                      </div>

                      {doc.is_demo && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-500/30 shrink-0">
                          <ShieldCheckIcon className="w-3 h-3" />
                          {t('demoDoctorBadge')}
                        </span>
                      )}
                    </div>

                    {/* Specialization & Hospital */}
                    <div className="space-y-2 mb-4 text-xs">
                      <div className="text-slate-300 font-medium">
                        {doc.specialization}
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-400">
                        <BuildingOffice2Icon className="w-3.5 h-3.5 shrink-0" />
                        <span>{doc.hospital}</span>
                      </div>
                      <div className="text-slate-400">
                        📍 {doc.location}
                      </div>
                    </div>

                    {/* Meta: Experience, Languages & Rating */}
                    <div className="grid grid-cols-2 gap-2 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 mb-5 text-[11px]">
                      <div>
                        <span className="text-slate-500 block">Experience:</span>
                        <span className="text-slate-200 font-semibold">{doc.experience_years} Years</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Languages:</span>
                        <span className="text-slate-200 font-medium truncate block">
                          {doc.languages?.join(', ')}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Working Hours:</span>
                        <span className="text-slate-200 font-medium font-mono">
                          {doc.working_hours_start} - {doc.working_hours_end}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Tele-Rating:</span>
                        <span className="text-amber-400 font-semibold">★ {doc.rating} / 5.0</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <button
                    onClick={() => handleOpenBooking(doc)}
                    className="w-full py-2.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 hover:border-transparent text-xs font-semibold transition-all duration-150 flex items-center justify-center gap-2"
                  >
                    <CalendarIcon className="w-4 h-4" />
                    {t('bookAppointmentBtn')}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: My Appointments List */}
      {activeTab === 'appointments' && (
        <div className="space-y-4">
          {filteredAppointments.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40">
              <CalendarIcon className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h2 className="text-base font-semibold text-slate-300">
                No appointments found
              </h2>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                No appointments matching status &apos;{statusFilter}&apos;. Schedule a new tele-consultation with a specialist.
              </p>
              <button
                onClick={() => setActiveTab('directory')}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500"
              >
                Browse Doctors
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredAppointments.map((apt) => (
                <div
                  key={apt.id}
                  className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 flex flex-col justify-between transition-all"
                >
                  <div>
                    {/* Top Row: ID, Status */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="text-xs font-mono font-semibold text-indigo-400">
                        #{apt.id}
                      </span>
                      {getStatusBadge(apt.status)}
                    </div>

                    {/* Patient & Doctor Header */}
                    <div className="mb-3">
                      <h2 className="text-white font-bold text-base flex items-center gap-2">
                        <UserIcon className="w-4 h-4 text-indigo-400" />
                        {apt.patient_name || apt.patientName}
                      </h2>
                      <div className="text-xs text-slate-400 mt-0.5">
                        Specialist: <span className="text-slate-200 font-medium">{apt.doctor_name || apt.doctorName}</span>
                      </div>
                      <div className="text-xs text-slate-400">
                        Village: <span className="text-slate-300">{apt.village || 'Rampur'}</span>
                      </div>
                    </div>

                    {/* Scheduled Time & Attached Screening */}
                    <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 mb-3 space-y-1.5 text-xs">
                      <div className="flex items-center gap-2 text-slate-200">
                        <CalendarIcon className="w-3.5 h-3.5 text-indigo-400" />
                        <span className="font-semibold">{apt.date}</span>
                        <span className="text-slate-500">•</span>
                        <ClockIcon className="w-3.5 h-3.5 text-indigo-400" />
                        <span className="font-mono">{apt.start_time} - {apt.end_time}</span>
                      </div>

                      {apt.screening_summary && (
                        <div className="text-[11px] text-amber-300/90 pt-1 border-t border-slate-800/60">
                          📊 Linked Screening: {apt.screening_summary}
                        </div>
                      )}

                      {apt.doctor_notes && (
                        <div className="text-[11px] text-emerald-300 pt-1 border-t border-slate-800/60">
                          ✍️ <span className="font-semibold">{apt.doctor_notes}</span>
                        </div>
                      )}
                    </div>

                    {/* Reason */}
                    <p className="text-xs text-slate-400 line-clamp-2 mb-4 italic">
                      &quot;{apt.reason}&quot;
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-3 border-t border-slate-800/80">
                    <Link
                      to={`/appointments/${apt.id}`}
                      className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition-colors"
                    >
                      View Details
                    </Link>

                    {apt.status === 'CONFIRMED' && (
                      <Link
                        to={`/appointments/${apt.id}/video`}
                        className="flex-1 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold text-center flex items-center justify-center gap-1.5 transition-all shadow-md shadow-emerald-900/30"
                      >
                        <VideoCameraIcon className="w-3.5 h-3.5" />
                        {t('joinVideoBtn')}
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* BOOKING MODAL WIZARD */}
      {isBookingModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative">
            {/* Header */}
            <div className="flex items-start justify-between mb-5">
              <div>
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider block">
                  {t('scheduleConsultation')}
                </span>
                <h2 className="text-xl font-bold text-white mt-0.5">
                  {selectedDoctor?.name}
                </h2>
                <p className="text-xs text-slate-400">
                  {selectedDoctor?.specialization} • {selectedDoctor?.hospital}
                </p>
              </div>
              <button
                onClick={() => setIsBookingModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <XCircleIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Error / Success Notifications */}
            {bookingError && (
              <div className="mb-4 p-3 rounded-xl bg-rose-950/80 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-2">
                <XCircleIcon className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{bookingError}</span>
              </div>
            )}

            {bookingSuccess && (
              <div className="mb-4 p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-xs flex items-start gap-2">
                <CheckCircleIcon className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{bookingSuccess}</span>
              </div>
            )}

            <form onSubmit={handleConfirmBooking} className="space-y-4">
              {/* Patient Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  {t('selectPatient')} *
                </label>
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                >
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.age}y, {p.gender}) — {p.village || 'Rampur'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Link Screening (Optional) */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  {t('linkScreeningOptional')}
                </label>
                <select
                  value={selectedScreeningId}
                  onChange={(e) => setSelectedScreeningId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="">-- Do not link screening --</option>
                  {screenings.map((s) => (
                    <option key={s.id} value={s.id}>
                      #{s.id} — {s.patientName || s.patient_name} ({s.overallSeverity || s.predicted_class_name || 'AI Screened'}, {s.date || s.screening_date})
                    </option>
                  ))}
                </select>
              </div>

              {/* Date Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  {t('selectDate')} *
                </label>
                <input
                  type="date"
                  value={selectedDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                />
              </div>

              {/* Time Slot Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  {t('selectTimeSlot')} *
                </label>
                {loadingSlots ? (
                  <div className="p-4 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                    <ArrowPathIcon className="w-4 h-4 animate-spin text-indigo-400" />
                    Checking doctor availability...
                  </div>
                ) : availableSlots.length === 0 ? (
                  <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-amber-400">
                    {slotMessage || t('noSlotsAvailable')}
                  </div>
                ) : (
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-40 overflow-y-auto p-1">
                    {availableSlots.map((slot) => (
                      <button
                        key={slot.start_time}
                        type="button"
                        disabled={!slot.available}
                        onClick={() => setSelectedTimeSlot(slot.start_time)}
                        className={`py-2 px-2 rounded-lg text-xs font-mono font-medium transition-all ${
                          selectedTimeSlot === slot.start_time
                            ? 'bg-indigo-600 text-white font-bold ring-2 ring-indigo-400'
                            : slot.available
                            ? 'bg-slate-950 border border-slate-700 text-slate-200 hover:border-indigo-400'
                            : 'bg-slate-950/40 border border-slate-800 text-slate-600 cursor-not-allowed line-through'
                        }`}
                      >
                        {slot.start_time}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Consultation Reason */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  {t('consultationReason')} *
                </label>
                <textarea
                  value={consultReason}
                  onChange={(e) => setConsultReason(e.target.value)}
                  rows={3}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  placeholder="Describe patient symptoms, screening severity, and primary reason for tele-consultation..."
                  required
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsBookingModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={bookingSubmitting || !selectedTimeSlot}
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 flex items-center gap-2"
                >
                  {bookingSubmitting ? (
                    <>
                      <ArrowPathIcon className="w-3.5 h-3.5 animate-spin" />
                      Booking...
                    </>
                  ) : (
                    t('confirmBookingBtn')
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
