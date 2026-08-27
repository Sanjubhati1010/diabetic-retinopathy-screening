import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { MOCK_PATIENTS, MOCK_SCREENINGS, SAMPLE_FUNDUS_IMAGES } from '../data/mockData';
import { voiceService } from '../services/voiceService';
import {
  safeLocalStorageSet,
  safeLocalStorageGet,
  getLightweightReview,
  sanitizeScreeningsForStorage,
  sanitizePatientsForStorage,
} from '../services/storage';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // Authentication State - Default to FALSE so Login page is always shown on start/refresh
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // User Role: 'health_worker' | 'doctor' | 'admin'
  const [userRole, setUserRole] = useState('health_worker');

  // Phase 7: Rural Mode, Low-Bandwidth Mode & Voice Guidance Preferences
  const [ruralMode, setRuralMode] = useState(() => {
    return safeLocalStorageGet('madocs_rural_mode', false) === 'true' || safeLocalStorageGet('madocs_rural_mode', false) === true;
  });

  const [lowBandwidthMode, setLowBandwidthMode] = useState(() => {
    return safeLocalStorageGet('madocs_low_bandwidth', false) === 'true' || safeLocalStorageGet('madocs_low_bandwidth', false) === true;
  });

  const [voiceGuidanceEnabled, setVoiceGuidanceEnabled] = useState(() => {
    return safeLocalStorageGet('madocs_voice_guidance', false) === 'true' || safeLocalStorageGet('madocs_voice_guidance', false) === true;
  });

  // Reactive Network Status Detection
  const [networkState, setNetworkState] = useState(() => {
    const online = typeof navigator !== 'undefined' ? navigator.onLine : true;
    const conn = typeof navigator !== 'undefined' && navigator.connection;
    const effectiveType = conn?.effectiveType || '4g';
    let status = online ? 'connected' : 'offline';
    if (online && (effectiveType === '2g' || effectiveType === 'slow-2g')) {
      status = 'weak';
    }
    return {
      isOnline: online,
      effectiveType,
      downlink: conn?.downlink || null,
      rtt: conn?.rtt || null,
      status,
    };
  });

  // Phase 7: Offline Sync Queue for Non-AI Records (Drafts, Reviews)
  const [pendingSyncQueue, setPendingSyncQueue] = useState(() => {
    return safeLocalStorageGet('madocs_sync_queue', []);
  });

  const [patients, setPatients] = useState(() => {
    return safeLocalStorageGet('dr_patients', MOCK_PATIENTS);
  });

  const [screenings, setScreenings] = useState(() => {
    return safeLocalStorageGet('dr_screenings', MOCK_SCREENINGS);
  });

  // Phase 11: Appointments & Doctors State
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState(() => {
    const saved = safeLocalStorageGet('dr_appointments', null);
    if (saved) return saved;
    return [
      {
        id: "APT-2026-101",
        doctor_id: "DOC-SWAMINATHAN",
        doctor_name: "Dr. Arvind Swaminathan, MS",
        health_worker_id: "HW-RAMPUR-01",
        health_worker_name: "Pooja Sharma (ASHA Worker)",
        health_worker_email: "asha.rampur@phc.in",
        patient_id: "PAT-2026-081",
        patient_name: "Ramesh Kumar Verma",
        patient_age: 58,
        patient_gender: "male",
        village: "Rampur Gram Panchayat",
        screening_id: "SCR-2026-0991",
        screening_summary: "Moderate DR (AI Confidence 85.0%)",
        date: "2026-08-28",
        start_time: "10:00",
        end_time: "10:30",
        reason: "Patient has moderate NPDR detected by AI screening. Diabetic for 8 years, complains of occasional blurriness.",
        status: "CONFIRMED",
        created_at: "2026-08-22T09:30:00Z",
        updated_at: "2026-08-22T10:00:00Z",
        doctor_notes: null,
        doctor_recommendation: null,
      },
      {
        id: "APT-2026-102",
        doctor_id: "DOC-SWAMINATHAN",
        doctor_name: "Dr. Arvind Swaminathan, MS",
        health_worker_id: "HW-SHIVPURI-02",
        health_worker_name: "Sarita Devi (Vision Tech)",
        health_worker_email: "sarita.vision@phc.in",
        patient_id: "PAT-2026-082",
        patient_name: "Sunita Devi",
        patient_age: 52,
        patient_gender: "female",
        village: "Shivpuri Taluk",
        screening_id: "SCR-2026-0992",
        screening_summary: "Severe DR (AI Confidence 92.1%)",
        date: "2026-08-28",
        start_time: "11:00",
        end_time: "11:30",
        reason: "Severe NPDR AI alert with multiple microaneurysms. Specialist urgent consultation requested.",
        status: "CONFIRMED",
        created_at: "2026-08-23T11:15:00Z",
        updated_at: "2026-08-23T11:15:00Z",
        doctor_notes: null,
        doctor_recommendation: null,
      },
      {
        id: "APT-2026-103",
        doctor_id: "DOC-NAMBIAR",
        doctor_name: "Dr. Meera Nambiar, MD, DNB",
        health_worker_id: "HW-KOLAR-03",
        health_worker_name: "Sunil Gowda (Vision Tech)",
        health_worker_email: "sunil.gowda@phc.in",
        patient_id: "PAT-2026-083",
        patient_name: "Balwinder Singh",
        patient_age: 64,
        patient_gender: "male",
        village: "Kalyanpur Camp",
        screening_id: "SCR-2026-0993",
        screening_summary: "Proliferative DR (AI Confidence 94.8%)",
        date: "2026-08-20",
        start_time: "15:00",
        end_time: "15:30",
        reason: "High risk neovascularization suspected in left eye.",
        status: "COMPLETED",
        created_at: "2026-08-19T14:00:00Z",
        updated_at: "2026-08-20T15:35:00Z",
        doctor_notes: "Doctor-entered consultation note: Tele-examination confirms active proliferative DR features. Immediate tertiary referral for panretinal photocoagulation (PRP) scheduled.",
        doctor_recommendation: "Emergency referral to District Hospital Ophthalmology dept for laser intervention.",
        follow_up_date: "2026-09-05",
      },
      {
        id: "APT-2026-104",
        doctor_id: "DOC-RAO",
        doctor_name: "Dr. K. Srinivas Rao, DO, FRCS",
        health_worker_id: "HW-RAMPUR-01",
        health_worker_name: "Pooja Sharma (ASHA Worker)",
        health_worker_email: "asha.rampur@phc.in",
        patient_id: "PAT-2026-084",
        patient_name: "Lakshmi Patel",
        patient_age: 49,
        patient_gender: "female",
        village: "Gopalpur Village",
        screening_id: "SCR-2026-0994",
        screening_summary: "Mild NPDR (AI Confidence 78.4%)",
        date: "2026-08-29",
        start_time: "14:00",
        end_time: "14:30",
        reason: "Routine tele-ophthalmology screening review for newly diagnosed diabetic patient.",
        status: "PENDING",
        created_at: "2026-08-24T16:20:00Z",
        updated_at: "2026-08-24T16:20:00Z",
        doctor_notes: null,
        doctor_recommendation: null,
      }
    ];
  });

  // Save appointments to local storage
  useEffect(() => {
    safeLocalStorageSet('dr_appointments', appointments);
  }, [appointments]);

  // Offline mode state for rural connectivity simulation
  const [isOnline, setIsOnline] = useState(true);
  const [offlineSyncCount, setOfflineSyncCount] = useState(3);
  const [highContrast, setHighContrast] = useState(false);
  const [largeText, setLargeText] = useState(false);

  // Active in-progress screening state
  const [activeScreening, setActiveScreening] = useState({
    patientId: 'PAT-2026-081',
    campLocation: 'Rampur PHC Community Camp',
    cameraModel: 'Forus 3nethra Classic HD',
    dilation: 'undilated',
    imageOD: SAMPLE_FUNDUS_IMAGES.sample_od,
    imageOS: SAMPLE_FUNDUS_IMAGES.sample_os,
    fileOD: null,
    fileOS: null,
    odStatus: 'ready', // 'pending' | 'validating' | 'valid' | 'warning' | 'recapture_required' | 'ready'
    osStatus: 'ready',
    odValidation: {
      is_valid_file: true,
      is_retinal: true,
      quality_grade: 'good',
      screening_status: 'Ready for Screening',
      can_proceed: true,
      reasons: [],
      metrics: { resolution: '1009x857', sharpness_score: 103.8, brightness_score: 131.5, retinal_coverage: 0.88 },
      message: 'Image validated successfully and ready for screening.',
    },
    osValidation: {
      is_valid_file: true,
      is_retinal: true,
      quality_grade: 'good',
      screening_status: 'Ready for Screening',
      can_proceed: true,
      reasons: [],
      metrics: { resolution: '980x840', sharpness_score: 98.4, brightness_score: 128.2, retinal_coverage: 0.86 },
      message: 'Image validated successfully and ready for screening.',
    },
    selectedEyeForAnalysis: 'OD',
    qualityChecked: true,
    odQuality: { illumination: true, focus: true, noArtifacts: true },
    osQuality: { illumination: true, focus: true, noArtifacts: true },
    rightEyeAnalysis: null,
    leftEyeAnalysis: null,
    odAnalysisError: null,
    osAnalysisError: null,
    overallSeverity: 'drUncertain',
    aiResult: null,
  });

  useEffect(() => {
    safeLocalStorageSet('dr_patients', sanitizePatientsForStorage(patients));
  }, [patients]);

  useEffect(() => {
    safeLocalStorageSet('dr_screenings', sanitizeScreeningsForStorage(screenings));
  }, [screenings]);

  const login = (role, userDetails) => {
    setIsAuthenticated(true);
    setUserRole(role);
    setCurrentUser(userDetails || { role });
  };

  const logout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  const addPatient = (newPatient) => {
    const id = `PAT-2026-${String(patients.length + 81).padStart(3, '0')}`;
    const patientObj = {
      ...newPatient,
      id,
      registeredDate: new Date().toISOString().split('T')[0],
      lastScreened: '-',
      latestStatus: 'drUncertain',
      referralUrgency: 'routine',
      doctorVerified: false,
    };
    setPatients((prev) => [patientObj, ...prev]);
    return patientObj;
  };

  const getPatientById = (id) => {
    const found = patients.find((p) => p.id === id);
    if (found) return found;
    if (patients && patients.length > 0) return patients[0];
    return {
      id: id || 'PAT-2026-081',
      name: 'Unknown Patient',
      age: 45,
      gender: 'Other',
      village: 'Rampur',
      diabetesDuration: 5,
      lastHba1c: 7.5,
      visualAcuityOD: '6/6',
      visualAcuityOS: '6/6',
      phone: '+91 98765 00000',
      abhaId: 'ABHA-9876-0000',
    };
  };

  const addScreening = (screeningData) => {
    const id = `SCR-2026-${String(screenings.length + 991).padStart(4, '0')}`;
    const newScr = {
      ...screeningData,
      id,
      screeningDate: new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }),
      doctorStatus: 'pending',
    };
    setScreenings((prev) => [newScr, ...prev]);

    // Update patient's latestStatus
    setPatients((prev) =>
      prev.map((p) =>
        p.id === screeningData.patientId
          ? {
              ...p,
              lastScreened: new Date().toISOString().split('T')[0],
              latestStatus: screeningData.overallSeverity || 'drUncertain',
              referralUrgency: screeningData.referralUrgency || 'routine',
            }
          : p
      )
    );

    return newScr;
  };

  const getScreeningById = (id) => {
    if (!id) return screenings[0] || activeScreening || null;
    const found = screenings.find((s) => s.id === id || s.screening_id === id);
    if (found) return found;
    if (activeScreening && (activeScreening.id === id || activeScreening.screening_id === id)) return activeScreening;

    // Check lightweight cache
    const local = getLightweightReview(id);
    if (local) {
      return {
        id,
        patientId: 'PAT-2026-081',
        patientName: 'Ramesh Kumar Verma',
        village: 'Rampur',
        screeningDate: local.updatedAt ? new Date(local.updatedAt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : new Date().toLocaleString('en-IN'),
        className: local.doctorReviewedResult || 'Moderate',
        confidence: 0.85,
        overallSeverity: 'dr2',
        riskCategory: 'MODERATE',
        referralPriority: 'EYE SPECIALIST REVIEW RECOMMENDED',
        screeningStatus: 'RELIABLE AI SCREENING',
        safetyStatus: 'READY_FOR_AI',
        doctorStatus: local.reviewStatus === 'AI RESULT ACCEPTED' ? 'verified' : 'pending',
        imageOD: SAMPLE_FUNDUS_IMAGES.sample_od,
        imageOS: SAMPLE_FUNDUS_IMAGES.sample_os,
      };
    }

    // Dynamic fallback for any valid SCR-* screening ID
    if (typeof id === 'string' && id.startsWith('SCR-')) {
      const template = (screenings && screenings[0]) || {
        patientId: 'PAT-2026-081',
        patientName: 'Ramesh Kumar Verma',
        village: 'Rampur',
        screeningDate: new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }),
        className: 'Moderate',
        confidence: 0.85,
        overallSeverity: 'dr2',
        riskCategory: 'MODERATE',
        referralPriority: 'EYE SPECIALIST REVIEW RECOMMENDED',
        screeningStatus: 'RELIABLE AI SCREENING',
        safetyStatus: 'READY_FOR_AI',
        doctorStatus: 'pending',
        imageOD: SAMPLE_FUNDUS_IMAGES.sample_od,
        imageOS: SAMPLE_FUNDUS_IMAGES.sample_os,
      };
      return {
        ...template,
        id,
      };
    }

    return (screenings && screenings[0]) || null;
  };

  const getPatientScreenings = useCallback(
    (patientId) => {
      if (!patientId) return [];
      return screenings
        .filter((s) => s.patientId === patientId || s.patient_id === patientId)
        .sort((a, b) => {
          const dateA = new Date(a.screeningDate || a.date || 0).getTime();
          const dateB = new Date(b.screeningDate || b.date || 0).getTime();
          return dateB - dateA;
        });
    },
    [screenings]
  );

  const getLatestComparableScreening = useCallback(
    (currentScreeningId, patientId) => {
      const targetScreening = getScreeningById(currentScreeningId);
      const pid = targetScreening?.patientId || targetScreening?.patient_id || patientId;
      if (!pid) return null;
      const patientHistory = getPatientScreenings(pid);
      const candidates = patientHistory.filter((s) => (s.id || s.screening_id) !== currentScreeningId);
      return candidates.length > 0 ? candidates[0] : null;
    },
    [getScreeningById, getPatientScreenings]
  );

  const updateScreeningReview = (screeningId, reviewResponse) => {
    if (!screeningId || !reviewResponse) return;

    setScreenings((prev) => {
      let found = false;
      const updated = prev.map((s) => {
        if (s.id === screeningId) {
          found = true;
          const status = reviewResponse.review_status;
          const isVerified = status === 'AI RESULT ACCEPTED' || status === 'DOCTOR REVIEWED / MODIFIED';
          const isRecapture = status === 'IMAGE RE-CAPTURE REQUESTED';
          return {
            ...s,
            reviewStatus: status,
            doctorStatus: isRecapture ? 'recapture_requested' : isVerified ? 'verified' : 'pending',
            doctorReviewedResult: reviewResponse.doctor_reviewed_result,
            doctorRemarks: reviewResponse.review_comment,
            doctorReviewDate: reviewResponse.review_timestamp || new Date().toISOString(),
            reviewerName: reviewResponse.reviewer_name || 'Dr. A. Swaminathan, MS',
          };
        }
        return s;
      });

      // If not in existing array, prepend a new item
      let finalScreenings = updated;
      if (!found) {
        const status = reviewResponse.review_status;
        const isVerified = status === 'AI RESULT ACCEPTED' || status === 'DOCTOR REVIEWED / MODIFIED';
        const isRecapture = status === 'IMAGE RE-CAPTURE REQUESTED';
        const newRecord = {
          id: screeningId,
          patientId: 'PAT-2026-081',
          patientName: 'Patient',
          village: 'Rampur',
          screeningDate: new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }),
          className: reviewResponse.original_ai_result || 'Moderate DR',
          confidence: reviewResponse.original_confidence || 0.85,
          overallSeverity: 'dr2',
          riskCategory: 'MODERATE',
          referralPriority: isRecapture ? 'IMAGE RE-CAPTURE REQUIRED' : 'EYE SPECIALIST REVIEW RECOMMENDED',
          screeningStatus: isRecapture ? 'IMAGE RE-CAPTURE REQUESTED' : 'RELIABLE AI SCREENING',
          safetyStatus: 'READY_FOR_AI',
          reviewStatus: status,
          doctorStatus: isRecapture ? 'recapture_requested' : isVerified ? 'verified' : 'pending',
          doctorReviewedResult: reviewResponse.doctor_reviewed_result,
          doctorRemarks: reviewResponse.review_comment,
          doctorReviewDate: reviewResponse.review_timestamp || new Date().toISOString(),
          reviewerName: reviewResponse.reviewer_name || 'Dr. A. Swaminathan, MS',
          imageOD: SAMPLE_FUNDUS_IMAGES.sample_od,
          imageOS: SAMPLE_FUNDUS_IMAGES.sample_os,
        };
        finalScreenings = [newRecord, ...prev];
      }

      safeLocalStorageSet('dr_screenings', sanitizeScreeningsForStorage(finalScreenings));
      return finalScreenings;
    });
  };

  // Network Event Listeners
  useEffect(() => {
    const handleOnline = () => {
      const conn = navigator.connection;
      const effectiveType = conn?.effectiveType || '4g';
      setNetworkState({
        isOnline: true,
        effectiveType,
        downlink: conn?.downlink || null,
        rtt: conn?.rtt || null,
        status: effectiveType === '2g' || effectiveType === 'slow-2g' ? 'weak' : 'connected',
      });
      setIsOnline(true);
    };

    const handleOffline = () => {
      setNetworkState((prev) => ({
        ...prev,
        isOnline: false,
        status: 'offline',
      }));
      setIsOnline(false);
    };

    const handleConnectionChange = () => {
      if (navigator.onLine) {
        handleOnline();
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    if (navigator.connection) {
      navigator.connection.addEventListener('change', handleConnectionChange);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (navigator.connection) {
        navigator.connection.removeEventListener('change', handleConnectionChange);
      }
    };
  }, []);

  // Persist Rural Mode & Low Bandwidth Preferences
  useEffect(() => {
    safeLocalStorageSet('madocs_rural_mode', String(ruralMode));
    if (ruralMode) {
      document.documentElement.classList.add('rural-mode');
    } else {
      document.documentElement.classList.remove('rural-mode');
    }
  }, [ruralMode]);

  useEffect(() => {
    safeLocalStorageSet('madocs_low_bandwidth', String(lowBandwidthMode));
    if (lowBandwidthMode) {
      document.documentElement.classList.add('low-bandwidth');
    } else {
      document.documentElement.classList.remove('low-bandwidth');
    }
  }, [lowBandwidthMode]);

  useEffect(() => {
    safeLocalStorageSet('madocs_voice_guidance', String(voiceGuidanceEnabled));
  }, [voiceGuidanceEnabled]);

  useEffect(() => {
    safeLocalStorageSet('madocs_sync_queue', pendingSyncQueue);
    setOfflineSyncCount(pendingSyncQueue.filter((q) => q.status === 'PENDING_SYNC').length);
  }, [pendingSyncQueue]);

  const toggleRuralMode = () => setRuralMode((prev) => !prev);
  const toggleLowBandwidthMode = () => setLowBandwidthMode((prev) => !prev);
  const toggleVoiceGuidance = () => {
    setVoiceGuidanceEnabled((prev) => {
      const next = !prev;
      if (!next) {
        voiceService.stop();
      }
      return next;
    });
  };

  const speakPrompt = useCallback(
    (text, language = 'en') => {
      if (voiceGuidanceEnabled) {
        voiceService.speak(text, language);
      }
    },
    [voiceGuidanceEnabled]
  );

  // Phase 7: Add item to offline sync queue (e.g. drafts or reviews)
  const addToSyncQueue = (type, payload) => {
    const queueItem = {
      id: `SYNC-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      type, // 'PATIENT_DRAFT' | 'DOCTOR_REVIEW' | 'SCREENING_INTAKE'
      payload,
      timestamp: new Date().toISOString(),
      status: 'PENDING_SYNC',
    };
    setPendingSyncQueue((prev) => [queueItem, ...prev]);
    return queueItem;
  };

  const syncPendingQueue = () => {
    // Mark all pending as synced
    setPendingSyncQueue((prev) =>
      prev.map((item) => ({
        ...item,
        status: 'SYNCED',
        syncedAt: new Date().toISOString(),
      }))
    );
    setOfflineSyncCount(0);
    return true;
  };

  const clearSyncedQueue = () => {
    setPendingSyncQueue((prev) => prev.filter((item) => item.status === 'PENDING_SYNC'));
  };

  const doctorVerifyScreening = (screeningId, { confirmedSeverity, doctorRemarks, signatureApproved }) => {
    setScreenings((prev) =>
      prev.map((s) => {
        if (s.id === screeningId) {
          return {
            ...s,
            overallSeverity: confirmedSeverity || s.overallSeverity,
            doctorRemarks: doctorRemarks || s.doctorRemarks,
            doctorStatus: signatureApproved ? 'verified' : 'pending',
          };
        }
        return s;
      })
    );
  };

  const syncOfflineQueue = () => {
    syncPendingQueue();
    return true;
  };

  // Phase 11: Appointments Helper Methods
  const addAppointment = (newApt) => {
    setAppointments((prev) => [newApt, ...prev.filter((a) => a.id !== newApt.id)]);
  };

  const updateAppointment = (appointmentId, updates) => {
    setAppointments((prev) =>
      prev.map((a) => (a.id === appointmentId ? { ...a, ...updates, updated_at: new Date().toISOString() } : a))
    );
  };

  const getAppointmentById = (appointmentId) => {
    return appointments.find((a) => a.id === appointmentId) || null;
  };

  const getAppointmentsForPatient = (patientId) => {
    return appointments.filter((a) => a.patient_id === patientId || a.patientId === patientId);
  };

  return (
    <AppContext.Provider
      value={{
        isAuthenticated,
        currentUser,
        login,
        logout,
        userRole,
        setUserRole,
        patients,
        addPatient,
        getPatientById,
        screenings,
        addScreening,
        getScreeningById,
        getPatientScreenings,
        getLatestComparableScreening,
        doctorVerifyScreening,
        updateScreeningReview,
        activeScreening,
        setActiveScreening,
        // Phase 11 Appointments & Tele-Ophthalmology
        doctors,
        setDoctors,
        appointments,
        setAppointments,
        addAppointment,
        updateAppointment,
        getAppointmentById,
        getAppointmentsForPatient,
        isOnline,
        setIsOnline,
        offlineSyncCount,
        syncOfflineQueue,
        highContrast,
        setHighContrast,
        largeText,
        setLargeText,
        // Phase 7 Rural Deployments
        ruralMode,
        setRuralMode,
        toggleRuralMode,
        lowBandwidthMode,
        setLowBandwidthMode,
        toggleLowBandwidthMode,
        voiceGuidanceEnabled,
        setVoiceGuidanceEnabled,
        toggleVoiceGuidance,
        networkState,
        pendingSyncQueue,
        addToSyncQueue,
        syncPendingQueue,
        clearSyncedQueue,
        speakPrompt,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
