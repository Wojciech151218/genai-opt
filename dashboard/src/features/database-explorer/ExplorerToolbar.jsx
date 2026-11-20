import { Database, Layers, RefreshCw } from 'lucide-react';
import { CUSTOM_DB_OPTION } from '@/constants/config';
import SummaryPills from '@/features/database-explorer/SummaryPills';
import { formatBytes, formatFitness } from '@/utils/formatters';

/**
 * Formats an experiment dropdown option label.
 * @param {{ experiment_id: string, checkpoint_count: number, best_fitness?: number | null }} exp
 * @returns {string}
 */
function formatExperimentOption(exp) {
  const bestSuffix =
    exp.best_fitness != null ? ` • Best: ${formatFitness(exp.best_fitness, 1)}` : '';
  return `${exp.experiment_id} (${exp.checkpoint_count} steps${bestSuffix})`;
}

/**
 * Top control bar for selecting SQLite database files, Experiment IDs, and triggering history reloads.
 * @param {{
 *   databases: Array<{ name: string, path: string, size_bytes: number }>,
 *   selectedDb: string,
 *   customDbPath: string,
 *   useCustomDb: boolean,
 *   experiments: Array<Record<string, any>>,
 *   selectedExp: string,
 *   summary: Record<string, any> | null,
 *   loading: boolean,
 *   onSelectDbOption: (value: string) => void,
 *   onCustomDbPathChange: (value: string) => void,
 *   onShowDbList: () => void,
 *   onSelectExp: (experimentId: string) => void,
 *   onRefresh: () => void
 * }} props
 */
function ExplorerToolbar({
  databases,
  selectedDb,
  customDbPath,
  useCustomDb,
  experiments,
  selectedExp,
  summary,
  loading,
  onSelectDbOption,
  onCustomDbPathChange,
  onShowDbList,
  onSelectExp,
  onRefresh,
}) {
  const hasDatabases = databases.length > 0;
  const hasExperiments = experiments.length > 0;
  const refreshIconClassName = loading ? 'spin-icon' : '';

  return (
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
            onChange={(e) => onSelectDbOption(e.target.value)}
          >
            {!hasDatabases && <option value="">No .db files in .checkpoints/</option>}
            {databases.map((db) => (
              <option key={db.path} value={db.path}>
                {db.name} ({formatBytes(db.size_bytes)})
              </option>
            ))}
            <option value={CUSTOM_DB_OPTION}>Custom file path...</option>
          </select>
        ) : (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="text"
              className="glass-input"
              placeholder="e.g. .checkpoints/my_run.db"
              value={customDbPath}
              onChange={(e) => onCustomDbPathChange(e.target.value)}
            />
            {hasDatabases && (
              <button type="button" className="btn btn-compact" onClick={onShowDbList}>
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
          onChange={(e) => onSelectExp(e.target.value)}
          disabled={!hasExperiments}
        >
          {!hasExperiments && <option value="">No experiments</option>}
          {experiments.map((exp) => (
            <option key={exp.experiment_id} value={exp.experiment_id}>
              {formatExperimentOption(exp)}
            </option>
          ))}
        </select>
      </div>

      <SummaryPills summary={summary} />

      <button
        type="button"
        className="btn btn-compact"
        style={{ marginLeft: 'auto' }}
        onClick={onRefresh}
        title="Reload database history"
      >
        <RefreshCw size={15} className={refreshIconClassName} /> Refresh
      </button>
    </div>
  );
}

export default ExplorerToolbar;
