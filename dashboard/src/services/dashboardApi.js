import { API_BASE_PATH, API_FALLBACK_ORIGIN, MESSAGES } from '@/constants/config';

/**
 * Performs a GET request to the dashboard SQLite API with Vite proxy and direct fallback.
 * @param {string} path
 * @param {{ signal?: AbortSignal }} [options]
 * @returns {Promise<any>}
 */
export async function fetchApiJson(path, { signal } = {}) {
  let response;
  try {
    response = await fetch(path, { signal });
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw err;
    }
    response = await fetch(`${API_FALLBACK_ORIGIN}${path}`, { signal });
  }

  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw new Error(MESSAGES.API_OFFLINE);
  }

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status})`);
  }
  return payload;
}

/**
 * Lists discovered SQLite database files inside `.checkpoints/`.
 * @param {{ signal?: AbortSignal }} [options]
 * @returns {Promise<Array<{ name: string, path: string, size_bytes: number, modified_at: string }>>}
 */
export async function fetchDatabases(options) {
  const data = await fetchApiJson(`${API_BASE_PATH}/databases`, options);
  return data.databases || [];
}

/**
 * Lists experiments stored inside a specific SQLite database file.
 * @param {string} dbPath
 * @param {{ signal?: AbortSignal }} [options]
 * @returns {Promise<Array<Record<string, any>>>}
 */
export async function fetchExperiments(dbPath, options) {
  const query = new URLSearchParams({ db: dbPath });
  const data = await fetchApiJson(`${API_BASE_PATH}/experiments?${query.toString()}`, options);
  return data.experiments || [];
}

/**
 * Lists recorded phase checkpoints for an experiment inside a SQLite database.
 * @param {string} dbPath
 * @param {string} experimentId
 * @param {{ signal?: AbortSignal }} [options]
 * @returns {Promise<Array<Record<string, any>>>}
 */
export async function fetchCheckpoints(dbPath, experimentId, options) {
  const query = new URLSearchParams({ db: dbPath, experiment_id: experimentId });
  const data = await fetchApiJson(`${API_BASE_PATH}/checkpoints?${query.toString()}`, options);
  return data.checkpoints || [];
}

/**
 * Fetches full population, offspring, and operation details for a single checkpoint.
 * @param {string} dbPath
 * @param {number | string} checkpointId
 * @param {{ signal?: AbortSignal }} [options]
 * @returns {Promise<Record<string, any>>}
 */
export async function fetchCheckpointDetail(dbPath, checkpointId, options) {
  const query = new URLSearchParams({ db: dbPath });
  return fetchApiJson(
    `${API_BASE_PATH}/checkpoints/${encodeURIComponent(checkpointId)}?${query.toString()}`,
    options
  );
}
