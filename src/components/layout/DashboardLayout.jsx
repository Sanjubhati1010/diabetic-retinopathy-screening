import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Navbar } from '../common/Navbar';
import { Sidebar } from '../common/Sidebar';
import { RuralModeBanner } from '../common/RuralModeBanner';
import { AiScreeningAssistant } from '../assistant/AiScreeningAssistant';
import { useApp } from '../../context/AppContext';

export const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { highContrast, largeText, ruralMode } = useApp();
  const location = useLocation();

  return (
    <div
      className={`min-h-screen bg-slate-50 text-slate-900 flex flex-col ${
        highContrast ? 'contrast-125 saturate-150' : ''
      } ${largeText || ruralMode ? 'text-base' : 'text-sm'}`}
    >
      {/* Responsive Fixed Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content & Header Area (Offset by sidebar width on desktop) */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64 transition-all w-full">
        {/* Rural Mode & Bandwidth Top Banner */}
        <RuralModeBanner />

        {/* Top Navbar Header */}
        <Navbar onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        {/* Page Content */}
        <main className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
            <Outlet />
          </div>

          {/* Footer */}
          <footer className="no-print border-t border-slate-200/70 py-4 px-6 bg-white/50 text-center text-xs text-slate-500">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
              <p>
                <strong>Explainable AI for Diabetic Retinopathy Screening in Rural India</strong>
              </p>
              <p className="text-slate-400 text-[11px]">
                Built for Primary Health Centers & Vision Technicians • v2.4.0
              </p>
            </div>
          </footer>
        </main>
      </div>

      {/* Global Contextual AI Screening Assistant Drawer */}
      <AiScreeningAssistant />
    </div>
  );
};
