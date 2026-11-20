import Controls from '@/components/layout/Controls';
import NavTabs from '@/components/layout/NavTabs';
import { DASHBOARD_VIEWS } from '@/constants/config';

/**
 * Secondary bar combining view navigation tabs and contextual live engine controls.
 * @param {{
 *   activeView: string,
 *   onSelectView: (view: string) => void,
 *   status: string,
 *   isConnected: boolean,
 *   onResume: () => void,
 *   onPause: () => void
 * }} props
 */
function TopBar({ activeView, onSelectView, status, isConnected, onResume, onPause }) {
  const showControls = activeView === DASHBOARD_VIEWS.LIVE;

  return (
    <div className="top-bar-row">
      <NavTabs activeView={activeView} onSelectView={onSelectView} />
      {showControls && (
        <Controls
          status={status}
          isConnected={isConnected}
          onResume={onResume}
          onPause={onPause}
        />
      )}
    </div>
  );
}

export default TopBar;
