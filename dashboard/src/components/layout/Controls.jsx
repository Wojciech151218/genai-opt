import { Pause, Play } from 'lucide-react';
import { ENGINE_STATUS } from '@/constants/config';

/**
 * Execution steering buttons (Resume / Pause) for the live optimizer engine.
 * @param {{
 *   status: string,
 *   isConnected: boolean,
 *   onResume: () => void,
 *   onPause: () => void
 * }} props
 */
function Controls({ status, isConnected, onResume, onPause }) {
  const resumeOpacity = status !== ENGINE_STATUS.PAUSED && isConnected ? 0.5 : 1;
  const pauseOpacity = status !== ENGINE_STATUS.RUNNING && isConnected ? 0.5 : 1;
  const pauseLabel = status === ENGINE_STATUS.PAUSING ? 'Pausing...' : 'Pause';

  return (
    <div className="controls">
      <button
        type="button"
        className="btn"
        onClick={onResume}
        style={{ opacity: resumeOpacity }}
      >
        <Play size={18} /> Resume
      </button>
      <button
        type="button"
        className="btn"
        onClick={onPause}
        style={{ opacity: pauseOpacity }}
      >
        <Pause size={18} /> {pauseLabel}
      </button>
    </div>
  );
}

export default Controls;
