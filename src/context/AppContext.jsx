import React, { createContext, useContext, useState, useEffect } from 'react';
import { MOCK_PATIENTS, MOCK_SCREENINGS, SAMPLE_FUNDUS_IMAGES } from '../data/mockData';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // Authentication State - Default to FALSE so Login page is always shown on start/refresh
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // User Role: 'health_worker' | 'doctor' | 'admin'
  const [userRole, setUserRole] = useState('health_worker');

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
    return patients.find((p) => p.id === id) || patients[0];
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
    return screenings.find((s) => s.id === id) || screenings[0];
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
    setOfflineSyncCount(0);
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
