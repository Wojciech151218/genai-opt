export const WS_URL = 'ws://localhost:8765';
export const API_BASE_PATH = '/api';
export const API_FALLBACK_ORIGIN = 'http://localhost:8766';

export const STORAGE_KEYS = {
  THEME: 'genai-opt-theme',
  STYLE: 'genai-opt-style',
};

export const THEMES = {
  DARK: 'dark',
  LIGHT: 'light',
};

export const ALLOWED_THEMES = [THEMES.DARK, THEMES.LIGHT];
export const DEFAULT_THEME = THEMES.DARK;

export const UI_STYLES = {
  GLASS: 'glass',
  MODERN: 'modern',
};

export const ALLOWED_UI_STYLES = [UI_STYLES.GLASS, UI_STYLES.MODERN];
export const DEFAULT_UI_STYLE = UI_STYLES.GLASS;

export const DASHBOARD_VIEWS = {
  LIVE: 'live',
  DATABASE: 'database',
};

export const ENGINE_STATUS = {
  RUNNING: 'running',
  PAUSING: 'pausing',
  PAUSED: 'paused',
  STOPPED: 'stopped',
};

export const ENGINE_COMMANDS = {
  PAUSE: 'pause',
  RESUME: 'resume',
};

export const WS_MESSAGE_TYPES = {
  STATUS: 'status',
  ITERATION: 'iteration',
  OPERATION: 'operation',
};

export const DEFAULT_METRICS = {
  iteration: 0,
  populationSize: 0,
  phase: 'IDLE',
};

export const TRANSITION_PHASE = 'TRANSITION';
export const MAX_LIVE_OPERATIONS = 30;
export const TOAST_DURATION_MS = 3000;

export const CUSTOM_DB_OPTION = '__custom__';

export const POPULATION_TABS = {
  PARENTS: 'population',
  OFFSPRING: 'offspring',
};

export const OFFSPRING_PHASES = new Set(['reproduce', 'mutate', 'evaluate_offspring']);

export const MESSAGES = {
  ENGINE_OFFLINE_COMMAND: 'Engine is offline. Start the backend before sending commands.',
  API_OFFLINE:
    'Database API server is offline. Launch via: PYTHONPATH=src python3 -m genai_opt.optimizer_engine.dashboard',
};
