import { Activity, Database } from 'lucide-react';
import { DASHBOARD_VIEWS } from '@/constants/config';

/**
 * Navigation tabs switching between Live Monitor and Database Explorer views.
 * @param {{ activeView: string, onSelectView: (view: string) => void }} props
 */
function NavTabs({ activeView, onSelectView }) {
  const isLive = activeView === DASHBOARD_VIEWS.LIVE;
  const isDatabase = activeView === DASHBOARD_VIEWS.DATABASE;
  const liveClassName = isLive ? 'nav-tab active' : 'nav-tab';
  const dbClassName = isDatabase ? 'nav-tab active' : 'nav-tab';

  return (
    <div className="nav-tabs" role="tablist" aria-label="Dashboard views">
      <button
        type="button"
        role="tab"
        aria-selected={isLive}
        className={liveClassName}
        onClick={() => onSelectView(DASHBOARD_VIEWS.LIVE)}
      >
        <Activity size={16} /> Live Monitor
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={isDatabase}
        className={dbClassName}
        onClick={() => onSelectView(DASHBOARD_VIEWS.DATABASE)}
      >
        <Database size={16} /> Database Explorer
      </button>
    </div>
  );
}

export default NavTabs;
