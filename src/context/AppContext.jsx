import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { MOCK_PATIENTS, MOCK_SCREENINGS, SAMPLE_FUNDUS_IMAGES } from '../data/mockData';
import { voiceService } from '../services/voiceService';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // Authentication State - Default to FALSE so Login page is always shown on start/refresh
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // User Role: 'health_worker' | 'doctor' | 'admin'
  const [userRole, setUserRole] = useState('health_worker');

  // Phase 7: Rural Mode, Low-Bandwidth Mode & Voice Guidance Preferences
  const [ruralMode, setRuralMode] = useState(() => {
    try {
      return localStorage.getItem('madocs_rural_mode') === 'true';
    } catch {
      return false;
    }
  });

  const [lowBandwidthMode, setLowBandwidthMode] = useState(() => {
    try {
      return localStorage.getItem('madocs_low_bandwidth') === 'true';
    } catch {
      return false;
    }
  });

  const [voiceGuidanceEnabled, setVoiceGuidanceEnabled] = useState(() => {
    try {
      return localStorage.getItem('madocs_voice_guidance') === 'true';
    } catch {
      return false;
    }
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
    try {
      const saved = localStorage.getItem('madocs_sync_queue');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [patients, setPatients] = useState(() => {
    try {
      const saved = localStorage.getItem('dr_patients');
      return saved ? JSON.parse(saved) : MOCK_PATIENTS;
    } catch {
      return MOCK_PATIENTS;
    }
  });

  const [screenings, setScreenings] = useState(() => {
    try {
      const saved = localStorage.getItem('dr_screenings');
      return saved ? JSON.parse(saved) : MOCK_SCREENINGS;
    } catch {
      return MOCK_SCREENINGS;
    }
  });

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
    try {
      localStorage.setItem('dr_patients', JSON.stringify(patients));
    } catch (e) {
      console.warn('Unable to persist patients to localStorage:', e);
    }
  }, [patients]);

  useEffect(() => {
    try {
      localStorage.setItem('dr_screenings', JSON.stringify(screenings));
    } catch (e) {
      console.warn('Unable to persist screenings to localStorage:', e);
    }
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
    const found = screenings.find((s) => s.id === id);
    if (found) return found;
    if (activeScreening && activeScreening.id === id) return activeScreening;

    // Check localStorage cache
    try {
      const local = localStorage.getItem(`madocs_review_${id}`);
      if (local) {
        const parsed = JSON.parse(local);
        return {
          id,
          patientId: 'PAT-2026-081',
          patientName: 'Patient',
          village: 'Rampur',
          screeningDate: parsed.review_timestamp ? new Date(parsed.review_timestamp).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : new Date().toLocaleString('en-IN'),
          className: parsed.original_ai_result || 'Moderate DR',
          confidence: parsed.original_confidence || 0.85,
          overallSeverity: 'dr2',
          riskCategory: 'MODERATE',
          referralPriority: 'EYE SPECIALIST REVIEW RECOMMENDED',
          screeningStatus: 'RELIABLE AI SCREENING',
          safetyStatus: 'READY_FOR_AI',
          doctorStatus: parsed.review_status === 'AI RESULT ACCEPTED' ? 'verified' : 'pending',
          imageOD: SAMPLE_FUNDUS_IMAGES.sample_od,
          imageOS: SAMPLE_FUNDUS_IMAGES.sample_os,
        };
      }
    } catch (e) {
      console.warn('Error reading cached screening:', e);
    }

    return null;
  };

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

      try {
        localStorage.setItem('dr_screenings', JSON.stringify(finalScreenings));
      } catch (e) {
        console.warn('Unable to persist screenings to localStorage:', e);
      }
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
    try {
      localStorage.setItem('madocs_rural_mode', String(ruralMode));
      if (ruralMode) {
        document.documentElement.classList.add('rural-mode');
      } else {
        document.documentElement.classList.remove('rural-mode');
      }
    } catch (e) {
      console.warn('Unable to persist ruralMode:', e);
    }
  }, [ruralMode]);

  useEffect(() => {
    try {
      localStorage.setItem('madocs_low_bandwidth', String(lowBandwidthMode));
      if (lowBandwidthMode) {
        document.documentElement.classList.add('low-bandwidth');
      } else {
        document.documentElement.classList.remove('low-bandwidth');
      }
    } catch (e) {
      console.warn('Unable to persist lowBandwidthMode:', e);
    }
  }, [lowBandwidthMode]);

  useEffect(() => {
    try {
      localStorage.setItem('madocs_voice_guidance', String(voiceGuidanceEnabled));
    } catch (e) {
      console.warn('Unable to persist voiceGuidanceEnabled:', e);
    }
  }, [voiceGuidanceEnabled]);

  useEffect(() => {
    try {
      localStorage.setItem('madocs_sync_queue', JSON.stringify(pendingSyncQueue));
      setOfflineSyncCount(pendingSyncQueue.filter((q) => q.status === 'PENDING_SYNC').length);
    } catch (e) {
      console.warn('Unable to persist pendingSyncQueue:', e);
    }
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
        doctorVerifyScreening,
        updateScreeningReview,
        activeScreening,
        setActiveScreening,
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
