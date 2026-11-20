const NAME_MAPPING = {
  evaluate_offspring: 'Offspring Evaluation',
  evaluate_population: 'Population Evaluation',
  reproduce: 'Reproduction',
  mutate: 'Mutation',
  replace: 'Replacement',
  crossover: 'Crossover Phase',
  invoke: 'Genome Invocation',
  evaluate: 'Genome Evaluation',
  mutate_genome: 'Genome Mutation',
  evaluate_genome: 'Genome Evaluation',
  llm_generate_haiku: 'LLM Haiku Generation',
  llm_mutate_haiku: 'LLM Haiku Mutation',
  SELECTION: 'Selection',
  CROSSOVER: 'Crossover',
  MUTATION: 'Mutation',
  EVALUATION: 'Evaluation',
  REPLACEMENT: 'Replacement',
};

/**
 * Formats internal snake_case or uppercase phase/operation identifiers into human-readable labels.
 * @param {string | null | undefined} name
 * @returns {string}
 */
export function formatName(name) {
  if (!name) return '';
  return (
    NAME_MAPPING[name] ||
    name
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  );
}

/**
 * Formats a byte count into B, KB, or MB.
 * @param {number | null | undefined} bytes
 * @returns {string}
 */
export function formatBytes(bytes) {
  if (bytes == null) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Formats a numeric fitness score or returns an em-dash placeholder when absent.
 * @param {number | null | undefined} value
 * @param {number} [decimals=2]
 * @returns {string}
 */
export function formatFitness(value, decimals = 2) {
  if (value == null) return '—';
  return Number(value).toFixed(decimals);
}

/**
 * Formats live WebSocket operation duration (matching original "-s" fallback).
 * @param {number | null | undefined} seconds
 * @returns {string}
 */
export function formatLiveDuration(seconds) {
  return `${seconds ? seconds.toFixed(2) : '-'}s`;
}

/**
 * Formats recorded checkpoint operation duration in seconds.
 * @param {number | null | undefined} seconds
 * @returns {string}
 */
export function formatRecordedDuration(seconds) {
  return seconds != null ? `${seconds.toFixed(2)}s` : '-';
}

/**
 * Formats JSON data with two-space indentation.
 * @param {unknown} value
 * @returns {string}
 */
export function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

/**
 * Formats genome invocation output as pretty-printed JSON for objects or plain string otherwise.
 * @param {unknown} invocation
 * @returns {string}
 */
export function formatInvocation(invocation) {
  return typeof invocation === 'object' ? JSON.stringify(invocation, null, 2) : String(invocation);
}

/**
 * Extracts the time portion from an ISO/SQLite timestamp string.
 * @param {string | null | undefined} timestamp
 * @returns {string}
 */
export function formatCheckpointTime(timestamp) {
  if (!timestamp) return '';
  return timestamp.split(' ')[1] || timestamp;
}

/**
 * Formats total tokens with optional input/output breakdown.
 * @param {number | null | undefined} tokens
 * @param {number | null | undefined} tokensIn
 * @param {number | null | undefined} tokensOut
 * @returns {string}
 */
export function formatTokenSummary(tokens, tokensIn, tokensOut) {
  const total = tokens ?? 0;
  if (tokensIn != null && tokensOut != null) {
    return `${total} (${tokensIn} in / ${tokensOut} out)`;
  }
  return String(total);
}
