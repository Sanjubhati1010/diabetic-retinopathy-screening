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
  Smartphone,
} from 'lucide-react';

import { NetworkIndicator } from './NetworkIndicator';

export const Navbar = ({ onToggleSidebar }) => {
  const { language, toggleLanguage, t } = useLanguage();
  const { userRole, setUserRole, logout, ruralMode, toggleRuralMode } = useApp();
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
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs w-full transition-colors">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 w-full">
        <div className="flex items-center justify-between h-16 w-full flex-nowrap gap-2 sm:gap-4 min-w-0">
          {/* Left: Mobile Menu + Brand + Location Badge */}
          <div className="flex items-center gap-2 sm:gap-3 flex-nowrap min-w-0 shrink">
            {onToggleSidebar && (
              <button
                type="button"
                onClick={onToggleSidebar}
                className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 focus:outline-none shrink-0"
                aria-label="Toggle Navigation"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}

            {/* Logo + Title */}
            <Link to="/" className="flex items-center gap-2 sm:gap-2.5 group min-w-0 shrink">
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 flex items-center justify-center text-white shadow-glow group-hover:scale-105 transition-transform shrink-0">
                <Eye className="w-5 h-5" />
              </div>
              <div className="min-w-0 shrink">
                <div className="flex items-center gap-1.5 sm:gap-2 flex-nowrap">
                  <span className="font-extrabold text-sm sm:text-base text-slate-900 tracking-tight whitespace-nowrap">
                    Rural DR Screening <span className="text-brand-600">AI</span>
                  </span>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-100 text-brand-800 border border-brand-200 shrink-0">
                    Clinical
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 font-medium hidden 2xl:block truncate max-w-[260px]">
                  Explainable AI for Diabetic Retinopathy Screening
                </p>
              </div>
            </Link>

            {/* Location / Rural Camp Badge */}
            <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium shrink-0 whitespace-nowrap">
              <MapPin className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span className="truncate max-w-[150px] xl:max-w-none">{t('activeCamp') || 'Rampur PHC Camp'}</span>
            </div>
          </div>

          {/* Right: Controls & Actions (Language, Connected, Rural Mode, Actions) */}
          <div className="flex items-center gap-1.5 sm:gap-2 lg:gap-2.5 flex-nowrap shrink-0">
            {/* Language Switcher */}
            <button
              type="button"
              onClick={toggleLanguage}
              className="flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-bold text-slate-700 transition shadow-xs shrink-0 whitespace-nowrap"
              title="Toggle Language / भाषा बदलें"
            >
              <Languages className="w-4 h-4 text-brand-600 shrink-0" />
              <span className={language === 'en' ? 'text-brand-700 font-bold' : 'text-slate-500'}>EN</span>
              <span className="text-slate-300">/</span>
              <span className={language === 'hi' ? 'text-brand-700 font-bold' : 'text-slate-500'}>हिन्दी</span>
            </button>

            {/* Reactive Network Status Indicator */}
            <div className="shrink-0">
              <NetworkIndicator compact={true} />
            </div>

            {/* Rural Mode Toggle */}
            <button
              type="button"
              onClick={toggleRuralMode}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-xs font-bold transition shadow-xs shrink-0 whitespace-nowrap ${
                ruralMode
                  ? 'bg-brand-600 text-white border-brand-500 shadow-sm'
                  : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
              }`}
              title="Toggle Rural Mode (Large Touch Targets & Simplified Guidance)"
            >
              <Smartphone className="w-3.5 h-3.5 shrink-0" />
              <span className="hidden md:inline">{t('ruralMode') || 'Rural Mode'}</span>
              {ruralMode && <span className="w-1.5 h-1.5 rounded-full bg-white ml-0.5"></span>}
            </button>

            {/* Role Switcher Dropdown */}
            <div className="relative shrink-0">
              <button
                type="button"
                onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
                className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 text-xs font-medium text-slate-700 shadow-xs transition shrink-0 whitespace-nowrap"
              >
                <div className="w-2 h-2 rounded-full bg-brand-500 shrink-0"></div>
                <span className="max-w-[100px] sm:max-w-[130px] lg:max-w-none truncate font-semibold">{getRoleLabel()}</span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              </button>

              {roleDropdownOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white border border-slate-200 shadow-xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
                  <div className="px-3 py-1.5 border-b border-slate-100">
                    <p className="text-[11px] font-semibold uppercase text-slate-400">{t('roleSwitch')}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRoleChange('health_worker')}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2 hover:bg-slate-50 transition ${
                      userRole === 'health_worker' ? 'text-brand-700 font-bold bg-brand-50/50' : 'text-slate-700'
                    }`}
                  >
                    <UserCheck className="w-4 h-4 text-brand-600" />
                    <span>{t('roleWorker')}</span>
                  </button>
                  <button
                    type="button"
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
              className="hidden sm:inline-flex items-center justify-center px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-lg transition shrink-0 whitespace-nowrap"
            >
              {t('navLogout')}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

