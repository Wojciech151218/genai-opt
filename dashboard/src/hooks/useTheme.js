import { useCallback, useEffect, useState } from 'react';
import { ALLOWED_THEMES, DEFAULT_THEME, STORAGE_KEYS, THEMES } from '@/constants/config';
import { getInitialPreference, savePreference } from '@/utils/storage';

/**
 * Manages Dark/Light color theme state, DOM attribute (`data-theme`), and localStorage persistence.
 * @returns {{ theme: string, setTheme: (theme: string) => void, toggleTheme: () => void }}
 */
export function useTheme() {
  const [theme, setTheme] = useState(() =>
    getInitialPreference(STORAGE_KEYS.THEME, DEFAULT_THEME, ALLOWED_THEMES)
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    savePreference(STORAGE_KEYS.THEME, theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK));
  }, []);

  return { theme, setTheme, toggleTheme };
}
