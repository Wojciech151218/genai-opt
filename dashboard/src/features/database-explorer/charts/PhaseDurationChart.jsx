import { useState } from 'react';
import Panel from '@/components/common/Panel';
import { formatName } from '@/utils/formatters';

const WIDTH = 780;
const HEIGHT = 320;
const PAD = { top: 24, right: 28, bottom: 42, left: 54 };

const PHASE_CONFIG = [
  { key: 'evaluate_population', shortLabel: 'Eval Pop', color: '#38bdf8' },
  { key: 'reproduce', shortLabel: 'Reproduce', color: '#a78bfa' },
  { key: 'mutate', shortLabel: 'Mutate', color: '#f59e0b' },
  { key: 'evaluate_offspring', shortLabel: 'Eval Offspring', color: 'var(--status-running)' },
  { key: 'replace', shortLabel: 'Replace', color: '#f472b6' },
];

const PHASE_COLOR_MAP = Object.fromEntries(PHASE_CONFIG.map((p) => [p.key, p.color]));

/**
 * Interactive stacked bar SVG chart breaking down execution duration by phase per iteration.
 * @param {{
 *   checkpoints: Array<Record<string, any>>,
 *   selectedCheckpointId: number | null,
 *   onSelectCheckpoint: (id: number) => void,
 *   headerPrefix?: import('react').ReactNode
 * }} props
 */
