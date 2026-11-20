import { Clock } from 'lucide-react';
import Panel from '@/components/common/Panel';
import { formatCheckpointTime, formatFitness, formatName } from '@/utils/formatters';

/**
 * Left column timeline listing recorded phase checkpoints for the selected experiment.
 * @param {{
 *   checkpoints: Array<{ id: number, iteration: number, phase: string, best_fitness?: number | null, timestamp?: string }>,
 *   selectedCheckpointId: number | null,
 *   hasError: boolean,
 *   onSelectCheckpoint: (id: number) => void
 * }} props
 */
function CheckpointsTimeline({
  checkpoints,
  selectedCheckpointId,
  hasError,
  onSelectCheckpoint,
}) {
  const panelTitle = `Checkpoints Timeline (${checkpoints.length})`;
  const showEmptyPlaceholder = checkpoints.length === 0 && !hasError;

  return (
    <Panel className="metrics-panel" title={panelTitle}>
      <div className="checkpoint-list">
        {checkpoints.map((cp) => {
          const isSelected = cp.id === selectedCheckpointId;
          const itemClassName = isSelected ? 'checkpoint-item active' : 'checkpoint-item';
          const phaseLabel = formatName(cp.phase);
          const bestFitness = formatFitness(cp.best_fitness);
          const timeLabel = formatCheckpointTime(cp.timestamp);

          return (
            <button
              type="button"
              key={cp.id}
              className={itemClassName}
              onClick={() => onSelectCheckpoint(cp.id)}
            >
              <div className="cp-top-row">
                <span className="cp-iter">Iter {cp.iteration}</span>
                <span className="cp-phase-badge">{phaseLabel}</span>
              </div>
              <div className="cp-bottom-row">
                <span>Best: {bestFitness}</span>
                <span className="cp-time">
                  <Clock size={11} /> {timeLabel}
                </span>
              </div>
            </button>
          );
        })}
        {showEmptyPlaceholder && (
          <div className="empty-placeholder">No checkpoints recorded yet.</div>
        )}
      </div>
    </Panel>
  );
}

export default CheckpointsTimeline;
