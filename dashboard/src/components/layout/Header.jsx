import { Activity } from 'lucide-react';
import ConnectionIndicator from '@/components/layout/ConnectionIndicator';
import StatusBadge from '@/components/layout/StatusBadge';
import StyleSwitcher from '@/components/layout/StyleSwitcher';
import ThemeToggle from '@/components/layout/ThemeToggle';

/**
 * Global application header containing title, visual preferences, and engine connection badges.
 * @param {{
 *   uiStyle: string,
 *   onSelectStyle: (style: string) => void,
 *   theme: string,
 *   onToggleTheme: () => void,
 *   isConnected: boolean,
 *   status: string
 * }} props
 */
function Header({ uiStyle, onSelectStyle, theme, onToggleTheme, isConnected, status }) {
  return (
    <header className="header">
      <div className="title" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Activity size={26} className="brand-icon" /> GenAI Opt // Control Dashboard
      </div>

      <div className="header-actions">
        <StyleSwitcher uiStyle={uiStyle} onSelectStyle={onSelectStyle} />
        <ThemeToggle theme={theme} onToggleTheme={onToggleTheme} />
        <ConnectionIndicator isConnected={isConnected} />
        <StatusBadge status={status} />
      </div>
    </header>
  );
}

export default Header;
