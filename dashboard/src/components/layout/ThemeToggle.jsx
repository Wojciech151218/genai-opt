import { Moon, Sun } from 'lucide-react';
import { THEMES } from '@/constants/config';

/**
 * Icon button toggling between Dark and Light color themes.
 * @param {{ theme: string, onToggleTheme: () => void }} props
 */
function ThemeToggle({ theme, onToggleTheme }) {
  const isDark = theme === THEMES.DARK;

  return (
    <button
      type="button"
      className="btn theme-toggle-btn"
      onClick={onToggleTheme}
      title="Toggle Dark / Light Theme"
    >
      {isDark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

export default ThemeToggle;