function PhaseDurationChart({
  checkpoints,
  selectedCheckpointId,
  onSelectCheckpoint,
  headerPrefix = null,
}) {
  const [hoveredStepId, setHoveredStepId] = useState(null);
  const [hoveredIteration, setHoveredIteration] = useState(null);

  if (checkpoints.length === 0) {
    return (
      <Panel
        className="population-panel"
        title="Phase Duration Breakdown"
        headerRow
        headerActions={headerPrefix}
      >
        <div className="empty-placeholder">No phase duration data recorded yet.</div>
      </Panel>
    );
  }

  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const bottomY = PAD.top + plotHeight;

  const iterationMap = new Map();
  checkpoints.forEach((cp) => {
    const iter = cp.iteration;
    if (!iterationMap.has(iter)) {
      iterationMap.set(iter, []);
    }
    iterationMap.get(iter).push(cp);
  });

  const iterationGroups = Array.from(iterationMap.entries()).map(([iteration, steps]) => {
    let cumulativeSeconds = 0;
    let slowestStep = steps[0];
    const segments = steps.map((cp) => {
      const duration = cp.total_duration_seconds ?? 0;
      if (duration > (slowestStep?.total_duration_seconds ?? -1)) {
        slowestStep = cp;
      }
      const startSeconds = cumulativeSeconds;
      cumulativeSeconds += duration;
      return {
        id: cp.id,
        iteration,
        phase: cp.phase,
        duration,
        startSeconds,
        endSeconds: cumulativeSeconds,
        color: PHASE_COLOR_MAP[cp.phase] || '#38bdf8',
      };
    });

    return {
      iteration,
      steps,
      segments,
      totalDuration: cumulativeSeconds,
      slowestPhase: slowestStep?.phase || 'IDLE',
      slowestDuration: slowestStep?.total_duration_seconds ?? 0,
    };
  });

  const maxTotalDuration = Math.max(...iterationGroups.map((g) => g.totalDuration), 0.1);
  const toHeight = (seconds) => (seconds / maxTotalDuration) * plotHeight;
  const toY = (seconds) => bottomY - toHeight(seconds);

  const slotWidth = plotWidth / iterationGroups.length;
  const barWidth = Math.min(Math.max(slotWidth * 0.55, 14), 52);

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const val = ratio * maxTotalDuration;
    return { value: val, y: toY(val) };
  });

  const selectedStep =
    checkpoints.find((cp) => cp.id === hoveredStepId) ||
    checkpoints.find((cp) => cp.id === selectedCheckpointId) ||
    checkpoints[checkpoints.length - 1];

  const activeGroup =
    iterationGroups.find((g) => g.iteration === hoveredIteration) ||
    iterationGroups.find((g) => g.iteration === selectedStep?.iteration) ||
    iterationGroups[iterationGroups.length - 1];

  const activePhaseDuration = selectedStep?.total_duration_seconds ?? 0;

  const legendControls = (
    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
      {headerPrefix}
      <div
        style={{
          display: 'inline-flex',
          gap: '10px',
          alignItems: 'center',
          fontSize: '11.5px',
          color: 'var(--text-secondary)',
          padding: '4px 8px',
        }}
      >
        {PHASE_CONFIG.slice(0, 4).map((p) => (
          <span key={p.key} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '2px',
                background: p.color,
                display: 'inline-block',
              }}
            />
            {p.shortLabel}
          </span>
        ))}
      </div>
    </div>
  );

  return (
    <Panel
      className="population-panel"
      title="Phase Duration Breakdown by Iteration"
      headerRow
      headerActions={legendControls}
    >
      {activeGroup && (
        <div
          className="step-metrics-bar"
          style={{
            gridTemplateColumns: 'minmax(210px, 1.8fr) repeat(3, minmax(0, 1fr))',
          }}
        >
          <div className="step-metric" style={{ minWidth: 0 }}>
            <span>Inspected Step</span>
            <strong
              style={{
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
              title={
                selectedStep
                  ? `Iter ${selectedStep.iteration} • ${formatName(selectedStep.phase)}`
                  : `Iteration ${activeGroup.iteration}`
              }
            >
              {selectedStep
                ? `Iter ${selectedStep.iteration} • ${formatName(selectedStep.phase)}`
                : `Iteration ${activeGroup.iteration}`}
            </strong>
          </div>
          <div className="step-metric">
            <span>Phase Duration</span>
            <strong style={{ color: PHASE_COLOR_MAP[selectedStep?.phase] || '#38bdf8' }}>
              {activePhaseDuration.toFixed(2)}s
            </strong>
          </div>
          <div className="step-metric">
            <span>Iteration Total Time</span>
            <strong>{activeGroup.totalDuration.toFixed(2)}s</strong>
          </div>
          <div className="step-metric" style={{ minWidth: 0 }}>
            <span>Slowest in Iteration</span>
            <strong
              style={{
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                color: 'var(--status-paused)',
              }}
              title={`${formatName(activeGroup.slowestPhase)} (${activeGroup.slowestDuration.toFixed(2)}s)`}
            >
              {formatName(activeGroup.slowestPhase)} ({activeGroup.slowestDuration.toFixed(2)}s)
            </strong>
          </div>
        </div>
      )}

      <div style={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center' }}>
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          style={{ width: '100%', height: '100%', maxHeight: '380px', overflow: 'visible' }}
        >
          {yTicks.map((tick) => (
            <g key={tick.value}>
              <line
                x1={PAD.left}
                y1={tick.y}
                x2={WIDTH - PAD.right}
                y2={tick.y}
                stroke="var(--glass-border)"
                strokeDasharray="4 4"
              />
              <text
                x={PAD.left - 10}
                y={tick.y + 4}
                textAnchor="end"
                fill="var(--text-secondary)"
                fontSize="11"
              >
                {tick.value.toFixed(1)}s
              </text>
            </g>
          ))}

          {iterationGroups.map((group, index) => {
            const xCenter =
              iterationGroups.length > 1
                ? PAD.left + (index + 0.5) * slotWidth
                : PAD.left + plotWidth / 2;
            const isIterActive = activeGroup?.iteration === group.iteration;

            return (
              <g
                key={group.iteration}
                onMouseEnter={() => setHoveredIteration(group.iteration)}
                onMouseLeave={() => {
                  setHoveredIteration(null);
                  setHoveredStepId(null);
                }}
              >
                {isIterActive && (
                  <rect
                    x={xCenter - barWidth / 2 - 6}
                    y={PAD.top}
                    width={barWidth + 12}
                    height={plotHeight}
                    rx="6"
                    fill="rgba(255, 255, 255, 0.03)"
                  />
                )}

                {group.segments.map((seg) => {
                  const segHeight = Math.max(toHeight(seg.duration), seg.duration > 0 ? 3 : 0);
                  const segY = toY(seg.endSeconds);
                  const isSegHighlighted =
                    seg.id === hoveredStepId || seg.id === selectedCheckpointId;

                  return (
                    <rect
                      key={seg.id}
                      x={xCenter - barWidth / 2}
                      y={segY}
                      width={barWidth}
                      height={segHeight}
                      rx="3"
                      fill={seg.color}
                      fillOpacity={isSegHighlighted ? 1 : 0.78}
                      stroke={isSegHighlighted ? 'var(--text-primary)' : 'var(--bg-dark)'}
                      strokeWidth={isSegHighlighted ? '1.8' : '1'}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredStepId(seg.id)}
                      onClick={() => onSelectCheckpoint(seg.id)}
                    />
                  );
                })}

                <text
                  x={xCenter}
                  y={bottomY + 20}
                  textAnchor="middle"
                  fill={isIterActive ? 'var(--text-primary)' : 'var(--text-secondary)'}
                  fontSize="11"
                  fontWeight={isIterActive ? '600' : '400'}
                >
                  Iter {group.iteration}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </Panel>
  );
}

export default PhaseDurationChart;
