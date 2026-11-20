import { useState } from 'react';
import Panel from '@/components/common/Panel';
import { formatFitness, formatName } from '@/utils/formatters';

const WIDTH = 780;
const HEIGHT = 320;
const PAD = { top: 24, right: 32, bottom: 44, left: 54 };

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
 * Formats token axis ticks compactly (e.g. 2.5k).
 * @param {number} tokens
 * @returns {string}
 */
function formatTokenTick(tokens) {
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(tokens >= 10000 ? 0 : 1)}k`;
  }
  return String(Math.round(tokens));
}

/**
 * Interactive SVG Pareto/ROI curve plotting Best Fitness achieved vs. Cumulative Tokens spent.
 * @param {{
 *   checkpoints: Array<Record<string, any>>,
 *   selectedCheckpointId: number | null,
 *   onSelectCheckpoint: (id: number) => void,
 *   headerPrefix?: import('react').ReactNode
 * }} props
 */
function EfficiencyCurveChart({
  checkpoints,
  selectedCheckpointId,
  onSelectCheckpoint,
  headerPrefix = null,
}) {
  const [hoveredId, setHoveredId] = useState(null);
  const [visibleSeries, setVisibleSeries] = useState({
    paretoPeak: true,
    stepBest: true,
  });

  let cumulativeTokens = 0;
  let runningPeak = null;
  const stepsWithFitness = [];

  checkpoints.forEach((cp) => {
    cumulativeTokens += cp.total_tokens ?? 0;
    if (cp.best_fitness != null) {
      runningPeak = runningPeak == null ? cp.best_fitness : Math.max(runningPeak, cp.best_fitness);
      stepsWithFitness.push({
        id: cp.id,
        iteration: cp.iteration,
        phase: cp.phase,
        best: cp.best_fitness,
        peakSoFar: runningPeak,
        cumulativeTokens,
      });
    }
  });

  if (stepsWithFitness.length === 0) {
    return (
      <Panel
        className="population-panel"
        title="Cost Efficiency Curve (Fitness vs. Tokens)"
        headerRow
        headerActions={headerPrefix}
      >
        <div className="empty-placeholder">No fitness and token data recorded yet.</div>
      </Panel>
    );
  }

  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const bottomY = PAD.top + plotHeight;

  const maxTokens = Math.max(stepsWithFitness[stepsWithFitness.length - 1].cumulativeTokens, 1);
  const allFitness = stepsWithFitness.flatMap((s) => [s.best, s.peakSoFar]);
  const maxFitness = Math.max(...allFitness, 1);
  const minFitness = Math.min(0, ...allFitness);
  const fitnessRange = maxFitness - minFitness || 1;

  const toX = (tokens, index) => {
    if (maxTokens <= 1 || stepsWithFitness.length === 1) {
      const ratio =
        stepsWithFitness.length > 1 ? index / (stepsWithFitness.length - 1) : 0.5;
      return PAD.left + ratio * plotWidth;
    }
    return PAD.left + (tokens / maxTokens) * plotWidth;
  };

  const toY = (fitness) =>
    PAD.top + plotHeight - ((fitness - minFitness) / fitnessRange) * plotHeight;

  const points = stepsWithFitness.map((s, index) => ({
    ...s,
    index,
    x: toX(s.cumulativeTokens, index),
    yPeak: toY(s.peakSoFar),
    yBest: toY(s.best),
  }));

  const peakPath = buildSmoothPath(points.map((p) => ({ x: p.x, y: p.yPeak })));
  const stepBestPath = buildSmoothPath(points.map((p) => ({ x: p.x, y: p.yBest })));

  const firstX = points[0].x;
  const lastX = points[points.length - 1].x;
  const peakAreaPath = `${peakPath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const val = minFitness + ratio * fitnessRange;
    return { value: val, y: toY(val) };
  });

  const xTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
    tokens: ratio * maxTokens,
    x: PAD.left + ratio * plotWidth,
  }));

  const activePoint =
    points.find((p) => p.id === hoveredId) ||
    points.find((p) => p.id === selectedCheckpointId) ||
    points[points.length - 1];

  const fitnessPer1kTokens =
    activePoint && activePoint.cumulativeTokens > 0
      ? ((activePoint.peakSoFar / activePoint.cumulativeTokens) * 1000).toFixed(2)
      : '—';

  const toggleSeries = (key) =>
    setVisibleSeries((prev) => ({ ...prev, [key]: !prev[key] }));

  const legendControls = (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
      {headerPrefix}
      <div className="pop-toggle">
        <button
          type="button"
          className={`pop-toggle-btn ${visibleSeries.paretoPeak ? 'active' : ''}`}
          onClick={() => toggleSeries('paretoPeak')}
        >
          ● Peak So Far
        </button>
        <button
          type="button"
          className={`pop-toggle-btn ${visibleSeries.stepBest ? 'active' : ''}`}
          onClick={() => toggleSeries('stepBest')}
        >
          ● Step Best
        </button>
      </div>
    </div>
  );

  return (
    <Panel
      className="population-panel"
      title="Cost Efficiency (Best Fitness vs. Cumulative Tokens)"
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
            <span>Peak / Step Fitness</span>
            <strong style={{ color: 'var(--status-running)' }}>
              {formatFitness(activePoint.peakSoFar)} / {formatFitness(activePoint.best)}
            </strong>
          </div>
          <div className="step-metric">
            <span>Tokens Spent So Far</span>
            <strong style={{ color: 'var(--status-paused)' }}>
              {activePoint.cumulativeTokens.toLocaleString()}
            </strong>
          </div>
          <div className="step-metric">
            <span>Peak Fitness / 1k Tok</span>
            <strong>{fitnessPer1kTokens}</strong>
          </div>
        </div>
      )}

      <div style={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center' }}>
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          style={{ width: '100%', height: '100%', maxHeight: '380px', overflow: 'visible' }}
        >
          <defs>
            <linearGradient id="efficiencyGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--status-running)" stopOpacity="0.3" />
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

          {xTicks.map((tick) => (
            <text
              key={tick.x}
              x={tick.x}
              y={bottomY + 22}
              textAnchor="middle"
              fill="var(--text-secondary)"
              fontSize="11"
            >
              {formatTokenTick(tick.tokens)} tok
            </text>
          ))}

          {visibleSeries.paretoPeak && points.length > 1 && (
            <path d={peakAreaPath} fill="url(#efficiencyGrad)" />
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

          {visibleSeries.stepBest && (
            <path
              d={stepBestPath}
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2"
              strokeDasharray="6 4"
            />
          )}

          {visibleSeries.paretoPeak && (
            <path
              d={peakPath}
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

            return (
              <g
                key={p.id}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredId(p.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => onSelectCheckpoint(p.id)}
              >
                <circle
                  cx={p.x}
                  cy={p.yPeak}
                  r="14"
                  fill="transparent"
                />

                {visibleSeries.stepBest && (
                  <circle
                    cx={p.x}
                    cy={p.yBest}
                    r={isHighlighted ? 5.5 : 3.5}
                    fill="#38bdf8"
                  />
                )}

                {visibleSeries.paretoPeak && (
                  <circle
                    cx={p.x}
                    cy={p.yPeak}
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
  );
}

export default EfficiencyCurveChart;
