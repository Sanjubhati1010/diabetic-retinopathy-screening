import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { useApp } from '../context/AppContext';
import {
  UserPlus,
  ArrowRight,
  Shield,
  Activity,
  Eye,
  CheckCircle2,
  Calendar,
  Phone,
  MapPin,
  FileCheck,
} from 'lucide-react';

export const PatientRegisterPage = () => {
  const { t } = useLanguage();
  const { addPatient, setActiveScreening } = useApp();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    abhaId: '',
    age: '',
    gender: 'male',
    phone: '',
    village: 'Rampur Gram Panchayat',
    district: 'Varanasi',
    diabetesDuration: '5',
    lastHba1c: '7.8',
    insulinUse: false,
    visualAcuityOD: '6/12',
    visualAcuityOS: '6/18',
    symptoms: ['blurredVision'],
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCheckboxToggle = (sym) => {
    setFormData((prev) => {
      const current = prev.symptoms;
      if (current.includes(sym)) {
        return { ...prev, symptoms: current.filter((s) => s !== sym) };
      } else {
        return { ...prev, symptoms: [...current, sym] };
      }
    });
  };

  const handleSubmit = (e, andStartScreening = true) => {
    e.preventDefault();
    setIsSubmitting(true);

    const newPatient = addPatient({
      ...formData,
      age: Number(formData.age) || 50,
      diabetesDuration: Number(formData.diabetesDuration) || 5,
      lastHba1c: Number(formData.lastHba1c) || 7.5,
    });

    setActiveScreening((prev) => ({
      ...prev,
      patientId: newPatient.id,
      patientName: newPatient.name,
    }));

    setTimeout(() => {
      setIsSubmitting(false);
      if (andStartScreening) {
        navigate('/screenings/upload');
      } else {
        navigate('/patients');
      }
    }, 400);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">{t('regTitle')}</h1>
          <p className="text-xs text-slate-500">{t('regSubtitle')}</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-brand-50 border border-brand-200 text-brand-800 text-xs font-semibold">
          <Shield className="w-4 h-4 text-brand-600" />
          <span>ABHA / Ayushman Bharat Compatible</span>
        </div>
      </div>

      <form onSubmit={(e) => handleSubmit(e, true)} className="space-y-6">
        {/* Section 1: Demographics */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <UserPlus className="w-4 h-4 text-brand-600" />
            <span>1. Patient Demographics & Identification</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('fullName')} *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Ramesh Kumar Verma"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('abhaId')}</label>
              <input
                type="text"
                value={formData.abhaId}
                onChange={(e) => setFormData({ ...formData, abhaId: e.target.value })}
                placeholder="91-XXXX-XXXX-XXXX"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('age')} *</label>
              <input
                type="number"
                required
                min="1"
                max="120"
                value={formData.age}
                onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                placeholder="55"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('gender')} *</label>
              <select
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white"
              >
                <option value="male">{t('male')}</option>
                <option value="female">{t('female')}</option>
                <option value="other">{t('other')}</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('phone')} *</label>
              <input
                type="tel"
                required
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+91 98765 43210"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('village')} *</label>
              <input
                type="text"
                required
                value={formData.village}
                onChange={(e) => setFormData({ ...formData, village: e.target.value })}
                placeholder="e.g. Rampur Gram Panchayat, Ward 3"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('district')} *</label>
              <input
                type="text"
                required
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                placeholder="e.g. Varanasi"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Clinical Diabetes & Visual History */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-card space-y-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
            <Activity className="w-4 h-4 text-brand-600" />
            <span>2. Diabetes History & Visual Acuity</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {t('diabetesDuration')}
              </label>
              <input
                type="number"
                min="0"
                max="60"
                value={formData.diabetesDuration}
                onChange={(e) => setFormData({ ...formData, diabetesDuration: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">{t('lastHba1c')}</label>
              <input
                type="number"
                step="0.1"
                min="4"
                max="20"
                value={formData.lastHba1c}
                onChange={(e) => setFormData({ ...formData, lastHba1c: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500"
              />
            </div>

            <div className="flex items-center pt-5">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={formData.insulinUse}
                  onChange={(e) => setFormData({ ...formData, insulinUse: e.target.checked })}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-4 h-4"
                />
                <span className="text-xs font-bold text-slate-700">{t('insulinUse')}</span>
              </label>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {t('visualAcuityRight')}
              </label>
              <select
                value={formData.visualAcuityOD}
                onChange={(e) => setFormData({ ...formData, visualAcuityOD: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white"
              >
                <option value="6/6">6/6 (Normal 20/20)</option>
                <option value="6/9">6/9</option>
                <option value="6/12">6/12</option>
                <option value="6/18">6/18</option>
                <option value="6/24">6/24</option>
                <option value="6/36">6/36</option>
                <option value="6/60">6/60</option>
                <option value="CF">Counting Fingers (CF)</option>
                <option value="HM">Hand Movements (HM)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {t('visualAcuityLeft')}
              </label>
              <select
                value={formData.visualAcuityOS}
                onChange={(e) => setFormData({ ...formData, visualAcuityOS: e.target.value })}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-brand-500 focus:border-brand-500 bg-white"
              >
                <option value="6/6">6/6 (Normal 20/20)</option>
                <option value="6/9">6/9</option>
                <option value="6/12">6/12</option>
                <option value="6/18">6/18</option>
                <option value="6/24">6/24</option>
                <option value="6/36">6/36</option>
                <option value="6/60">6/60</option>
                <option value="CF">Counting Fingers (CF)</option>
                <option value="HM">Hand Movements (HM)</option>
              </select>
            </div>
          </div>

          {/* Eye Symptoms Checklist */}
          <div className="pt-2">
            <label className="block text-xs font-bold text-slate-700 mb-2">{t('symptoms')}</label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {[
                { id: 'blurredVision', label: t('blurredVision') },
                { id: 'floaters', label: t('floaters') },
                { id: 'nightBlindness', label: t('nightBlindness') },
                { id: 'eyePain', label: t('eyePain') },
                { id: 'noneSymptoms', label: t('noneSymptoms') },
              ].map((sym) => (
                <button
                  type="button"
                  key={sym.id}
                  onClick={() => handleCheckboxToggle(sym.id)}
                  className={`p-2.5 rounded-xl border text-left text-xs font-semibold transition ${
                    formData.symptoms.includes(sym.id)
                      ? 'bg-brand-50 border-brand-500 text-brand-900'
                      : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3.5 h-3.5 rounded flex items-center justify-center border ${
                        formData.symptoms.includes(sym.id)
                          ? 'bg-brand-600 border-brand-600 text-white'
                          : 'border-slate-300'
                      }`}
                    >
                      {formData.symptoms.includes(sym.id) && <CheckCircle2 className="w-3 h-3" />}
                    </div>
                    <span>{sym.label}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={(e) => handleSubmit(e, false)}
            disabled={isSubmitting}
            className="w-full sm:w-auto px-6 py-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-bold text-slate-700 transition"
          >
            {t('btnSaveOnly')}
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-glow transition disabled:opacity-50"
          >
            <span>{t('btnSubmitRegister')}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
