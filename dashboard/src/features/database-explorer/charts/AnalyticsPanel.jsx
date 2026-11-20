import { useState } from 'react';
import EfficiencyCurveChart from '@/features/database-explorer/charts/EfficiencyCurveChart';
import FitnessConvergenceChart from '@/features/database-explorer/charts/FitnessConvergenceChart';
import PhaseDurationChart from '@/features/database-explorer/charts/PhaseDurationChart';
import PopulationDistributionChart from '@/features/database-explorer/charts/PopulationDistributionChart';
import TokenUsageChart from '@/features/database-explorer/charts/TokenUsageChart';

const CHART_TABS = [
  { id: 'fitness', label: 'Fitness Convergence' },
  { id: 'tokens', label: 'Token Usage' },
  { id: 'duration', label: 'Phase Duration' },
  { id: 'population', label: 'Population Distribution' },
  { id: 'efficiency', label: 'Efficiency Curve' },
];

/**
 * Analytics container allowing users to switch between all 5 experiment SVG charts.
 * @param {{
 *   checkpoints: Array<Record<string, any>>,
 *   checkpointDetail: Record<string, any> | null,
 *   selectedCheckpointId: number | null,
 *   onSelectCheckpoint: (id: number) => void
 * }} props
 */
function AnalyticsPanel({
  checkpoints,
  checkpointDetail,
  selectedCheckpointId,
  onSelectCheckpoint,
}) {
  const [activeChart, setActiveChart] = useState('fitness');

  const chartSelector = (
    <div className="pop-toggle">
      {CHART_TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={`pop-toggle-btn ${activeChart === tab.id ? 'active' : ''}`}
          onClick={() => setActiveChart(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );

  return (
    <div
      style={{
        gridColumn: '2 / -1',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
      }}
    >
      {activeChart === 'fitness' && (
        <FitnessConvergenceChart
          checkpoints={checkpoints}
          selectedCheckpointId={selectedCheckpointId}
          onSelectCheckpoint={onSelectCheckpoint}
          headerPrefix={chartSelector}
        />
      )}
      {activeChart === 'tokens' && (
        <TokenUsageChart
          checkpoints={checkpoints}
          selectedCheckpointId={selectedCheckpointId}
          onSelectCheckpoint={onSelectCheckpoint}
          headerPrefix={chartSelector}
        />
      )}
      {activeChart === 'duration' && (
        <PhaseDurationChart
          checkpoints={checkpoints}
          selectedCheckpointId={selectedCheckpointId}
          onSelectCheckpoint={onSelectCheckpoint}
          headerPrefix={chartSelector}
        />
      )}
      {activeChart === 'population' && (
        <PopulationDistributionChart
          checkpointDetail={checkpointDetail}
          headerPrefix={chartSelector}
        />
      )}
      {activeChart === 'efficiency' && (
        <EfficiencyCurveChart
          checkpoints={checkpoints}
          selectedCheckpointId={selectedCheckpointId}
          onSelectCheckpoint={onSelectCheckpoint}
          headerPrefix={chartSelector}
        />
      )}
    </div>
  );
}

export default AnalyticsPanel;
