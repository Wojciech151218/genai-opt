import { Sparkles, Terminal } from 'lucide-react';
import { UI_STYLES } from '@/constants/config';

/**
 * Segmented control switching between Liquid Glass and Modern Developer UI styles.
 * @param {{ uiStyle: string, onSelectStyle: (style: string) => void }} props
 */
function StyleSwitcher({ uiStyle, onSelectStyle }) {
  const glassClassName =
    uiStyle === UI_STYLES.GLASS ? 'style-switch-btn active' : 'style-switch-btn';
  const modernClassName =
    uiStyle === UI_STYLES.MODERN ? 'style-switch-btn active' : 'style-switch-btn';

  return (
    <div className="style-switcher" role="group" aria-label="Interface style">
      <button
        type="button"
        className={glassClassName}
        onClick={() => onSelectStyle(UI_STYLES.GLASS)}
        title="Liquid Glass interface"
      >
        <Sparkles size={14} /> Liquid Glass
      </button>
      <button
        type="button"
        className={modernClassName}
        onClick={() => onSelectStyle(UI_STYLES.MODERN)}
        title="Modern Developer workspace interface"
      >
        <Terminal size={14} /> Modern Developer
      </button>
    </div>
  );
}

export default StyleSwitcher;
