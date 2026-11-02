import { useEffect, useState } from 'react';
import { ALLOWED_UI_STYLES, DEFAULT_UI_STYLE, STORAGE_KEYS } from '@/constants/config';
import { getInitialPreference, savePreference } from '@/utils/storage';

/**
 * Manages UI visual style (`glass` vs `modern`), DOM attribute (`data-style`), and localStorage persistence.
 * @returns {{ uiStyle: string, setUiStyle: (style: string) => void }}
 */
export function useStyleVariant() {
  const [uiStyle, setUiStyle] = useState(() =>
    getInitialPreference(STORAGE_KEYS.STYLE, DEFAULT_UI_STYLE, ALLOWED_UI_STYLES)
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-style', uiStyle);
    savePreference(STORAGE_KEYS.STYLE, uiStyle);
  }, [uiStyle]);

  return { uiStyle, setUiStyle };
}
