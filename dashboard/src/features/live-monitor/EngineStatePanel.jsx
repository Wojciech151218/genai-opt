import MetricCard from '@/components/common/MetricCard';
import Panel from '@/components/common/Panel';
import { formatName } from '@/utils/formatters';

/**
 * Left column panel displaying current iteration, population size, and active phase in Live Monitor.
 * @param {{ metrics: { iteration: number, populationSize: number, phase: string } }} props
 */
function EngineStatePanel({ metrics }) {
  const phaseLabel = formatName(metrics.phase);

  return (
    <Panel className="metrics-panel" title="Engine Live State">
      <div className="metrics-grid">
        <MetricCard label="Current Iteration" value={metrics.iteration} />
        <MetricCard label="Population Size" value={metrics.populationSize} />
        <MetricCard label="Active Phase" value={phaseLabel} fullWidth isPhase />
      </div>
    </Panel>
  );
}

export default EngineStatePanel;
