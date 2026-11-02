/**
 * Pill badge showing the current optimizer execution state (running, pausing, paused, stopped).
 * @param {{ status: string }} props
 */
function StatusBadge({ status }) {
  return (
    <div className={`status-badge ${status}`}>
      <div className="status-dot"></div>
      {status}
    </div>
  );
}

export default StatusBadge;
