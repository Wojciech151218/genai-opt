import { useState } from 'react';
import Panel from '@/components/common/Panel';
import { formatFitness, formatName } from '@/utils/formatters';

const WIDTH = 780;
const HEIGHT = 320;
const PAD = { top: 24, right: 28, bottom: 42, left: 54 };

/**
 * Converts an array of {x, y} points into a smooth cubic Bezier SVG path string.
 * @param {Array<{ x: number, y: number }>} pts
 * @returns {string}
 */
function buildSmoothPath(pts) {
  if (pts.length === 0) return '';
  if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;
  return pts.reduce((acc, pt, i, arr) => {
    if (i === 0) return `M ${pt.x} ${pt.y}`;
    const prev = arr[i - 1];
    const cpx = (prev.x + pt.x) / 2;
    return `${acc} C ${cpx} ${prev.y}, ${cpx} ${pt.y}, ${pt.x} ${pt.y}`;
  }, '');
}

/**
 * Interactive SVG chart displaying Best and Mean fitness convergence across steps.
 * @param {{
 *   checkpoints: Array<Record<string, any>>,
 *   selectedCheckpointId: number | null,
 *   onSelectCheckpoint: (id: number) => void
 * }} props
 */
function FitnessConvergenceChart({ checkpoints, selectedCheckpointId, onSelectCheckpoint }) {
  const [hoveredId, setHoveredId] = useState(null);
  const [visibleSeries, setVisibleSeries] = useState({
    best: true,
    mean: true,
  });

  const validSteps = checkpoints.filter((cp) => cp.best_fitness != null);

  if (validSteps.length === 0) {
    return (
      <div style={{ gridColumn: '2 / -1', display: 'flex', minHeight: 0 }}>
        <Panel className="population-panel" title="Fitness Convergence">
          <div className="empty-placeholder">No fitness data recorded yet.</div>
        </Panel>
      </div>
    );
  }

  const allValues = validSteps.flatMap((cp) => [
    cp.best_fitness,
    cp.mean_fitness ?? cp.best_fitness,
  ]);
  const maxVal = Math.max(...allValues, 1);
  const minVal = Math.min(0, ...allValues);
  const valueRange = maxVal - minVal || 1;

  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const bottomY = PAD.top + plotHeight;

  const toY = (val) => PAD.top + plotHeight - (((val ?? 0) - minVal) / valueRange) * plotHeight;

  const points = validSteps.map((cp, index) => {
    const xRatio = validSteps.length > 1 ? index / (validSteps.length - 1) : 0.5;
    const best = cp.best_fitness;
    const mean = cp.mean_fitness ?? best;
    return {
      id: cp.id,
      index,
      iteration: cp.iteration,
      phase: cp.phase,
      tokens: cp.total_tokens,
      best,
      mean,
      x: PAD.left + xRatio * plotWidth,
      yBest: toY(best),
      yMean: toY(mean),
    };
  });

  const bestPath = buildSmoothPath(points.map((p) => ({ x: p.x, y: p.yBest })));
  const meanPath = buildSmoothPath(points.map((p) => ({ x: p.x, y: p.yMean })));

  const firstX = points[0].x;
  const lastX = points[points.length - 1].x;
  const bestAreaPath = `${bestPath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const val = minVal + ratio * valueRange;
    return { value: val, y: toY(val) };
  });

  const activePoint =
    points.find((p) => p.id === hoveredId) ||
    points.find((p) => p.id === selectedCheckpointId) ||
    points[points.length - 1];

  const toggleSeries = (key) =>
    setVisibleSeries((prev) => ({ ...prev, [key]: !prev[key] }));

  const legendControls = (
    <div className="pop-toggle">
      <button
        type="button"
        className={`pop-toggle-btn ${visibleSeries.best ? 'active' : ''}`}
        onClick={() => toggleSeries('best')}
      >
        ● Best
      </button>
      <button
        type="button"
        className={`pop-toggle-btn ${visibleSeries.mean ? 'active' : ''}`}
        onClick={() => toggleSeries('mean')}
      >
        ● Mean
      </button>
    </div>
  );

  return (
    <div style={{ gridColumn: '2 / -1', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Panel
        className="population-panel"
        title="Fitness Convergence Across Steps"
        headerRow
        headerActions={legendControls}
      >
        {activePoint && (
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
                title={`Iter ${activePoint.iteration} • ${formatName(activePoint.phase)}`}
              >
                Iter {activePoint.iteration} • {formatName(activePoint.phase)}
              </strong>
            </div>
            <div className="step-metric">
              <span>Best Fitness</span>
              <strong style={{ color: 'var(--status-running)' }}>
                {formatFitness(activePoint.best)}
              </strong>
            </div>
            <div className="step-metric">
              <span>Mean Fitness</span>
              <strong style={{ color: '#38bdf8' }}>{formatFitness(activePoint.mean)}</strong>
            </div>
            <div className="step-metric">
              <span>Lead (Best - Mean)</span>
              <strong>{formatFitness(activePoint.best - activePoint.mean)}</strong>
            </div>
          </div>
        )}

        <div style={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center' }}>
          <svg
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            style={{ width: '100%', height: '100%', maxHeight: '380px', overflow: 'visible' }}
          >
            <defs>
              <linearGradient id="bestAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--status-running)" stopOpacity="0.32" />
                <stop offset="100%" stopColor="var(--status-running)" stopOpacity="0.0" />
              </linearGradient>
            </defs>

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
                  {tick.value.toFixed(0)}
                </text>
              </g>
            ))}

            {visibleSeries.best && points.length > 1 && (
              <path d={bestAreaPath} fill="url(#bestAreaGrad)" />
            )}

            {activePoint && (
              <line
                x1={activePoint.x}
                y1={PAD.top}
                x2={activePoint.x}
                y2={bottomY}
                stroke="var(--text-secondary)"
                strokeWidth="1.5"
                strokeDasharray="3 3"
              />
            )}

            {visibleSeries.mean && (
              <path
                d={meanPath}
                fill="none"
                stroke="#38bdf8"
                strokeWidth="2.2"
                strokeDasharray="6 4"
              />
            )}

            {visibleSeries.best && (
              <path
                d={bestPath}
                fill="none"
                stroke="var(--status-running)"
                strokeWidth="3"
                strokeLinecap="round"
              />
            )}

            {points.map((p) => {
              const isSelected = p.id === selectedCheckpointId;
              const isHovered = p.id === hoveredId;
              const isHighlighted = isSelected || isHovered;
              const showXLabel =
                points.length <= 12 || p.index % Math.ceil(points.length / 10) === 0;
              const hitWidth = Math.max(plotWidth / points.length, 24);

              return (
                <g
                  key={p.id}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoveredId(p.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  onClick={() => onSelectCheckpoint(p.id)}
                >
                  <rect
                    x={p.x - hitWidth / 2}
                    y={PAD.top}
                    width={hitWidth}
                    height={plotHeight}
                    fill="transparent"
                  />

                  {showXLabel && (
                    <text
                      x={p.x}
                      y={bottomY + 20}
                      textAnchor="middle"
                      fill={isHighlighted ? 'var(--text-primary)' : 'var(--text-secondary)'}
                      fontSize="11"
                      fontWeight={isHighlighted ? '600' : '400'}
                    >
                      I{p.iteration}
                    </text>
                  )}

                  {visibleSeries.mean && (
                    <circle
                      cx={p.x}
                      cy={p.yMean}
                      r={isHighlighted ? 5.5 : 3.5}
                      fill="#38bdf8"
                    />
                  )}

                  {visibleSeries.best && (
                    <circle
                      cx={p.x}
                      cy={p.yBest}
                      r={isHighlighted ? 7 : 4.5}
                      fill="var(--status-running)"
                      stroke="var(--bg-dark)"
                      strokeWidth="2"
                    />
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      </Panel>
    </div>
  );
}

export default FitnessConvergenceChart;
