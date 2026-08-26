import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import { SeverityBadge, UrgencyBadge } from '../components/common/SeverityBadge';
import { EmptyState } from '../components/common/EmptyState';
import {
  Users,
  Search,
  UserPlus,
  Filter,
  Eye,
  ChevronRight,
  Sparkles,
  Phone,
  MapPin,
  Calendar,
} from 'lucide-react';

export const PatientListPage = () => {
  const { t } = useLanguage();
  const { patients, setActiveScreening } = useApp();
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVillage, setSelectedVillage] = useState('all');
  const [selectedRisk, setSelectedRisk] = useState('all');

  const villages = ['all', ...new Set(patients.map((p) => p.village))];

  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.phone.includes(searchQuery) ||
      (p.abhaId && p.abhaId.includes(searchQuery)) ||
      p.village.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesVillage = selectedVillage === 'all' || p.village === selectedVillage;
    const matchesRisk = selectedRisk === 'all' || p.latestStatus === selectedRisk;

    return matchesSearch && matchesVillage && matchesRisk;
  });

  const handleStartScreeningForPatient = (patient) => {
    setActiveScreening((prev) => ({
      ...prev,
      patientId: patient.id,
      patientName: patient.name,
    }));
    navigate('/screenings/upload');
  };

  return (
    <div className="space-y-6">
      {/* Demo Data Disclaimer */}
      <div className="flex items-center gap-2 p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
        <Users className="w-4 h-4 text-amber-600 shrink-0" />
        <span>DEMO DATA — NOT REAL MEDICAL RESULTS</span>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">{t('patientListTitle')}</h1>
          <p className="text-xs text-slate-500">{t('patientListSub')}</p>
        </div>
        <Link
          to="/patients/register"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-glow transition"
        >
          <UserPlus className="w-4 h-4" />
          <span>{t('btnRegisterPatient')}</span>
        </Link>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white rounded-3xl p-4 sm:p-5 border border-slate-200 shadow-card space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          {/* Search Box */}
          <div className="sm:col-span-6 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('searchPatientPlaceholder')}
              className="w-full pl-9 pr-4 py-2.5 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
            />
          </div>

          {/* Village Filter */}
          <div className="sm:col-span-3">
            <select
              value={selectedVillage}
              onChange={(e) => setSelectedVillage(e.target.value)}
              className="w-full py-2.5 px-3 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white font-medium text-slate-700"
            >
              <option value="all">All Villages ({patients.length})</option>
              {villages
                .filter((v) => v !== 'all')
                .map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
            </select>
          </div>

          {/* Risk Level Filter */}
          <div className="sm:col-span-3">
            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="w-full py-2.5 px-3 text-xs rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white font-medium text-slate-700"
            >
              <option value="all">All DR Severity Grades</option>
              <option value="dr0">DR 0 (No Retinopathy)</option>
              <option value="dr1">DR 1 (Mild NPDR)</option>
              <option value="dr2">DR 2 (Moderate NPDR)</option>
              <option value="dr3">DR 3 (Severe NPDR)</option>
              <option value="dr4">DR 4 (Proliferative DR)</option>
              <option value="drUncertain">Pending Screening</option>
            </select>
          </div>
        </div>
      </div>

      {/* Patient Table */}
      {filteredPatients.length === 0 ? (
        <EmptyState
          icon={Users}
          title={t('noDataFound')}
          description="No registered patients match your search criteria. Try modifying your search or add a new patient."
          actionLabel={t('btnRegisterPatient')}
          onAction={() => navigate('/patients/register')}
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-4">{t('colName')}</th>
                  <th className="py-3.5 px-4">{t('colAgeGender')}</th>
                  <th className="py-3.5 px-4">{t('colVillage')}</th>
                  <th className="py-3.5 px-4">{t('colDiabetes')}</th>
                  <th className="py-3.5 px-4">{t('colLastScreened')}</th>
                  <th className="py-3.5 px-4">{t('colStatus')}</th>
                  <th className="py-3.5 px-4 text-right">{t('colActions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {filteredPatients.map((patient) => (
                  <tr key={patient.id} className="hover:bg-slate-50 transition">
                    <td className="py-4 px-4">
                      <div className="font-bold text-slate-900">{patient.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {patient.abhaId || patient.id}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="capitalize">
                        {patient.age}y / {patient.gender === 'male' ? 'M' : 'F'}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-slate-800">{patient.village}</span>
                      <div className="text-[11px] text-slate-400">{patient.district}</div>
                    </td>
                    <td className="py-4 px-4">
                      <div>{patient.diabetesDuration} yrs duration</div>
                      <div className="text-[11px] text-slate-500 font-semibold">
                        HbA1c: {patient.lastHba1c}%
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-slate-700">{patient.lastScreened}</span>
                    </td>
                    <td className="py-4 px-4">
                      <SeverityBadge severity={patient.latestStatus} size="sm" />
                    </td>
                    <td className="py-4 px-4 text-right space-x-1.5 whitespace-nowrap">
                      <button
                        onClick={() => handleStartScreeningForPatient(patient)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-sm transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>{t('btnStartScreen')}</span>
                      </button>
                      <Link
                        to={`/patients/${patient.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition"
                      >
                        <span>{t('btnProfile')}</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
