import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import {
  Eye,
  Languages,
  Wifi,
  WifiOff,
  UserCheck,
  Stethoscope,
  Menu,
  X,
  Bell,
  ChevronDown,
  Sparkles,
  MapPin,
} from 'lucide-react';

export const Navbar = ({ onToggleSidebar }) => {
  const { language, toggleLanguage, t } = useLanguage();
  const { userRole, setUserRole, isOnline, setIsOnline, offlineSyncCount, logout } = useApp();
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleRoleChange = (role) => {
    setUserRole(role);
    setRoleDropdownOpen(false);
    if (role === 'doctor') {
      navigate('/doctor');
    } else {
      navigate('/dashboard');
    }
  };

  const getRoleLabel = () => {
    switch (userRole) {
      case 'doctor':
        return t('roleDoctor');
      case 'admin':
        return t('roleAdmin');
      default:
        return t('roleWorker');
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-sm transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Mobile Menu + Brand */}
          <div className="flex items-center gap-3">
            {onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 focus:outline-none"
                aria-label="Toggle Navigation"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}

            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center text-white shadow-glow group-hover:scale-105 transition-transform">
                <Eye className="w-5 h-5" />
              </div>
              <div className="hidden sm:block">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-base text-slate-900 tracking-tight">
                    Rural DR Screening <span className="text-brand-600">AI</span>
                  </span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-100 text-brand-800 border border-brand-200">
                    Clinical
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 font-medium hidden md:block">
                  Explainable AI for Diabetic Retinopathy Screening in Rural India
                </p>
              </div>
            </Link>

            {/* Active Camp Badge */}
            <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium">
              <MapPin className="w-3.5 h-3.5 text-emerald-600" />
              <span>{t('activeCamp')}</span>
            </div>
          </div>

          {/* Right: Controls & Actions */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Language Switcher */}
            <button
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-bold text-slate-700 transition shadow-sm"
              title="Toggle Language / भाषा बदलें"
            >
              <Languages className="w-4 h-4 text-brand-600" />
              <span className={language === 'en' ? 'text-brand-700 font-bold' : 'text-slate-500'}>EN</span>
              <span className="text-slate-300">/</span>
              <span className={language === 'hi' ? 'text-brand-700 font-bold' : 'text-slate-500'}>हिन्दी</span>
            </button>

            {/* Connectivity Switch (Rural Offline Mode Simulator) */}
            <button
              onClick={() => setIsOnline(!isOnline)}
              className={`hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition ${
                isOnline
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                  : 'bg-amber-50 text-amber-800 border-amber-300 hover:bg-amber-100'
              }`}
              title="Toggle Online/Offline mode simulation"
            >
              {isOnline ? (
                <>
                  <Wifi className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{t('onlineStatus')}</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-amber-600" />
                  <span>
                    {t('offlineStatus')} ({offlineSyncCount})
                  </span>
                </>
              )}
            </button>

            {/* Role Switcher Dropdown */}
            <div className="relative">
              <button
                onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 text-xs font-medium text-slate-700 shadow-sm transition"
              >
                <div className="w-2 h-2 rounded-full bg-brand-500"></div>
                <span className="max-w-[130px] sm:max-w-none truncate font-semibold">{getRoleLabel()}</span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {roleDropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white border border-slate-200 shadow-xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
                  <div className="px-3 py-1.5 border-b border-slate-100">
                    <p className="text-[11px] font-semibold uppercase text-slate-400">{t('roleSwitch')}</p>
                  </div>
                  <button
                    onClick={() => handleRoleChange('health_worker')}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2 hover:bg-slate-50 transition ${
                      userRole === 'health_worker' ? 'text-brand-700 font-bold bg-brand-50/50' : 'text-slate-700'
                    }`}
                  >
                    <UserCheck className="w-4 h-4 text-brand-600" />
                    <span>{t('roleWorker')}</span>
                  </button>
                  <button
                    onClick={() => handleRoleChange('doctor')}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2 hover:bg-slate-50 transition ${
                      userRole === 'doctor' ? 'text-brand-700 font-bold bg-brand-50/50' : 'text-slate-700'
                    }`}
                  >
                    <Stethoscope className="w-4 h-4 text-teal-600" />
                    <span>{t('roleDoctor')}</span>
                  </button>
                </div>
              )}
            </div>

            {/* Logout Button */}
            <button
              type="button"
              onClick={handleLogout}
              className="hidden sm:inline-flex items-center justify-center px-3 py-1.5 text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-lg transition"
            >
              {t('navLogout')}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
