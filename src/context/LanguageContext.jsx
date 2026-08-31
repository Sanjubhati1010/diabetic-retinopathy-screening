import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from '../data/translations';
import { safeLocalStorageSet, safeLocalStorageGet } from '../services/storage';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return safeLocalStorageGet('dr_lang', 'en') || 'en';
  });

  useEffect(() => {
    safeLocalStorageSet('dr_lang', language);
    document.documentElement.lang = language;
  }, [language]);

  const toggleLanguage = () => {
    setLanguage(prev => (prev === 'en' ? 'hi' : 'en'));
  };

  const t = (key, fallback = '') => {
    if (!key) return fallback || '';
    const currentDict = translations[language] || translations.en;
    if (currentDict && currentDict[key] !== undefined && currentDict[key] !== null) {
      return currentDict[key];
    }
    const fallbackDict = translations.en;
    if (fallbackDict && fallbackDict[key] !== undefined && fallbackDict[key] !== null) {
      return fallbackDict[key];
    }
    if (fallback !== '' && fallback !== null && fallback !== undefined) {
      return fallback;
    }
    return key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
