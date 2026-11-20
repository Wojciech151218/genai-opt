import OperationCard from '@/components/common/OperationCard';
import Panel from '@/components/common/Panel';

/**
 * Right column listing all LLM and genome operations recorded in the selected checkpoint phase.
 * @param {{ operations?: Array<Record<string, any>> }} props
 */
function PhaseOperationsPanel({ operations }) {
  const list = operations || [];
  const panelTitle = `Phase Operations (${list.length})`;
  const isEmpty = list.length === 0;

  return (
    <Panel className="operations-panel" title={panelTitle}>
      <div className="operations-list">
        {list.map((op) => (
          <OperationCard
            key={op.id}
            variant="recorded"
            kind={op.kind}
            model={op.model}
            durationSeconds={op.duration_seconds}
            tokens={op.tokens}
            tokensIn={op.tokens_in}
            tokensOut={op.tokens_out}
          />
        ))}
        {isEmpty && (
          <div className="empty-placeholder">
            No LLM/genome operations recorded in this phase.
          </div>
        )}
      </div>
    </Panel>
  );
}

export default PhaseOperationsPanel;
