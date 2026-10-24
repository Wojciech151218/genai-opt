import { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Database, Layers, Clock, Cpu, AlertCircle } from 'lucide-react';

function formatBytes(bytes) {
  if (bytes == null) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const OFFSPRING_PHASES = new Set(['reproduce', 'mutate', 'evaluate_offspring']);

function DatabaseExplorer({ formatName }) {
  const [databases, setDatabases] = useState([]);
  const [selectedDb, setSelectedDb] = useState('');
  const [customDbPath, setCustomDbPath] = useState('');
  const [useCustomDb, setUseCustomDb] = useState(false);

  const [experiments, setExperiments] = useState([]);
  const [selectedExp, setSelectedExp] = useState('');

  const [checkpoints, setCheckpoints] = useState([]);
  const [selectedCheckpointId, setSelectedCheckpointId] = useState(null);
  const [checkpointDetail, setCheckpointDetail] = useState(null);
  const [populationTab, setPopulationTab] = useState('population');

  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  const activeDb = useCustomDb ? customDbPath.trim() : selectedDb;

  const fetchJson = useCallback(async (path) => {
    let response;
    try {
      response = await fetch(path);
    } catch {
      response = await fetch(`http://localhost:8766${path}`);
    }
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(
        'Database API server is offline. Launch via: PYTHONPATH=src python3 -m genai_opt.optimizer_engine.dashboard'
      );
    }
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `Request failed (${response.status})`);
    }
    return payload;
  }, []);

  const loadDatabases = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const data = await fetchJson('/api/databases');
      const dbs = data.databases || [];
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
      setApiError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fetchJson]);

  const loadExperiments = useCallback(
    async (dbPath) => {
      if (!dbPath) return;
      setLoading(true);
      setApiError(null);
      try {
        const data = await fetchJson(`/api/experiments?db=${encodeURIComponent(dbPath)}`);
        const exps = data.experiments || [];
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
        setApiError(err.message);
        setExperiments([]);
        setCheckpoints([]);
        setCheckpointDetail(null);
      } finally {
        setLoading(false);
      }
    },
    [fetchJson]
  );

  const loadCheckpoints = useCallback(
    async (dbPath, experimentId) => {
      if (!dbPath || !experimentId) return;
      setLoading(true);
      setApiError(null);
      try {
        const data = await fetchJson(
          `/api/checkpoints?db=${encodeURIComponent(dbPath)}&experiment_id=${encodeURIComponent(experimentId)}`
        );
        const cps = data.checkpoints || [];
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
        setApiError(err.message);
        setCheckpoints([]);
        setCheckpointDetail(null);
      } finally {
        setLoading(false);
      }
    },
    [fetchJson]
  );

  const loadCheckpointDetail = useCallback(
    async (dbPath, checkpointId) => {
      if (!dbPath || checkpointId == null) return;
      setApiError(null);
      try {
        const detail = await fetchJson(
          `/api/checkpoints/${checkpointId}?db=${encodeURIComponent(dbPath)}`
        );
        setCheckpointDetail(detail);
        if (
          detail.offspring_population &&
          detail.offspring_population.length > 0 &&
          OFFSPRING_PHASES.has(detail.phase)
        ) {
          setPopulationTab('offspring');
        } else {
          setPopulationTab('population');
        }
      } catch (err) {
        setApiError(err.message);
      }
    },
    [fetchJson]
  );

  useEffect(() => {
    loadDatabases();
  }, [loadDatabases]);

  useEffect(() => {
    if (activeDb) {
      loadExperiments(activeDb);
    }
  }, [activeDb, loadExperiments]);

  useEffect(() => {
    if (activeDb && selectedExp) {
      loadCheckpoints(activeDb, selectedExp);
    }
  }, [activeDb, selectedExp, loadCheckpoints]);

  useEffect(() => {
    if (activeDb && selectedCheckpointId != null) {
      loadCheckpointDetail(activeDb, selectedCheckpointId);
    }
  }, [activeDb, selectedCheckpointId, loadCheckpointDetail]);

  const handleRefresh = async () => {
    await loadDatabases();
    if (activeDb) {
      await loadExperiments(activeDb);
      if (selectedExp) {
        await loadCheckpoints(activeDb, selectedExp);
        if (selectedCheckpointId != null) {
          await loadCheckpointDetail(activeDb, selectedCheckpointId);
        }
      }
    }
  };

  const currentExpSummary = experiments.find((e) => e.experiment_id === selectedExp);
  const displayedGenomes =
    populationTab === 'offspring' && checkpointDetail?.offspring_population
      ? checkpointDetail.offspring_population
      : checkpointDetail?.population || [];

  return (
    <div className="explorer-wrapper">
      <div className="explorer-toolbar glass-panel">
        <div className="toolbar-group">
          <label className="toolbar-label" htmlFor="db-select">
            <Database size={14} /> SQLite File
          </label>
          {!useCustomDb ? (
            <select
              id="db-select"
              className="glass-select"
              value={selectedDb}
              onChange={(e) => {
                if (e.target.value === '__custom__') {
                  setUseCustomDb(true);
                } else {
                  setSelectedDb(e.target.value);
                }
              }}
            >
              {databases.length === 0 && <option value="">No .db files in .checkpoints/</option>}
              {databases.map((db) => (
                <option key={db.path} value={db.path}>
                  {db.name} ({formatBytes(db.size_bytes)})
                </option>
              ))}
              <option value="__custom__">Custom file path...</option>
            </select>
          ) : (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="text"
                className="glass-input"
                placeholder="e.g. .checkpoints/my_run.db"
                value={customDbPath}
                onChange={(e) => setCustomDbPath(e.target.value)}
              />
              {databases.length > 0 && (
                <button
                  type="button"
                  className="btn btn-compact"
                  onClick={() => setUseCustomDb(false)}
                >
                  List
                </button>
              )}
            </div>
          )}
        </div>

        <div className="toolbar-group">
          <label className="toolbar-label" htmlFor="exp-select">
            <Layers size={14} /> Experiment ID
          </label>
          <select
            id="exp-select"
            className="glass-select"
            value={selectedExp}
            onChange={(e) => setSelectedExp(e.target.value)}
            disabled={experiments.length === 0}
          >
            {experiments.length === 0 && <option value="">No experiments</option>}
            {experiments.map((exp) => (
              <option key={exp.experiment_id} value={exp.experiment_id}>
                {exp.experiment_id} ({exp.checkpoint_count} steps
                {exp.best_fitness != null ? ` • Best: ${exp.best_fitness.toFixed(1)}` : ''})
              </option>
            ))}
          </select>
        </div>

        {currentExpSummary && (
          <div className="exp-summary-pills">
            <span className="summary-pill">
              Peak Fitness:{' '}
              <strong>
                {currentExpSummary.best_fitness != null
                  ? currentExpSummary.best_fitness.toFixed(2)
                  : '—'}
              </strong>
            </span>
            <span className="summary-pill">
              Total Tokens: <strong>{currentExpSummary.total_tokens.toLocaleString()}</strong>
            </span>
          </div>
        )}

        <button
          type="button"
          className="btn btn-compact"
          style={{ marginLeft: 'auto' }}
          onClick={handleRefresh}
          title="Reload database history"
        >
          <RefreshCw size={15} className={loading ? 'spin-icon' : ''} /> Refresh
        </button>
      </div>

      {apiError && (
        <div className="explorer-error glass-panel">
          <AlertCircle size={18} />
          <span>{apiError}</span>
        </div>
      )}

      <div className="main-grid">
        {/* Column 1: Checkpoints Timeline */}
        <div className="metrics-panel glass-panel">
          <h2 className="panel-title">
            Checkpoints Timeline ({checkpoints.length})
          </h2>
          <div className="checkpoint-list">
            {checkpoints.map((cp) => {
              const isSelected = cp.id === selectedCheckpointId;
              return (
                <button
                  type="button"
                  key={cp.id}
                  className={`checkpoint-item ${isSelected ? 'active' : ''}`}
                  onClick={() => setSelectedCheckpointId(cp.id)}
                >
                  <div className="cp-top-row">
                    <span className="cp-iter">Iter {cp.iteration}</span>
                    <span className="cp-phase-badge">{formatName(cp.phase)}</span>
                  </div>
                  <div className="cp-bottom-row">
                    <span>
                      Best: {cp.best_fitness != null ? cp.best_fitness.toFixed(2) : '—'}
                    </span>
                    <span className="cp-time">
                      <Clock size={11} /> {cp.timestamp?.split(' ')[1] || cp.timestamp}
                    </span>
                  </div>
                </button>
              );
            })}
            {checkpoints.length === 0 && !apiError && (
              <div className="empty-placeholder">
                No checkpoints recorded yet.
              </div>
            )}
          </div>
        </div>

        {/* Column 2: Saved Population Snapshot */}
        <div className="population-panel glass-panel">
          <div className="pop-panel-header">
            <h2 className="panel-title" style={{ marginBottom: 0 }}>
              Saved Population
              {checkpointDetail
                ? ` • Iter ${checkpointDetail.iteration} (${formatName(checkpointDetail.phase)})`
                : ''}
            </h2>
            {checkpointDetail?.offspring_population && (
              <div className="pop-toggle">
                <button
                  type="button"
                  className={`pop-toggle-btn ${populationTab === 'population' ? 'active' : ''}`}
                  onClick={() => setPopulationTab('population')}
                >
                  Parents ({checkpointDetail.population.length})
                </button>
                <button
                  type="button"
                  className={`pop-toggle-btn ${populationTab === 'offspring' ? 'active' : ''}`}
                  onClick={() => setPopulationTab('offspring')}
                >
                  Offspring ({checkpointDetail.offspring_population.length})
                </button>
              </div>
            )}
          </div>

          {checkpointDetail && (
            <div className="step-metrics-bar">
              <div className="step-metric">
                <span>Best</span>
                <strong>
                  {checkpointDetail.best_fitness != null
                    ? checkpointDetail.best_fitness.toFixed(2)
                    : '—'}
                </strong>
              </div>
              <div className="step-metric">
                <span>Mean</span>
                <strong>
                  {checkpointDetail.mean_fitness != null
                    ? checkpointDetail.mean_fitness.toFixed(2)
                    : '—'}
                </strong>
              </div>
              <div className="step-metric">
                <span>Worst</span>
                <strong>
                  {checkpointDetail.worst_fitness != null
                    ? checkpointDetail.worst_fitness.toFixed(2)
                    : '—'}
                </strong>
              </div>
              <div className="step-metric">
                <span>Step Tokens</span>
                <strong>{checkpointDetail.total_tokens.toLocaleString()}</strong>
              </div>
              <div className="step-metric">
                <span>Duration</span>
                <strong>{checkpointDetail.total_duration_seconds.toFixed(2)}s</strong>
              </div>
            </div>
          )}

          <div className="population-list">
            {displayedGenomes.length > 0 ? (
              displayedGenomes.map((member, idx) => (
                <div key={member.id || idx} className="genome-card">
                  <div className="genome-header">
                    <span className="genome-id">
                      {member.id ? formatName(String(member.id)) : `Genome #${idx + 1}`}
                    </span>
                    <span className={`genome-fitness ${member.fitness == null ? 'pending' : ''}`}>
                      {member.fitness != null
                        ? `Fitness: ${Number(member.fitness).toFixed(2)}`
                        : 'Fitness: Pending'}
                    </span>
                  </div>
                  <div className="genome-section-label">Phenotype (JSON)</div>
                  <pre className="genome-json">
                    {JSON.stringify(member.phenotype ?? member, null, 2)}
                  </pre>
                  {member.invocation != null && (
                    <>
                      <div className="genome-section-label" style={{ marginTop: '10px' }}>
                        Invocation Output
                      </div>
                      <pre className="genome-json genome-invocation">
                        {typeof member.invocation === 'object'
                          ? JSON.stringify(member.invocation, null, 2)
                          : String(member.invocation)}
                      </pre>
                    </>
                  )}
                </div>
              ))
            ) : (
              <div className="empty-placeholder">
                Select a checkpoint to inspect saved genomes.
              </div>
            )}
          </div>
        </div>

        {/* Column 3: Recorded Operations */}
        <div className="operations-panel glass-panel">
          <h2 className="panel-title">
            Phase Operations ({checkpointDetail?.operations?.length || 0})
          </h2>
          <div className="operations-list">
            {checkpointDetail?.operations?.map((op) => (
              <div key={op.id} className="operation-card">
                <div className="op-header">
                  <span className="op-kind">{formatName(op.kind)}</span>
                  {op.model && (
                    <span className="op-phase" title="LLM Model">
                      <Cpu size={11} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      {op.model}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  Duration: {op.duration_seconds != null ? `${op.duration_seconds.toFixed(2)}s` : '-'}
                  {' | '}
                  Tokens: {op.tokens ?? 0}
                  {op.tokens_in != null && op.tokens_out != null
                    ? ` (${op.tokens_in} in / ${op.tokens_out} out)`
                    : ''}
                </div>
              </div>
            ))}
            {(!checkpointDetail?.operations || checkpointDetail.operations.length === 0) && (
              <div className="empty-placeholder">
                No LLM/genome operations recorded in this phase.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DatabaseExplorer;
