import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './context/LanguageContext';
import { AppProvider, useApp } from './context/AppContext';
import { DashboardLayout } from './components/layout/DashboardLayout';

// 16 Core Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { PatientRegisterPage } from './pages/PatientRegisterPage';
import { PatientListPage } from './pages/PatientListPage';
import { PatientProfilePage } from './pages/PatientProfilePage';
import { NewScreeningPage } from './pages/NewScreeningPage';
import { ImageUploadPage } from './pages/ImageUploadPage';
import { AiAnalysisPage } from './pages/AiAnalysisPage';
import { ScreeningResultPage } from './pages/ScreeningResultPage';
import { ExplainableAiPage } from './pages/ExplainableAiPage';
import { ScreeningHistoryPage } from './pages/ScreeningHistoryPage';
import { PatientReportPage } from './pages/PatientReportPage';
import { DoctorDashboardPage } from './pages/DoctorDashboardPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import AppointmentsPage from './pages/AppointmentsPage';
import AppointmentDetailsPage from './pages/AppointmentDetailsPage';
import VideoConsultationPage from './pages/VideoConsultationPage';

// Protected Route Component to require explicit login
const ProtectedDashboardLayout = () => {
  const { isAuthenticated } = useApp();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <DashboardLayout />;
};

function AppRoutes() {
  const { isAuthenticated, userRole } = useApp();

  return (
    <Routes>
      {/* App starts at Login page */}
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <Navigate to={userRole === 'doctor' ? '/doctor' : '/dashboard'} replace />
          ) : (
            <LoginPage />
          )
        }
      />
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to={userRole === 'doctor' ? '/doctor' : '/dashboard'} replace />
          ) : (
            <LoginPage />
          )
        }
      />

      {/* Optional public landing overview */}
      <Route path="/landing" element={<LandingPage />} />

      {/* Authenticated Dashboard Pages wrapped in Protected Layout */}
      <Route element={<ProtectedDashboardLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/patients" element={<PatientListPage />} />
        <Route path="/patients/register" element={<PatientRegisterPage />} />
        <Route path="/patients/:id" element={<PatientProfilePage />} />

        {/* Screening & Explainable AI Workflow */}
        <Route path="/screenings/new" element={<NewScreeningPage />} />
        <Route path="/screenings/upload" element={<ImageUploadPage />} />
        <Route path="/screenings/analysis" element={<AiAnalysisPage />} />
        <Route path="/screenings/:id/result" element={<ScreeningResultPage />} />
        <Route path="/screenings/result" element={<ScreeningResultPage />} />
        <Route path="/screenings/:id/xai" element={<ExplainableAiPage />} />
        <Route path="/screenings/xai" element={<ExplainableAiPage />} />
        <Route path="/screenings/:id/gradcam" element={<ExplainableAiPage />} />
        <Route path="/screenings/gradcam" element={<ExplainableAiPage />} />
        <Route path="/screenings/:id/report" element={<PatientReportPage />} />
        <Route path="/screenings/report" element={<PatientReportPage />} />
        <Route path="/history" element={<ScreeningHistoryPage />} />

        {/* Phase 11: Specialist Tele-Ophthalmology & Appointments */}
        <Route path="/appointments" element={<AppointmentsPage />} />
        <Route path="/appointments/:id" element={<AppointmentDetailsPage />} />
        <Route path="/appointments/:id/video" element={<VideoConsultationPage />} />

        {/* Specialist Tele-Ophthalmology & Insights */}
        <Route path="/doctor" element={<DoctorDashboardPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Catch-all fallback */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AppProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AppProvider>
    </LanguageProvider>
  );
}

export default App;
