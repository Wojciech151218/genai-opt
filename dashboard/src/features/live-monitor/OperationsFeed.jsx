import OperationCard from '@/components/common/OperationCard';
import Panel from '@/components/common/Panel';

const EMPTY_STYLE = {
  color: 'var(--text-secondary)',
  textAlign: 'center',
  marginTop: '40px',
};

/**
 * Right column panel streaming the most recent live operations from the optimizer engine.
 * @param {{ operations: Array<Record<string, any>> }} props
 */
function OperationsFeed({ operations }) {
  const isEmpty = operations.length === 0;

  return (
    <Panel className="operations-panel" title="Live Operations Feed">
      <div className="operations-list">
        {operations.map((op) => (
          <OperationCard
            key={op._clientId || `${op.iteration}-${op.phase}-${op.operation_kind}`}
            variant="live"
            kind={op.operation_kind}
            phase={op.phase}
            iteration={op.iteration}
            duration={op.duration}
          />
        ))}
        {isEmpty && <div style={EMPTY_STYLE}>Awaiting engine telemetry...</div>}
      </div>
    </Panel>
  );
}

export default OperationsFeed;
