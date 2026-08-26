import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import {
  LayoutDashboard,
  Users,
  UserPlus,
  PlusCircle,
  Upload,
  Cpu,
  FileCheck,
  Eye,
  History,
  FileText,
  Stethoscope,
  BarChart3,
  Settings,
  Sparkles,
  Home,
  X,
  Radio,
} from 'lucide-react';

export const Sidebar = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  const { userRole, screenings } = useApp();
  const location = useLocation();

  const pendingDoctorCount = screenings.filter((s) => s.doctorStatus === 'pending').length;

  const navGroups = [
    {
      groupTitle: 'Overview',
      items: [
        { name: t('navLanding'), path: '/', icon: Home },
        { name: t('navDashboard'), path: '/dashboard', icon: LayoutDashboard },
        { name: t('navPatients'), path: '/patients', icon: Users },
        { name: t('btnRegisterPatient'), path: '/patients/register', icon: UserPlus },
      ],
    },
    {
      groupTitle: 'Screening & AI Workflow',
      items: [
        { name: t('navNewScreening'), path: '/screenings/new', icon: PlusCircle, highlight: true },
        { name: t('navUpload'), path: '/screenings/upload', icon: Upload },
        { name: t('navAnalysis'), path: '/screenings/analysis', icon: Cpu },
        {
          name: t('navResults'),
          path: `/screenings/${screenings[0]?.id || 'SCR-2026-0991'}/result`,
          icon: FileCheck,
        },
        {
          name: t('navGradCam'),
          path: `/screenings/${screenings[0]?.id || 'SCR-2026-0991'}/xai`,
          icon: Eye,
          badge: 'XAI',
        },
        { name: t('navHistory'), path: '/history', icon: History },
        {
          name: t('navReports'),
          path: `/screenings/${screenings[0]?.id || 'SCR-2026-0991'}/report`,
          icon: FileText,
        },
      ],
    },
    {
      groupTitle: 'Tele-Ophthalmology & Insights',
      items: [
        {
          name: t('navDoctor'),
          path: '/doctor',
          icon: Stethoscope,
          badge: pendingDoctorCount > 0 ? String(pendingDoctorCount) : null,
          badgeColor: 'bg-amber-100 text-amber-800',
        },
        { name: t('navAnalytics'), path: '/analytics', icon: BarChart3 },
        { name: t('navSettings'), path: '/settings', icon: Settings },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Sidebar Drawer */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-white border-r border-slate-200/80 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header in sidebar */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white shadow-glow">
              <Eye className="w-4 h-4" />
            </div>
            <span className="font-bold text-slate-800 text-xs tracking-tight">Rural DR Screening</span>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Link Groups */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navGroups.map((group, gIdx) => (
            <div key={gIdx} className="space-y-1">
              <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                {group.groupTitle}
              </p>
              <div className="space-y-1 mt-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive =
                    item.path === '/'
                      ? location.pathname === '/'
                      : location.pathname.startsWith(item.path.split('/')[1] ? `/${item.path.split('/')[1]}` : item.path) &&
                        (item.path.includes('xai') ? location.pathname.includes('xai') : true) &&
                        (item.path.includes('report') ? location.pathname.includes('report') : true) &&
                        (item.path.includes('result') ? location.pathname.includes('result') : true);

                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={({ isActive: exactActive }) => {
                        const active = item.path === '/' ? exactActive : location.pathname === item.path;
                        return `group flex items-center justify-between px-3 py-2 text-xs font-semibold rounded-xl transition-all ${
                          active
                            ? 'bg-brand-600 text-white shadow-glow'
                            : item.highlight
                            ? 'bg-brand-50 text-brand-700 hover:bg-brand-100 font-bold border border-brand-200/60'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                        }`;
                      }}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />
                        <span className="truncate">{item.name}</span>
                      </div>
                      {item.badge && (
                        <span
                          className={`text-[10px] font-extrabold px-1.5 py-0.5 rounded-full ${
                            item.badgeColor || 'bg-brand-100 text-brand-800'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Sidebar Footer info */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2 p-2 rounded-xl bg-white border border-slate-200/70 shadow-sm">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-bold text-slate-800 truncate">Rampur Health Center</p>
              <p className="text-[10px] text-slate-500">ASHA Unit • Online</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
