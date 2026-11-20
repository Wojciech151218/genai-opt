import GenomeCard from '@/components/common/GenomeCard';
import Panel from '@/components/common/Panel';

const EMPTY_STYLE = {
  color: 'var(--text-secondary)',
  textAlign: 'center',
  marginTop: '40px',
};

/**
 * Center column panel listing current live genomes streamed over WebSocket.
 * @param {{ populationJson: Array<Record<string, any>> | null }} props
 */
function PopulationPanel({ populationJson }) {
  const hasGenomes = Array.isArray(populationJson) && populationJson.length > 0;

  return (
    <Panel className="population-panel" title="Population State">
      <div className="population-list">
        {hasGenomes ? (
          populationJson.map((member, index) => (
            <GenomeCard key={member.id ?? `live-genome-${index}`} member={member} index={index} />
          ))
        ) : (
          <div style={EMPTY_STYLE}>Awaiting population data...</div>
        )}
      </div>
    </Panel>
  );
}

export default PopulationPanel;
