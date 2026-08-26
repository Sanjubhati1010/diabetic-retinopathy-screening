import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  PlusCircle,
  Users,
  Camera,
  MapPin,
  Eye,
  ArrowRight,
  UserPlus,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export const NewScreeningPage = () => {
  const { t } = useLanguage();
  const { patients, activeScreening, setActiveScreening } = useApp();
  const navigate = useNavigate();

  const [selectedPatientId, setSelectedPatientId] = useState(
    activeScreening.patientId || (patients[0] ? patients[0].id : '')
  );
  const [campLocation, setCampLocation] = useState(
    activeScreening.campLocation || 'Rampur PHC Community Camp'
  );
  const [cameraModel, setCameraModel] = useState(
    activeScreening.cameraModel || 'Forus 3nethra Classic HD'
  );
  const [dilation, setDilation] = useState(activeScreening.dilation || 'undilated');
  const [screenerName, setScreenerName] = useState('Pooja Sharma (ASHA Worker)');

  const selectedPatient = patients.find((p) => p.id === selectedPatientId) || patients[0];

  const handleProceed = (e) => {
    e.preventDefault();
    setActiveScreening((prev) => ({
      ...prev,
      patientId: selectedPatientId,
      patientName: selectedPatient ? selectedPatient.name : 'Unknown Patient',
      campLocation,
      cameraModel,
      dilation,
      screenerName,
    }));
    navigate('/screenings/upload');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Wizard Step Tracker */}
      <div className="bg-white rounded-3xl p-4 sm:p-6 border border-slate-200 shadow-card">
        <div className="grid grid-cols-3 gap-2 text-center text-xs font-bold">
          <div className="p-3 rounded-2xl bg-brand-50 text-brand-700 border border-brand-200 flex items-center justify-center gap-2">
            <span className="w-5 h-5 rounded-full bg-brand-600 text-white flex items-center justify-center text-[10px]">
              1
            </span>
            <span>{t('stepSelectPatient')}</span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 text-slate-400 border border-slate-200 flex items-center justify-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center text-[10px]">
              2
            </span>
            <span>{t('stepUploadImages')}</span>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 text-slate-400 border border-slate-200 flex items-center justify-center gap-2">
            <span className="w-5 h-5 rounded-full bg-slate-300 text-slate-700 flex items-center justify-center text-[10px]">
              3
            </span>
            <span>{t('stepRunAi')}</span>
          </div>
        </div>
      </div>

      {/* Main Configuration Card */}
      <form onSubmit={handleProceed} className="space-y-6">
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-card space-y-6">
          <div>
            <h1 className="text-xl font-extrabold text-slate-900">{t('screeningWizardTitle')}</h1>
            <p className="text-xs text-slate-500">{t('screeningWizardSub')}</p>
          </div>

          {/* Patient Selection Box */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                {t('selectExistingPatient')} *
              </label>
              <Link
                to="/patients/register"
                className="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>+ Register New Patient</span>
              </Link>
            </div>

            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="w-full text-xs py-3 px-3.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white font-semibold text-slate-800"
            >
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.age}y, {p.gender}) — {p.village} [ABHA: {p.abhaId || p.id}]
                </option>
              ))}
            </select>

            {/* Selected Patient Mini Card */}
            {selectedPatient && (
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div>
                  <p className="font-bold text-slate-900">{selectedPatient.name}</p>
                  <p className="text-slate-500 text-[11px]">
                    Diabetes: {selectedPatient.diabetesDuration} yrs • HbA1c: {selectedPatient.lastHba1c}% • Visual Acuity (OD: {selectedPatient.visualAcuityOD}, OS: {selectedPatient.visualAcuityOS})
                  </p>
                </div>
                <div className="text-[11px] text-slate-500 font-medium">
                  Village: <strong>{selectedPatient.village}</strong>
                </div>
              </div>
            )}
          </div>

          {/* Camp & Hardware Settings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-100">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {t('campLocation')}
              </label>
              <input
                type="text"
                required
                value={campLocation}
                onChange={(e) => setCampLocation(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {t('cameraDevice')}
              </label>
              <select
                value={cameraModel}
                onChange={(e) => setCameraModel(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white"
              >
                <option value="Forus 3nethra Classic HD">Forus 3nethra Classic HD (Portable)</option>
                <option value="Remidio NM-FOP 2.0 Smartphone Fundus">Remidio NM-FOP 2.0 (Mobile)</option>
                <option value="Topcon TRC-NW400 Robotic">Topcon TRC-NW400 Robotic</option>
                <option value="Zeiss Visuscout 100 Handheld">Zeiss Visuscout 100 Handheld</option>
                <option value="Volk iNview Smartphone Adapter">Volk iNview Smartphone Adapter</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {t('dilationStatus')}
              </label>
              <select
                value={dilation}
                onChange={(e) => setDilation(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white font-medium"
              >
                <option value="undilated">{t('undilated')}</option>
                <option value="dilated">{t('dilated')}</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Screener / Health Worker Name
              </label>
              <input
                type="text"
                required
                value={screenerName}
                onChange={(e) => setScreenerName(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-end">
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-glow transition transform hover:-translate-y-0.5"
          >
            <span>Proceed to Retinal Image Capture</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
