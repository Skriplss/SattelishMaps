import { useSyncExternalStore } from 'react';
import { translations } from '../i18n/translations';
import type { Language } from '../i18n/translations';

// Language lives in a module-level store so every component using the hook
// re-renders on toggle (a per-component useState would desync Sidebar/TopBar).
let currentLanguage: Language = (() => {
  const saved = localStorage.getItem('language');
  return (saved === 'en' || saved === 'sk') ? saved : 'en';
})();

const listeners = new Set<() => void>();

function setLanguage(newLang: Language) {
  currentLanguage = newLang;
  localStorage.setItem('language', newLang);
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useTranslation() {
  const language = useSyncExternalStore(subscribe, () => currentLanguage);

  const t = (key: string): string => {
    const keys = key.split('.');
    let value: any = translations[language];

    for (const k of keys) {
      value = value?.[k];
    }

    return value || key;
  };

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'sk' : 'en');
  };

  return { t, language, toggleLanguage };
}
