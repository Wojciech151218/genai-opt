import { useState } from 'react';
import Panel from '@/components/common/Panel';
import { formatName } from '@/utils/formatters';

const WIDTH = 780;
const HEIGHT = 320;
const PAD = { top: 24, right: 58, bottom: 42, left: 54 };

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
 * Formats large token counts compactly for axis tick labels (e.g. 1.2k).
 * @param {number} value
 * @returns {string}
 */
function formatAxisTokens(value) {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`;
  }
  return String(Math.round(value));
}

/**
 * Interactive dual-axis SVG chart showing per-step token bars and cumulative token curve.
 * @param {{
 *   checkpoints: Array<Record<string, any>>,
 *   selectedCheckpointId: number | null,
 *   onSelectCheckpoint: (id: number) => void,
 *   headerPrefix?: import('react').ReactNode
 * }} props
 */
function TokenUsageChart({
  checkpoints,
  selectedCheckpointId,
  onSelectCheckpoint,
  headerPrefix = null,
}) {
  const [hoveredId, setHoveredId] = useState(null);
  const [visibleSeries, setVisibleSeries] = useState({
    stepBars: true,
    cumulative: true,
  });

  if (checkpoints.length === 0) {
    return (
      <Panel
        className="population-panel"
        title="Token Usage Across Steps"
        headerRow
        headerActions={headerPrefix}
      >
        <div className="empty-placeholder">No token usage data recorded yet.</div>
      </Panel>
    );
  }

  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const bottomY = PAD.top + plotHeight;

  let runningTotal = 0;
  const rawPoints = checkpoints.map((cp, index) => {
    const stepTokens = cp.total_tokens ?? 0;
    runningTotal += stepTokens;
    return {
      id: cp.id,
      index,
      iteration: cp.iteration,
      phase: cp.phase,
      tokens: stepTokens,
      cumulative: runningTotal,
      operations: cp.operation_count ?? 0,
    };
  });

  const maxStepTokens = Math.max(...rawPoints.map((p) => p.tokens), 1);
  const maxCumulativeTokens = Math.max(runningTotal, 1);

  const toStepY = (val) => PAD.top + plotHeight - (val / maxStepTokens) * plotHeight;
  const toCumulativeY = (val) =>
    PAD.top + plotHeight - (val / maxCumulativeTokens) * plotHeight;

  const slotWidth = plotWidth / rawPoints.length;
  const barWidth = Math.min(Math.max(slotWidth * 0.56, 6), 34);

  const points = rawPoints.map((pt, index) => {
    const x =
      rawPoints.length > 1
        ? PAD.left + (index + 0.5) * slotWidth
        : PAD.left + plotWidth / 2;
    const yBar = toStepY(pt.tokens);
    return {
      ...pt,
      x,
      yBar,
      barHeight: Math.max(bottomY - yBar, pt.tokens > 0 ? 3 : 1),
      yCumulative: toCumulativeY(pt.cumulative),
    };
  });

  const cumulativePath = buildSmoothPath(
    points.map((p) => ({ x: p.x, y: p.yCumulative }))
  );

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    ratio,
    y: PAD.top + plotHeight - ratio * plotHeight,
    stepVal: ratio * maxStepTokens,
    cumVal: ratio * maxCumulativeTokens,
  }));

  const activePoint =
    points.find((p) => p.id === hoveredId) ||
    points.find((p) => p.id === selectedCheckpointId) ||
    points[points.length - 1];

  const budgetShare =
    activePoint && runningTotal > 0
      ? `${((activePoint.tokens / runningTotal) * 100).toFixed(1)}%`
      : '0.0%';

  const toggleSeries = (key) =>
    setVisibleSeries((prev) => ({ ...prev, [key]: !prev[key] }));

  const legendControls = (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
      {headerPrefix}
      <div className="pop-toggle">
        <button
          type="button"
          className={`pop-toggle-btn ${visibleSeries.stepBars ? 'active' : ''}`}
          onClick={() => toggleSeries('stepBars')}
        >
          ■ Step Tokens
        </button>
        <button
          type="button"
          className={`pop-toggle-btn ${visibleSeries.cumulative ? 'active' : ''}`}
          onClick={() => toggleSeries('cumulative')}
        >
          ● Cumulative
        </button>
      </div>
    </div>
  );

  return (
    <Panel
      className="population-panel"
      title="Token Usage & Cumulative Budget"
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
            <span>Step Tokens</span>
            <strong style={{ color: '#38bdf8' }}>{activePoint.tokens.toLocaleString()}</strong>
          </div>
          <div className="step-metric">
            <span>Cumulative Tokens</span>
            <strong style={{ color: 'var(--status-paused)' }}>
              {activePoint.cumulative.toLocaleString()}
            </strong>
          </div>
          <div className="step-metric">
            <span>Share of Total Budget</span>
            <strong>{budgetShare}</strong>
          </div>
        </div>
      )}

      <div style={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center' }}>
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          style={{ width: '100%', height: '100%', maxHeight: '380px', overflow: 'visible' }}
        >
          <defs>
            <linearGradient id="tokenBarGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.88" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.28" />
            </linearGradient>
            <linearGradient id="tokenBarActiveGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--status-running)" stopOpacity="0.98" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.5" />
            </linearGradient>
          </defs>

          {yTicks.map((tick) => (
            <g key={tick.ratio}>
              <line
                x1={PAD.left}
                y1={tick.y}
                x2={WIDTH - PAD.right}
                y2={tick.y}
                stroke="var(--glass-border)"
                strokeDasharray="4 4"
              />
              {visibleSeries.stepBars && (
                <text
                  x={PAD.left - 10}
                  y={tick.y + 4}
                  textAnchor="end"
                  fill="#38bdf8"
                  fontSize="11"
                >
                  {formatAxisTokens(tick.stepVal)}
                </text>
              )}
              {visibleSeries.cumulative && (
                <text
                  x={WIDTH - PAD.right + 10}
                  y={tick.y + 4}
                  textAnchor="start"
                  fill="var(--status-paused)"
                  fontSize="11"
                >
                  {formatAxisTokens(tick.cumVal)}
                </text>
              )}
            </g>
          ))}

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

          {points.map((p) => {
            const isSelected = p.id === selectedCheckpointId;
            const isHovered = p.id === hoveredId;
            const isHighlighted = isSelected || isHovered;
            const showXLabel =
              points.length <= 12 || p.index % Math.ceil(points.length / 10) === 0;

            return (
              <g
                key={p.id}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredId(p.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => onSelectCheckpoint(p.id)}
              >
                <rect
                  x={p.x - Math.max(slotWidth / 2, 12)}
                  y={PAD.top}
                  width={Math.max(slotWidth, 24)}
                  height={plotHeight}
                  fill="transparent"
                />

                {visibleSeries.stepBars && (
                  <rect
                    x={p.x - barWidth / 2}
                    y={bottomY - p.barHeight}
                    width={barWidth}
                    height={p.barHeight}
                    rx="4"
                    fill={isHighlighted ? 'url(#tokenBarActiveGrad)' : 'url(#tokenBarGrad)'}
                    stroke={isHighlighted ? 'var(--text-primary)' : 'none'}
                    strokeWidth={isHighlighted ? '1' : '0'}
                  />
                )}

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
              </g>
            );
          })}

          {visibleSeries.cumulative && (
            <path
              d={cumulativePath}
              fill="none"
              stroke="var(--status-paused)"
              strokeWidth="2.6"
              strokeLinecap="round"
              style={{ pointerEvents: 'none' }}
            />
          )}

          {visibleSeries.cumulative &&
            points.map((p) => {
              const isHighlighted = p.id === selectedCheckpointId || p.id === hoveredId;
              return (
                <circle
                  key={`cum-${p.id}`}
                  cx={p.x}
                  cy={p.yCumulative}
                  r={isHighlighted ? 6 : 3.8}
                  fill="var(--status-paused)"
                  stroke="var(--bg-dark)"
                  strokeWidth="2"
                  style={{ pointerEvents: 'none' }}
                />
              );
            })}
        </svg>
      </div>
    </Panel>
  );
}

export default TokenUsageChart;
