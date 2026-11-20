import { useCallback, useEffect, useRef, useState } from 'react';
import { TOAST_DURATION_MS } from '@/constants/config';

/**
 * Manages temporary floating toast messages with automatic timer cleanup.
 * @returns {{ toastMessage: string | null, showToast: (message: string) => void }}
 */
export function useToast() {
  const [toastMessage, setToastMessage] = useState(null);
  const timerRef = useRef(null);

  const showToast = useCallback((message) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    setToastMessage(message);
    timerRef.current = setTimeout(() => {
      setToastMessage(null);
      timerRef.current = null;
    }, TOAST_DURATION_MS);
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return { toastMessage, showToast };
}
