/**
 * Displays a labeled telemetry metric tile inside Engine Live State.
 * @param {{
 *   label: string,
 *   value: string | number,
 *   fullWidth?: boolean,
 *   isPhase?: boolean
 * }} props
 */
function MetricCard({ label, value, fullWidth = false, isPhase = false }) {
  const cardStyle = fullWidth ? { gridColumn: '1 / -1' } : undefined;
  const valueClassName = isPhase ? 'metric-value metric-phase' : 'metric-value';
  const valueStyle = isPhase ? { color: 'var(--primary-glow)' } : undefined;

  return (
    <div className="metric-card" style={cardStyle}>
      <div className="metric-label">{label}</div>
      <div className={valueClassName} style={valueStyle}>
        {value}
      </div>
    </div>
  );
}

export default MetricCard;
