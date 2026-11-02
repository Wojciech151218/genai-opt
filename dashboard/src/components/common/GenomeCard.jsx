import { memo } from 'react';
import { formatFitness, formatInvocation, formatJson, formatName } from '@/utils/formatters';

/**
 * Displays a single genome's ID, fitness badge, phenotype JSON, and optional invocation output.
 * @param {{
 *   member: { id?: string | number, fitness?: number | null, phenotype?: unknown, invocation?: unknown },
 *   index: number
 * }} props
 */
const GenomeCard = memo(function GenomeCard({ member, index }) {
  const genomeLabel = member.id ? formatName(String(member.id)) : `Genome #${index + 1}`;
  const hasFitness = member.fitness != null;
  const fitnessClassName = hasFitness ? 'genome-fitness' : 'genome-fitness pending';
  const fitnessText = hasFitness
    ? `Fitness: ${formatFitness(member.fitness)}`
    : 'Fitness: Pending';
  const phenotypeText = formatJson(member.phenotype ?? member);
  const hasInvocation = member.invocation != null;
  const invocationText = hasInvocation ? formatInvocation(member.invocation) : '';

  return (
    <div className="genome-card">
      <div className="genome-header">
        <span className="genome-id">{genomeLabel}</span>
        <span className={fitnessClassName}>{fitnessText}</span>
      </div>
      <div className="genome-section-label">Phenotype (JSON)</div>
      <pre className="genome-json">{phenotypeText}</pre>
      {hasInvocation && (
        <>
          <div className="genome-section-label" style={{ marginTop: '10px' }}>
            Invocation Output
          </div>
          <pre className="genome-json genome-invocation">{invocationText}</pre>
        </>
      )}
    </div>
  );
});

export default GenomeCard;
