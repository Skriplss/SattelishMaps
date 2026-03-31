import { useState } from 'react';
import { translations } from '../i18n/translations';
import type { Language } from '../i18n/translations';

export function useTranslation() {
  const [language, setLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem('language');
    return (saved === 'en' || saved === 'sk') ? saved : 'en';
  });

  const t = (key: string): string => {
    const keys = key.split('.');
    let value: any = translations[language];
    
    for (const k of keys) {
      value = value?.[k];
    }
    
    return value || key;
  };

  const changeLanguage = (newLang: Language) => {
    setLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'sk' : 'en';
    changeLanguage(newLang);
  };

  return { t, language, changeLanguage, toggleLanguage };
}
