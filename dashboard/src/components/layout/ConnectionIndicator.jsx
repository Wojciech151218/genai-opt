import { Wifi, WifiOff } from 'lucide-react';

/**
 * Displays live WebSocket connectivity status with the Python optimizer engine.
 * @param {{ isConnected: boolean }} props
 */
function ConnectionIndicator({ isConnected }) {
  const color = isConnected ? 'var(--status-running)' : 'var(--text-secondary)';
  const label = isConnected ? 'Engine Online' : 'Engine Offline';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color }}>
      {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
      {label}
    </div>
  );
}

export default ConnectionIndicator;
