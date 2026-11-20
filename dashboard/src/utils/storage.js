/**
 * Reads a persisted UI preference from localStorage with validation against allowed values.
 * @param {string} key
 * @param {string} fallback
 * @param {string[]} allowed
 * @returns {string}
 */
export function getInitialPreference(key, fallback, allowed) {
  try {
    const saved = window.localStorage.getItem(key);
    if (saved && allowed.includes(saved)) {
      return saved;
    }
  } catch {
    // Ignore storage errors in restricted environments
  }
  return fallback;
}

/**
 * Persists a UI preference to localStorage, ignoring quota/privacy errors.
 * @param {string} key
 * @param {string} value
 */
export function savePreference(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Ignore storage errors in restricted environments
  }
}
