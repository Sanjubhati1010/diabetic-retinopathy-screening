import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  Settings,
  Languages,
  Wifi,
  WifiOff,
  RefreshCw,
  Eye,
  CheckCircle2,
  Download,
  Building,
  Sliders,
  Sun,
  Shield,
} from 'lucide-react';

export const SettingsPage = () => {
  const { language, setLanguage, t } = useLanguage();
  const {
    isOnline,
    setIsOnline,
    offlineSyncCount,
    syncOfflineQueue,
    highContrast,
    setHighContrast,
    largeText,
    setLargeText,
  } = useApp();

  const [phcName, setPhcName] = useState('Primary Health Center Rampur (Sector 4)');
  const [defaultCamp, setDefaultCamp] = useState('Rampur Gram Panchayat Mela');
  const [syncing, setSyncing] = useState(false);
  const [saveToast, setSaveToast] = useState(false);

  const handleSyncNow = () => {
    setSyncing(true);
    setTimeout(() => {
      syncOfflineQueue();
      setSyncing(false);
    }, 1200);
  };

  const handleSaveSettings = (e) => {
    e.preventDefault();
    setSaveToast(true);
    setTimeout(() => setSaveToast(false), 2500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 flex items-center gap-2">
          <Settings className="w-6 h-6 text-brand-600" />
          <span>{t('settingsTitle')}</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">{t('settingsSub')}</p>
      </div>

      <form onSubmit={handleSaveSettings} className="space-y-6">
        {/* Section 1: Language & Locale */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Languages className="w-4 h-4 text-brand-600" />
            <span>{t('langSection')}</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setLanguage('en')}
              className={`p-4 rounded-2xl border text-left transition flex items-center justify-between ${
                language === 'en'
                  ? 'bg-brand-50 border-brand-500 text-brand-950 ring-2 ring-brand-500/20'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div>
                <p className="text-xs font-bold">English (UK / Clinical)</p>
                <p className="text-[11px] text-slate-500">Standard English interface</p>
              </div>
              {language === 'en' && <CheckCircle2 className="w-5 h-5 text-brand-600 shrink-0" />}
            </button>

            <button
              type="button"
              onClick={() => setLanguage('hi')}
              className={`p-4 rounded-2xl border text-left transition flex items-center justify-between ${
                language === 'hi'
                  ? 'bg-brand-50 border-brand-500 text-brand-950 ring-2 ring-brand-500/20'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div>
                <p className="text-xs font-bold">हिन्दी (Hindi - Devanagari)</p>
                <p className="text-[11px] text-slate-500">ग्रामीण स्वास्थ्य कार्यकर्ताओं हेतु</p>
              </div>
              {language === 'hi' && <CheckCircle2 className="w-5 h-5 text-brand-600 shrink-0" />}
            </button>
          </div>
        </div>

        {/* Section 2: Rural Offline Sync & Cache Engine */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Wifi className="w-4 h-4 text-teal-600" />
            <span>{t('offlineSyncSection')}</span>
          </h2>

          <p className="text-xs text-slate-600 leading-relaxed">{t('offlineDesc')}</p>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    isOnline ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                />
                <p className="text-xs font-bold text-slate-900">
                  {isOnline ? 'Online (Connected to District Hospital Gateway)' : 'Offline Mode'}
                </p>
              </div>
              <p className="text-[11px] text-slate-500">
                {offlineSyncCount === 0 ? t('syncedAll') : `${offlineSyncCount} records awaiting sync`}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsOnline(!isOnline)}
                className="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-bold text-slate-700 transition"
              >
                {isOnline ? 'Simulate Offline Mode' : 'Restore Online Mode'}
              </button>

              <button
                type="button"
                onClick={handleSyncNow}
                disabled={syncing || offlineSyncCount === 0}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-sm transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                <span>{syncing ? 'Syncing...' : t('btnForceSync')}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Section 3: Camp & Facility Setup */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Building className="w-4 h-4 text-indigo-600" />
            <span>{t('campConfigSection')}</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('centerName')}</label>
              <input
                type="text"
                value={phcName}
                onChange={(e) => setPhcName(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {t('defaultVillage')}
              </label>
              <input
                type="text"
                value={defaultCamp}
                onChange={(e) => setDefaultCamp(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
          </div>
        </div>

        {/* Section 4: Accessibility & Display */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Sun className="w-4 h-4 text-amber-600" />
            <span>{t('accessibilitySection')}</span>
          </h2>

          <div className="space-y-3">
            <label className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-200 cursor-pointer">
              <div>
                <p className="text-xs font-bold text-slate-900">{t('highContrastMode')}</p>
                <p className="text-[11px] text-slate-500">
                  Boosts contrast & saturation for outdoor bright sunlight screening camps
                </p>
              </div>
              <input
                type="checkbox"
                checked={highContrast}
                onChange={(e) => setHighContrast(e.target.checked)}
                className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-4 h-4"
              />
            </label>

            <label className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-200 cursor-pointer">
              <div>
                <p className="text-xs font-bold text-slate-900">{t('largeTextMode')}</p>
                <p className="text-[11px] text-slate-500">
                  Enlarges baseline font size for rapid visual readability by field staff
                </p>
              </div>
              <input
                type="checkbox"
                checked={largeText}
                onChange={(e) => setLargeText(e.target.checked)}
                className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-4 h-4"
              />
            </label>
          </div>
        </div>

        {/* Section 5: Phase 12 WhatsApp Health Worker Profile & Opt-in Consent */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-emerald-200 shadow-card space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <span className="p-1.5 rounded-lg bg-emerald-100 text-emerald-700">📱</span>
            <span>{t('whatsappConfigSection') || 'WhatsApp Health Worker Profile & Opt-In Settings'}</span>
          </h2>

          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Registered Health Worker Name
                </label>
                <input
                  type="text"
                  defaultValue="Pooja Sharma (ASHA Worker)"
                  readOnly
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 font-semibold"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">
                  Registered WhatsApp Mobile (+91)
                </label>
                <input
                  type="text"
                  defaultValue="+91 98765 43210"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white font-mono font-bold text-slate-900 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <label className="flex items-center justify-between p-4 rounded-2xl bg-emerald-50/80 border border-emerald-200 cursor-pointer">
              <div className="pr-4">
                <p className="text-xs font-bold text-emerald-950">
                  {t('whatsappOptInConsent') || 'WhatsApp Clinical Report Opt-In Consent'}
                </p>
                <p className="text-[11px] text-emerald-800/80 mt-0.5">
                  {t('whatsappOptInDesc') || 'Allow clinical screening reports to be delivered directly to the health worker\'s registered WhatsApp number.'}
                </p>
              </div>
              <input
                type="checkbox"
                defaultChecked={true}
                className="rounded border-emerald-300 text-emerald-600 focus:ring-emerald-500 w-5 h-5 cursor-pointer shrink-0"
              />
            </label>
          </div>
        </div>

        {/* Action Save Bar */}
        <div className="flex items-center justify-between pt-2">
          {saveToast ? (
            <span className="text-xs font-bold text-emerald-700 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Settings configuration saved successfully!</span>
            </span>
          ) : (
            <span />
          )}

          <button
            type="submit"
            className="px-6 py-3 rounded-2xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-glow transition transform hover:-translate-y-0.5"
          >
            {t('btnSave')} Configuration
          </button>
        </div>
      </form>
    </div>
  );
};
