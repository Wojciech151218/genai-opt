import { formatFitness } from '@/utils/formatters';

/**
 * Summary badges showing peak fitness and cumulative token count for the selected experiment.
 * @param {{ summary: { best_fitness?: number | null, total_tokens: number } | null }} props
 */
function SummaryPills({ summary }) {
  if (!summary) {
    return null;
  }

  const peakFitness = formatFitness(summary.best_fitness);
  const totalTokens = summary.total_tokens.toLocaleString();

  return (
    <div className="exp-summary-pills">
      <span className="summary-pill">
        Peak Fitness: <strong>{peakFitness}</strong>
      </span>
      <span className="summary-pill">
        Total Tokens: <strong>{totalTokens}</strong>
      </span>
    </div>
  );
}

export default SummaryPills;
