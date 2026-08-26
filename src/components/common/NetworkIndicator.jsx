import React, { useState } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useApp } from '../../context/AppContext';
import {
  Wifi,
  WifiOff,
  Activity,
  RefreshCw,
  HelpCircle,
  Database,
  CloudUpload,
  CheckCircle2,
  AlertTriangle,
  X,
} from 'lucide-react';

export const NetworkIndicator = ({ compact = false }) => {
  const { t } = useLanguage();
  const { networkState, setIsOnline, offlineSyncCount, pendingSyncQueue, syncPendingQueue } = useApp();
  const [modalOpen, setModalOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const { status, effectiveType, downlink, rtt, isOnline } = networkState;

  const handleSyncNow = () => {
    setIsSyncing(true);
    setTimeout(() => {
      syncPendingQueue();
      setIsSyncing(false);
    }, 800);
  };

  const getStatusBadge = () => {
    if (!isOnline || status === 'offline') {
      return {
        bg: 'bg-rose-50 border-rose-300 text-rose-800',
        dot: 'bg-rose-500',
        icon: <WifiOff className="w-3.5 h-3.5 text-rose-600 shrink-0" />,
        label: t('netOffline') || 'Offline',
      };
    }
    if (status === 'weak') {
      return {
        bg: 'bg-amber-50 border-amber-300 text-amber-900',
        dot: 'bg-amber-500',
        icon: <Activity className="w-3.5 h-3.5 text-amber-600 shrink-0" />,
        label: `${t('netWeak') || 'Weak Connection'} (${effectiveType?.toUpperCase() || '2G'})`,
      };
    }
    if (status === 'connected') {
      return {
        bg: 'bg-emerald-50 border-emerald-300 text-emerald-800',
        dot: 'bg-emerald-500',
        icon: <Wifi className="w-3.5 h-3.5 text-emerald-600 shrink-0" />,
        label: t('netConnected') || 'Connected',
      };
    }
    return {
      bg: 'bg-slate-50 border-slate-300 text-slate-700',
      dot: 'bg-slate-400',
      icon: <HelpCircle className="w-3.5 h-3.5 text-slate-500 shrink-0" />,
      label: t('netUnavailable') || 'Status Unavailable',
    };
  };

  const badge = getStatusBadge();

  return (
    <>
      <button
        type="button"
        onClick={() => setModalOpen(true)}
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold transition shadow-sm hover:shadow ${badge.bg}`}
        title="View Connectivity & Offline Sync Details"
        aria-label={`Network status: ${badge.label}`}
      >
        <span className={`w-2 h-2 rounded-full ${badge.dot} ${status === 'connected' ? 'animate-pulse' : ''}`}></span>
        {badge.icon}
        <span className={compact ? 'hidden md:inline' : 'inline'}>{badge.label}</span>
        {offlineSyncCount > 0 && (
          <span className="ml-1 px-1.5 py-0.2 rounded-full bg-slate-900 text-white text-[10px] font-mono">
            {offlineSyncCount}
          </span>
        )}
      </button>

      {/* Connectivity & Sync Status Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-md w-full p-6 space-y-5 animate-in fade-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-brand-50 border border-brand-200 text-brand-700">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-slate-900">
                    {t('dashNetStatus') || 'Network & Sync Status'}
                  </h3>
                  <p className="text-xs text-slate-500 font-medium">
                    Rural Connectivity Health & Pending Queue
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="p-1.5 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Network Metrics */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-600 font-medium">Connectivity State:</span>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-bold border ${badge.bg}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`}></span>
                  {badge.label}
                </span>
              </div>
              {effectiveType && (
                <div className="flex items-center justify-between text-slate-600">
                  <span>Network Technology:</span>
                  <span className="font-mono font-bold text-slate-900 uppercase">{effectiveType}</span>
                </div>
              )}
              {downlink && (
                <div className="flex items-center justify-between text-slate-600">
                  <span>Estimated Speed:</span>
                  <span className="font-mono font-bold text-slate-900">{downlink} Mbps</span>
                </div>
              )}
              {rtt && (
                <div className="flex items-center justify-between text-slate-600">
                  <span>Round-Trip Latency:</span>
                  <span className="font-mono font-bold text-slate-900">{rtt} ms</span>
                </div>
              )}
            </div>

            {/* Offline Sync Architecture Notice */}
            <div className="p-3.5 rounded-2xl bg-blue-50/80 border border-blue-200 text-blue-900 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <Database className="w-4 h-4 text-blue-600" />
                <span>{t('syncQueueTitle') || 'Offline Sync Queue'}</span>
              </div>
              <p className="text-[11px] text-blue-800 leading-relaxed">
                Patient drafts and offline records are stored locally. 
                <strong className="block mt-0.5 text-blue-950">
                  * Note: AI model screening requires active connection to the AI screening service.
                </strong>
              </p>
            </div>

            {/* Sync Queue Count & Action */}
            <div className="flex items-center justify-between p-3 rounded-2xl border border-slate-200 bg-white">
              <div>
                <p className="text-xs font-bold text-slate-800">
                  {pendingSyncQueue.length} {pendingSyncQueue.length === 1 ? 'Record' : 'Records'} in Queue
                </p>
                <p className="text-[11px] text-slate-500">
                  {offlineSyncCount} Pending Synchronization
                </p>
              </div>
              <button
                type="button"
                onClick={handleSyncNow}
                disabled={isSyncing || offlineSyncCount === 0}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-xs font-bold shadow-sm transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                <span>{isSyncing ? 'Syncing...' : t('btnSyncNow') || 'Sync All'}</span>
              </button>
            </div>

            {/* Toggle Online Simulator for Field Testing */}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500 font-medium">Field Test Offline Simulator:</span>
              <button
                type="button"
                onClick={() => setIsOnline(!isOnline)}
                className="px-2.5 py-1 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700 font-bold transition"
              >
                {isOnline ? 'Simulate Offline' : 'Restore Online'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
