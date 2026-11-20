import { useState } from 'react';
import Panel from '@/components/common/Panel';
import { formatFitness, formatName } from '@/utils/formatters';

const WIDTH = 780;
const HEIGHT = 320;
const PAD = { top: 24, right: 28, bottom: 44, left: 54 };

/**
 * Interactive SVG bar chart comparing individual genome fitness inside the selected checkpoint.
 * @param {{
 *   checkpointDetail: Record<string, any> | null,
 *   headerPrefix?: import('react').ReactNode
 * }} props
 */
function PopulationDistributionChart({ checkpointDetail, headerPrefix = null }) {
  const [hoveredKey, setHoveredKey] = useState(null);
  const [visibleGroups, setVisibleGroups] = useState({
    parents: true,
    offspring: true,
  });

  const parents = checkpointDetail?.population || [];
  const offspring = checkpointDetail?.offspring_population || [];
  const hasOffspring = offspring.length > 0;

  if (!checkpointDetail || (parents.length === 0 && offspring.length === 0)) {
    return (
      <Panel
        className="population-panel"
        title="Population Fitness Distribution"
        headerRow
        headerActions={headerPrefix}
      >
        <div className="empty-placeholder">
          Select a checkpoint on the timeline to inspect individual genome fitness bars.
        </div>
      </Panel>
    );
  }

  const bars = [];
  if (visibleGroups.parents) {
    parents.forEach((member, idx) => {
      bars.push({
        key: `parent-${member.id || idx}`,
        label: member.id ? formatName(String(member.id)) : `Parent #${idx + 1}`,
        shortLabel: `P${idx + 1}`,
        group: 'Parents',
        color: '#38bdf8',
        fitness: member.fitness,
      });
    });
  }
  if (hasOffspring && visibleGroups.offspring) {
    offspring.forEach((member, idx) => {
      bars.push({
        key: `offspring-${member.id || idx}`,
        label: member.id ? formatName(String(member.id)) : `Offspring #${idx + 1}`,
        shortLabel: `O${idx + 1}`,
        group: 'Offspring',
        color: 'var(--status-running)',
        fitness: member.fitness,
      });
    });
  }

  const numericFitnesses = bars.map((b) => b.fitness ?? 0);
  const maxFitness = Math.max(...numericFitnesses, checkpointDetail.best_fitness ?? 1, 1);

  const plotWidth = WIDTH - PAD.left - PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const bottomY = PAD.top + plotHeight;

  const toY = (val) => PAD.top + plotHeight - ((val ?? 0) / maxFitness) * plotHeight;

  const slotWidth = bars.length > 0 ? plotWidth / bars.length : plotWidth;
  const barWidth = Math.min(Math.max(slotWidth * 0.6, 10), 44);

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
    const val = ratio * maxFitness;
    return { value: val, y: toY(val) };
  });

  const meanFitness = checkpointDetail.mean_fitness;
  const meanY = meanFitness != null ? toY(meanFitness) : null;

  const activeBar = bars.find((b) => b.key === hoveredKey) || bars[0] || null;
  const deltaVsMean =
    activeBar?.fitness != null && meanFitness != null
      ? `${activeBar.fitness - meanFitness >= 0 ? '+' : ''}${(activeBar.fitness - meanFitness).toFixed(2)}`
      : '—';

  const toggleGroup = (key) =>
    setVisibleGroups((prev) => ({ ...prev, [key]: !prev[key] }));

  const legendControls = (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
      {headerPrefix}
      {hasOffspring && (
        <div className="pop-toggle">
          <button
            type="button"
            className={`pop-toggle-btn ${visibleGroups.parents ? 'active' : ''}`}
            onClick={() => toggleGroup('parents')}
          >
            ■ Parents ({parents.length})
          </button>
          <button
            type="button"
            className={`pop-toggle-btn ${visibleGroups.offspring ? 'active' : ''}`}
            onClick={() => toggleGroup('offspring')}
          >
            ■ Offspring ({offspring.length})
          </button>
        </div>
      )}
    </div>
  );

  const panelTitle = `Population Fitness • Iter ${checkpointDetail.iteration} (${formatName(checkpointDetail.phase)})`;

  return (
    <Panel
      className="population-panel"
      title={panelTitle}
      headerRow
      headerActions={legendControls}
    >
      <div
        className="step-metrics-bar"
        style={{
          gridTemplateColumns: 'minmax(210px, 1.8fr) repeat(3, minmax(0, 1fr))',
        }}
      >
        <div className="step-metric" style={{ minWidth: 0 }}>
          <span>Inspected Genome</span>
          <strong
            style={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            title={activeBar ? `${activeBar.label} (${activeBar.group})` : '—'}
          >
            {activeBar ? `${activeBar.label} (${activeBar.group})` : '—'}
          </strong>
        </div>
        <div className="step-metric">
          <span>Genome Fitness</span>
          <strong style={{ color: activeBar?.color || 'var(--text-primary)' }}>
            {activeBar?.fitness != null ? formatFitness(activeBar.fitness) : 'Pending'}
          </strong>
        </div>
        <div className="step-metric">
          <span>Step Mean Fitness</span>
          <strong style={{ color: 'var(--status-paused)' }}>
            {formatFitness(meanFitness)}
          </strong>
        </div>
        <div className="step-metric">
          <span>Delta vs. Mean</span>
          <strong>{deltaVsMean}</strong>
        </div>
      </div>

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
                {tick.value.toFixed(0)}
              </text>
            </g>
          ))}

          {meanY != null && (
            <g>
              <line
                x1={PAD.left}
                y1={meanY}
                x2={WIDTH - PAD.right}
                y2={meanY}
                stroke="var(--status-paused)"
                strokeWidth="1.8"
                strokeDasharray="6 4"
              />
              <text
                x={WIDTH - PAD.right - 4}
                y={meanY - 6}
                textAnchor="end"
                fill="var(--status-paused)"
                fontSize="10.5"
                fontWeight="600"
              >
                Mean: {formatFitness(meanFitness)}
              </text>
            </g>
          )}

          {bars.map((bar, index) => {
            const xCenter = PAD.left + (index + 0.5) * slotWidth;
            const yTop = toY(bar.fitness ?? 0);
            const barHeight = Math.max(bottomY - yTop, bar.fitness != null ? 4 : 2);
            const isHovered = bar.key === activeBar?.key;

            return (
              <g
                key={bar.key}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredKey(bar.key)}
              >
                <rect
                  x={xCenter - slotWidth / 2}
                  y={PAD.top}
                  width={slotWidth}
                  height={plotHeight}
                  fill="transparent"
                />
                <rect
                  x={xCenter - barWidth / 2}
                  y={bottomY - barHeight}
                  width={barWidth}
                  height={barHeight}
                  rx="5"
                  fill={bar.color}
                  fillOpacity={bar.fitness == null ? 0.25 : isHovered ? 1 : 0.78}
                  stroke={isHovered ? 'var(--text-primary)' : 'none'}
                  strokeWidth={isHovered ? '1.5' : '0'}
                />
                <text
                  x={xCenter}
                  y={bottomY + 20}
                  textAnchor="middle"
                  fill={isHovered ? 'var(--text-primary)' : 'var(--text-secondary)'}
                  fontSize="11"
                  fontWeight={isHovered ? '600' : '400'}
                >
                  {bar.shortLabel}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </Panel>
  );
}

export default PopulationDistributionChart;
