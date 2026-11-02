import { memo } from 'react';
import { Cpu } from 'lucide-react';
import {
  formatLiveDuration,
  formatName,
  formatRecordedDuration,
  formatTokenSummary,
} from '@/utils/formatters';

/**
 * Displays either a live WebSocket operation or a recorded checkpoint operation card.
 * @param {{
 *   variant?: 'live' | 'recorded',
 *   kind: string,
 *   phase?: string,
 *   iteration?: number,
 *   duration?: number | null,
 *   model?: string | null,
 *   durationSeconds?: number | null,
 *   tokens?: number | null,
 *   tokensIn?: number | null,
 *   tokensOut?: number | null
 * }} props
 */
const OperationCard = memo(function OperationCard({
  variant = 'live',
  kind,
  phase,
  iteration,
  duration,
  model,
  durationSeconds,
  tokens,
  tokensIn,
  tokensOut,
}) {
  const isLive = variant === 'live';
  const kindLabel = formatName(kind);
  const phaseLabel = isLive ? formatName(phase) : '';
  const metadataLine = isLive
    ? `Iter: ${iteration} | Duration: ${formatLiveDuration(duration)}`
    : `Duration: ${formatRecordedDuration(durationSeconds)} | Tokens: ${formatTokenSummary(tokens, tokensIn, tokensOut)}`;

  return (
    <div className="operation-card">
      <div className="op-header">
        <span className="op-kind">{kindLabel}</span>
        {isLive && <span className="op-phase">{phaseLabel}</span>}
        {!isLive && model && (
          <span className="op-phase" title="LLM Model">
            <Cpu size={11} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
            {model}
          </span>
        )}
      </div>
      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{metadataLine}</div>
    </div>
  );
});

export default OperationCard;
