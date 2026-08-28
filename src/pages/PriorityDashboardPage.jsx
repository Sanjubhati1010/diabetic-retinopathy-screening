import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { PriorityStatCards } from '../components/priority/PriorityStatCards';
import { PriorityQueueTable } from '../components/priority/PriorityQueueTable';
import { WhyPriorityDrawer } from '../components/priority/WhyPriorityDrawer';
import { PriorityCaseDetailModal } from '../components/priority/PriorityCaseDetailModal';
import { getPriorityQueue, getPriorityStats } from '../services/api';
import { Sparkles, Activity, ShieldCheck, RefreshCw, AlertCircle, Info, Stethoscope, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const PriorityDashboardPage = () => {
  const { t } = useLanguage();
  const { screenings, patients } = useApp();

  const [stats, setStats] = useState({
    total_screened: 0,
    urgent_count: 0,
    priority_count: 0,
    routine_count: 0,
    verification_required_count: 0,
    recapture_required_count: 0,
  });
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState('all');
  const [sortBy, setSortBy] = useState('priority');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWhyItem, setSelectedWhyItem] = useState(null);
  const [selectedCaseItem, setSelectedCaseItem] = useState(null);

  // Fetch priority queue from backend or local fallback
  const fetchPriorityData = async () => {
    setLoading(true);
    try {
      const qRes = await getPriorityQueue({
        filter: filterLevel,
        search: searchQuery,
        sort_by: sortBy,
        sort_order: 'desc',
      });
      if (qRes && qRes.queue) {
        setQueue(qRes.queue);
        setStats({
          total_screened: qRes.total || qRes.queue.length,
          urgent_count: qRes.urgent_count || 0,
          priority_count: qRes.priority_count || 0,
          routine_count: qRes.routine_count || 0,
          verification_required_count: qRes.verification_required_count || 0,
          recapture_required_count: qRes.recapture_required_count || 0,
        });
      }
    } catch (err) {
      console.error('Error fetching priority data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPriorityData();
  }, [filterLevel, sortBy, searchQuery, screenings]);

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Top Banner Header */}
      <div className="rounded-3xl p-6 sm:p-7 bg-gradient-to-r from-slate-900 via-brand-950 to-slate-900 text-white shadow-lg border border-slate-800 relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-400/30 text-xs font-bold">
              <Activity className="w-3.5 h-3.5 text-brand-400" />
              <span>Clinical Decision-Support & Triage Module</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              Rural Care Priority Engine
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Prioritizing specialist attention using explainable screening evidence, longitudinal change detection, and clinical risk context.
            </p>
          </div>

          {/* Direct Actions */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={fetchPriorityData}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs border border-white/20 transition"
              title="Refresh Priority Calculation"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Recalculate</span>
            </button>
            <Link
              to="/doctor"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-400 text-slate-950 font-extrabold text-xs sm:text-sm hover:bg-brand-300 shadow-glow transition"
            >
              <Stethoscope className="w-4 h-4" />
              <span>Doctor Review Queue</span>
            </Link>
          </div>
        </div>

        {/* Decorative background circle */}
        <div className="absolute -right-16 -bottom-16 w-64 h-64 rounded-full bg-brand-500/10 blur-2xl pointer-events-none" />
      </div>

      {/* Clinical Disclaimer Banner */}
      <div className="flex items-start gap-2.5 p-3.5 rounded-2xl bg-amber-50/80 border border-amber-200/80 text-amber-900 text-xs leading-relaxed">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <p>
          <strong>Clinical Decision Support Notice:</strong> Priority levels are deterministic, rule-driven recommendations based on available screening evidence. This engine does not diagnose or replace clinical judgment. Final triage and treatment decisions remain exclusively with the consulting physician.
        </p>
      </div>

      {/* Priority Summary Cards */}
      <PriorityStatCards
        stats={stats}
        loading={loading}
        onRefresh={fetchPriorityData}
      />

      {/* Priority Queue Table */}
      <PriorityQueueTable
        queue={queue}
        loading={loading}
        filterLevel={filterLevel}
        onFilterChange={setFilterLevel}
        sortBy={sortBy}
        onSortChange={setSortBy}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onOpenWhyPriority={(item) => setSelectedWhyItem(item)}
        onViewCase={(item) => setSelectedCaseItem(item)}
      />

      {/* "Why This Priority?" Explanation Drawer / Modal */}
      <WhyPriorityDrawer
        item={selectedWhyItem}
        isOpen={Boolean(selectedWhyItem)}
        onClose={() => setSelectedWhyItem(null)}
        onViewCase={(item) => setSelectedCaseItem(item)}
      />

      {/* Full Patient Case Detail Modal */}
      <PriorityCaseDetailModal
        item={selectedCaseItem}
        isOpen={Boolean(selectedCaseItem)}
        onClose={() => setSelectedCaseItem(null)}
        onOpenWhyPriority={(item) => setSelectedWhyItem(item)}
      />
    </div>
  );
};

export default PriorityDashboardPage;
