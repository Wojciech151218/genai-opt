import EngineStatePanel from '@/features/live-monitor/EngineStatePanel';
import OperationsFeed from '@/features/live-monitor/OperationsFeed';
import PopulationPanel from '@/features/live-monitor/PopulationPanel';

/**
 * Three-column Live Monitor view rendering engine telemetry, live population, and operation stream.
 * Renders `.main-grid` as root element to preserve `.dashboard-container > .main-grid` styling.
 * @param {{
 *   metrics: { iteration: number, populationSize: number, phase: string },
 *   populationJson: Array<Record<string, any>> | null,
 *   operations: Array<Record<string, any>>
 * }} props
 */
function LiveMonitor({ metrics, populationJson, operations }) {
  return (
    <div className="main-grid">
      <EngineStatePanel metrics={metrics} />
      <PopulationPanel populationJson={populationJson} />
      <OperationsFeed operations={operations} />
    </div>
  );
}

export default LiveMonitor;
