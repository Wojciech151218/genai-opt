import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { CUSTOM_DB_OPTION, OFFSPRING_PHASES, POPULATION_TABS } from '@/constants/config';
import {
  fetchCheckpointDetail,
  fetchCheckpoints,
  fetchDatabases,
  fetchExperiments,
} from '@/services/dashboardApi';

/**
 * Manages cascading SQLite database, experiment, checkpoint list, and checkpoint detail state.
 * Cancels superseded in-flight HTTP requests via AbortController.
 * @returns {Record<string, any>}
 */
export function useDatabaseExplorer() {
  const [databases, setDatabases] = useState([]);
  const [selectedDb, setSelectedDb] = useState('');
  const [customDbPath, setCustomDbPath] = useState('');
  const [useCustomDb, setUseCustomDb] = useState(false);

  const [experiments, setExperiments] = useState([]);
  const [selectedExp, setSelectedExp] = useState('');

  const [checkpoints, setCheckpoints] = useState([]);
  const [selectedCheckpointId, setSelectedCheckpointId] = useState(null);
  const [checkpointDetail, setCheckpointDetail] = useState(null);
  const [populationTab, setPopulationTab] = useState(POPULATION_TABS.PARENTS);

  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  const refreshControllerRef = useRef(null);
  const activeDb = useCustomDb ? customDbPath.trim() : selectedDb;

  const loadDatabases = useCallback(async ({ signal } = {}) => {
    setLoading(true);
    setApiError(null);
    try {
      const dbs = await fetchDatabases({ signal });
      if (signal?.aborted) return;
      setDatabases(dbs);
      if (dbs.length > 0) {
        setSelectedDb((prev) => (prev && dbs.some((d) => d.path === prev) ? prev : dbs[0].path));
      } else {
        setSelectedDb('');
        setExperiments([]);
        setCheckpoints([]);
        setCheckpointDetail(null);
      }
    } catch (err) {
      if (err?.name === 'AbortError') return;
      setApiError(err.message);
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  const loadExperiments = useCallback(async (dbPath, { signal } = {}) => {
    if (!dbPath) return;
    setLoading(true);
    setApiError(null);
    try {
      const exps = await fetchExperiments(dbPath, { signal });
      if (signal?.aborted) return;
      setExperiments(exps);
      if (exps.length > 0) {
        setSelectedExp((prev) =>
          prev && exps.some((e) => e.experiment_id === prev) ? prev : exps[0].experiment_id
        );
      } else {
        setSelectedExp('');
        setCheckpoints([]);
        setCheckpointDetail(null);
      }
    } catch (err) {
      if (err?.name === 'AbortError') return;
      setApiError(err.message);
      setExperiments([]);
      setCheckpoints([]);
      setCheckpointDetail(null);
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  const loadCheckpoints = useCallback(async (dbPath, experimentId, { signal } = {}) => {
    if (!dbPath || !experimentId) return;
    setLoading(true);
    setApiError(null);
    try {
      const cps = await fetchCheckpoints(dbPath, experimentId, { signal });
      if (signal?.aborted) return;
      setCheckpoints(cps);
      if (cps.length > 0) {
        setSelectedCheckpointId((prev) =>
          prev && cps.some((c) => c.id === prev) ? prev : cps[cps.length - 1].id
        );
      } else {
        setSelectedCheckpointId(null);
        setCheckpointDetail(null);
      }
    } catch (err) {
      if (err?.name === 'AbortError') return;
      setApiError(err.message);
      setCheckpoints([]);
      setCheckpointDetail(null);
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  const loadCheckpointDetail = useCallback(async (dbPath, checkpointId, { signal } = {}) => {
    if (!dbPath || checkpointId == null) return;
    setApiError(null);
    try {
      const detail = await fetchCheckpointDetail(dbPath, checkpointId, { signal });
      if (signal?.aborted) return;
      setCheckpointDetail(detail);
      const shouldShowOffspring =
        detail.offspring_population &&
        detail.offspring_population.length > 0 &&
        OFFSPRING_PHASES.has(detail.phase);
      setPopulationTab(shouldShowOffspring ? POPULATION_TABS.OFFSPRING : POPULATION_TABS.PARENTS);
    } catch (err) {
      if (err?.name === 'AbortError') return;
      setApiError(err.message);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadDatabases({ signal: controller.signal });
    return () => controller.abort();
  }, [loadDatabases]);

  useEffect(() => {
    if (!activeDb) return undefined;
    const controller = new AbortController();
    loadExperiments(activeDb, { signal: controller.signal });
    return () => controller.abort();
  }, [activeDb, loadExperiments]);

  useEffect(() => {
    if (!activeDb || !selectedExp) return undefined;
    const controller = new AbortController();
    loadCheckpoints(activeDb, selectedExp, { signal: controller.signal });
    return () => controller.abort();
  }, [activeDb, selectedExp, loadCheckpoints]);

  useEffect(() => {
    if (!activeDb || selectedCheckpointId == null) return undefined;
    const controller = new AbortController();
    loadCheckpointDetail(activeDb, selectedCheckpointId, { signal: controller.signal });
    return () => controller.abort();
  }, [activeDb, selectedCheckpointId, loadCheckpointDetail]);

  useEffect(() => {
    return () => {
      refreshControllerRef.current?.abort();
    };
  }, []);

  const handleDbSelectChange = useCallback((value) => {
    if (value === CUSTOM_DB_OPTION) {
      setUseCustomDb(true);
    } else {
      setSelectedDb(value);
    }
  }, []);

  const showDatabaseList = useCallback(() => {
    setUseCustomDb(false);
  }, []);

  const handleRefresh = useCallback(async () => {
    refreshControllerRef.current?.abort();
    const controller = new AbortController();
    refreshControllerRef.current = controller;
    const { signal } = controller;

    await loadDatabases({ signal });
    if (signal.aborted || !activeDb) return;
    await loadExperiments(activeDb, { signal });
    if (signal.aborted || !selectedExp) return;
    await loadCheckpoints(activeDb, selectedExp, { signal });
    if (signal.aborted || selectedCheckpointId == null) return;
    await loadCheckpointDetail(activeDb, selectedCheckpointId, { signal });
  }, [
    activeDb,
    loadCheckpointDetail,
    loadCheckpoints,
    loadDatabases,
    loadExperiments,
    selectedCheckpointId,
    selectedExp,
  ]);

  const currentExpSummary = useMemo(
    () => experiments.find((exp) => exp.experiment_id === selectedExp) || null,
    [experiments, selectedExp]
  );

  const displayedGenomes = useMemo(() => {
    if (populationTab === POPULATION_TABS.OFFSPRING && checkpointDetail?.offspring_population) {
      return checkpointDetail.offspring_population;
    }
    return checkpointDetail?.population || [];
  }, [checkpointDetail, populationTab]);

  return {
    databases,
    selectedDb,
    customDbPath,
    useCustomDb,
    experiments,
    selectedExp,
    checkpoints,
    selectedCheckpointId,
    checkpointDetail,
    populationTab,
    loading,
    apiError,
    currentExpSummary,
    displayedGenomes,
    setCustomDbPath,
    setSelectedExp,
    setSelectedCheckpointId,
    setPopulationTab,
    handleDbSelectChange,
    showDatabaseList,
    handleRefresh,
  };
}
