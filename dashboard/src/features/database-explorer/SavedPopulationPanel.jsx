import GenomeCard from '@/components/common/GenomeCard';
import Panel from '@/components/common/Panel';
import { POPULATION_TABS } from '@/constants/config';
import { formatFitness, formatName } from '@/utils/formatters';

/**
 * Center column displaying saved parent/offspring population snapshots and step summary metrics.
 * @param {{
 *   checkpointDetail: Record<string, any> | null,
 *   populationTab: string,
 *   displayedGenomes: Array<Record<string, any>>,
 *   onSelectPopulationTab: (tab: string) => void
 * }} props
 */
function SavedPopulationPanel({
  checkpointDetail,
  populationTab,
  displayedGenomes,
  onSelectPopulationTab,
}) {
  const titleSuffix = checkpointDetail
    ? ` • Iter ${checkpointDetail.iteration} (${formatName(checkpointDetail.phase)})`
    : '';
  const panelTitle = `Saved Population${titleSuffix}`;

  const offspringList = checkpointDetail?.offspring_population;
  const parentsClassName =
    populationTab === POPULATION_TABS.PARENTS ? 'pop-toggle-btn active' : 'pop-toggle-btn';
  const offspringClassName =
    populationTab === POPULATION_TABS.OFFSPRING ? 'pop-toggle-btn active' : 'pop-toggle-btn';

  const headerActions = offspringList ? (
    <div className="pop-toggle">
      <button
        type="button"
        className={parentsClassName}
        onClick={() => onSelectPopulationTab(POPULATION_TABS.PARENTS)}
      >
        Parents ({checkpointDetail.population.length})
      </button>
      <button
        type="button"
        className={offspringClassName}
        onClick={() => onSelectPopulationTab(POPULATION_TABS.OFFSPRING)}
      >
        Offspring ({offspringList.length})
      </button>
    </div>
  ) : null;

  const hasGenomes = displayedGenomes.length > 0;
  const bestFitness = formatFitness(checkpointDetail?.best_fitness);
  const meanFitness = formatFitness(checkpointDetail?.mean_fitness);
  const worstFitness = formatFitness(checkpointDetail?.worst_fitness);
  const stepTokens = checkpointDetail ? checkpointDetail.total_tokens.toLocaleString() : '0';
  const stepDuration = checkpointDetail
    ? `${checkpointDetail.total_duration_seconds.toFixed(2)}s`
    : '0.00s';

  return (
    <Panel className="population-panel" title={panelTitle} headerRow headerActions={headerActions}>
      {checkpointDetail && (
        <div className="step-metrics-bar">
          <div className="step-metric">
            <span>Best</span>
            <strong>{bestFitness}</strong>
          </div>
          <div className="step-metric">
            <span>Mean</span>
            <strong>{meanFitness}</strong>
          </div>
          <div className="step-metric">
            <span>Worst</span>
            <strong>{worstFitness}</strong>
          </div>
          <div className="step-metric">
            <span>Step Tokens</span>
            <strong>{stepTokens}</strong>
          </div>
          <div className="step-metric">
            <span>Duration</span>
            <strong>{stepDuration}</strong>
          </div>
        </div>
      )}

      <div className="population-list">
        {hasGenomes ? (
          displayedGenomes.map((member, index) => (
            <GenomeCard
              key={member.id ?? `saved-genome-${index}`}
              member={member}
              index={index}
            />
          ))
        ) : (
          <div className="empty-placeholder">Select a checkpoint to inspect saved genomes.</div>
        )}
      </div>
    </Panel>
  );
}

export default SavedPopulationPanel;
