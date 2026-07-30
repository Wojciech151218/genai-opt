import { useEffect, useState, useRef } from 'react';
import { Play, Pause, Activity, Wifi, WifiOff } from 'lucide-react';
import './index.css';

function App() {
  const [status, setStatus] = useState('stopped');
  const [isConnected, setIsConnected] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const [metrics, setMetrics] = useState({
    iteration: 0,
    populationSize: 0,
    phase: 'IDLE',
  });
  const [operations, setOperations] = useState([]);
  const ws = useRef(null);

  const connectWebSocket = () => {
    ws.current = new WebSocket('ws://localhost:8765');
    
    ws.current.onopen = () => {
      setIsConnected(true);
      setStatus('running'); // Założenie optymistyczne
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'status') {
        setStatus(data.status);
      } else if (data.type === 'iteration') {
        setMetrics(prev => ({
          ...prev,
          iteration: data.iteration,
          populationSize: data.population_size,
          phase: data.phase || 'TRANSITION',
        }));
      } else if (data.type === 'operation') {
        setOperations(prev => [data, ...prev].slice(0, 30));
      }
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      setStatus('stopped');
    };
    
    ws.current.onerror = () => {
      setIsConnected(false);
      setStatus('stopped');
    };
  };

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const sendCommand = (cmd) => {
    if (!isConnected) {
      showToast('Silnik jest offline. Zanim wyślesz komendę, uruchom backend.');
      return;
    }
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ command: cmd }));
    }
  };

  return (
    <div className={`state-${status}`} style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
      {/* Background Liquid Orbs */}
      <div className="orb orb-1"></div>
      <div className="orb orb-2"></div>

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div className="toast">
          {toastMessage}
        </div>
      )}

      <div className="dashboard-container glass-panel">
        <header className="header">
          <div className="title" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
             <Activity size={28} color="var(--primary-glow)" /> GenAI Opt // Control Dashboard
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            {/* Connection Status Indicator */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: isConnected ? 'var(--status-running)' : 'var(--text-secondary)' }}>
              {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
              {isConnected ? 'Engine Online' : 'Engine Offline'}
            </div>

            <div className={`status-badge ${status}`}>
              <div className="status-dot"></div>
              {status}
            </div>
          </div>
        </header>

        <div className="controls">
          <button 
            className="btn" 
            onClick={() => sendCommand('resume')}
            style={{ opacity: (status !== 'paused' && isConnected) ? 0.5 : 1 }}
          >
            <Play size={18} /> Resume
          </button>
          <button 
            className="btn" 
            onClick={() => sendCommand('pause')}
            style={{ opacity: (status !== 'running' && isConnected) ? 0.5 : 1 }}
          >
            <Pause size={18} /> Pause
          </button>
        </div>

        <div className="main-grid">
          <div className="metrics-panel glass-panel">
            <h2 className="panel-title">Engine Live State</h2>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">Current Iteration</div>
                <div className="metric-value">{metrics.iteration}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Population Size</div>
                <div className="metric-value">{metrics.populationSize}</div>
              </div>
              <div className="metric-card" style={{ gridColumn: '1 / -1' }}>
                <div className="metric-label">Active Phase</div>
                <div className="metric-value" style={{ color: 'var(--primary-glow)' }}>{metrics.phase}</div>
              </div>
            </div>
          </div>

          <div className="operations-panel glass-panel">
            <h2 className="panel-title">Live Operations Feed</h2>
            <div className="operations-list">
              {operations.map((op, idx) => (
                <div key={idx} className="operation-card">
                  <div className="op-header">
                    <span className="op-kind">{op.operation_kind}</span>
                    <span className="op-phase">{op.phase}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Iter: {op.iteration} | Duration: {op.duration ? op.duration.toFixed(2) : '-'}s
                  </div>
                </div>
              ))}
              {operations.length === 0 && (
                <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '40px' }}>
                  Awaiting engine telemetry...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
