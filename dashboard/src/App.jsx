import { useState } from 'react';
import BackgroundOrbs from '@/components/layout/BackgroundOrbs';
import Header from '@/components/layout/Header';
import Toast from '@/components/layout/Toast';
import TopBar from '@/components/layout/TopBar';
import { DASHBOARD_VIEWS } from '@/constants/config';
import DatabaseExplorer from '@/features/database-explorer/DatabaseExplorer';
import LiveMonitor from '@/features/live-monitor/LiveMonitor';
import { useEngineSocket } from '@/features/live-monitor/useEngineSocket';
import { useStyleVariant } from '@/hooks/useStyleVariant';
import { useTheme } from '@/hooks/useTheme';
import { useToast } from '@/hooks/useToast';

/**
 * Root dashboard shell composing layout chrome, preferences, and active view switching.
 */
function App() {
  const [activeView, setActiveView] = useState(DASHBOARD_VIEWS.LIVE);
  const { theme, toggleTheme } = useTheme();
  const { uiStyle, setUiStyle } = useStyleVariant();
  const { toastMessage, showToast } = useToast();
  const {
    status,
    isConnected,
    metrics,
    populationJson,
    operations,
    resumeEngine,
    pauseEngine,
  } = useEngineSocket({ onOfflineCommand: showToast });

  const isLiveView = activeView === DASHBOARD_VIEWS.LIVE;

  return (
    <div className={`app-shell state-${status}`}>
      <BackgroundOrbs />
      <Toast message={toastMessage} />

      <div className="dashboard-container glass-panel">
        <Header
          uiStyle={uiStyle}
          onSelectStyle={setUiStyle}
          theme={theme}
          onToggleTheme={toggleTheme}
          isConnected={isConnected}
          status={status}
        />

        <TopBar
          activeView={activeView}
          onSelectView={setActiveView}
          status={status}
          isConnected={isConnected}
          onResume={resumeEngine}
          onPause={pauseEngine}
        />

        {isLiveView ? (
          <LiveMonitor
            metrics={metrics}
            populationJson={populationJson}
            operations={operations}
          />
        ) : (
          <DatabaseExplorer />
        )}
      </div>
    </div>
  );
}

export default App;
