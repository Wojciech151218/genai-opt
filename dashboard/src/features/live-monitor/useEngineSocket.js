import { useCallback, useEffect, useRef, useState } from 'react';
import {
  DEFAULT_METRICS,
  ENGINE_COMMANDS,
  ENGINE_STATUS,
  MAX_LIVE_OPERATIONS,
  MESSAGES,
  TRANSITION_PHASE,
  WS_MESSAGE_TYPES,
  WS_URL,
} from '@/constants/config';

/**
 * Connects to the Python optimizer WebSocket server, tracks live telemetry, and sends pause/resume commands.
 * @param {{ onOfflineCommand?: (message: string) => void }} [options]
 * @returns {{
 *   status: string,
 *   isConnected: boolean,
 *   metrics: { iteration: number, populationSize: number, phase: string },
 *   populationJson: Array<Record<string, any>> | null,
 *   operations: Array<Record<string, any>>,
 *   resumeEngine: () => void,
 *   pauseEngine: () => void
 * }}
 */
export function useEngineSocket({ onOfflineCommand } = {}) {
  const [status, setStatus] = useState(ENGINE_STATUS.STOPPED);
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState(DEFAULT_METRICS);
  const [populationJson, setPopulationJson] = useState(null);
  const [operations, setOperations] = useState([]);

  const wsRef = useRef(null);
  const nextOperationIdRef = useRef(0);

  useEffect(() => {
    const socket = new WebSocket(WS_URL);
    wsRef.current = socket;

    socket.onopen = () => {
      if (wsRef.current !== socket) return;
      setIsConnected(true);
      setStatus(ENGINE_STATUS.RUNNING);
    };

    socket.onmessage = (event) => {
      if (wsRef.current !== socket) return;
      const data = JSON.parse(event.data);

      if (data.type === WS_MESSAGE_TYPES.STATUS) {
        setStatus(data.status);
      } else if (data.type === WS_MESSAGE_TYPES.ITERATION) {
        setMetrics((prev) => ({
          ...prev,
          iteration: data.iteration,
          populationSize: data.population_size,
          phase: data.phase || TRANSITION_PHASE,
        }));
        if (data.population_json) {
          setPopulationJson(data.population_json);
        }
      } else if (data.type === WS_MESSAGE_TYPES.OPERATION) {
        nextOperationIdRef.current += 1;
        const operationWithKey = {
          ...data,
          _clientId: `live-op-${nextOperationIdRef.current}`,
        };
        setOperations((prev) => [operationWithKey, ...prev].slice(0, MAX_LIVE_OPERATIONS));
      }
    };

    socket.onclose = () => {
      if (wsRef.current !== socket) return;
      setIsConnected(false);
      setStatus(ENGINE_STATUS.STOPPED);
    };

    socket.onerror = () => {
      if (wsRef.current !== socket) return;
      setIsConnected(false);
      setStatus(ENGINE_STATUS.STOPPED);
    };

    return () => {
      if (wsRef.current === socket) {
        wsRef.current = null;
      }
      socket.close();
    };
  }, []);

  const sendCommand = useCallback(
    (command) => {
      if (!isConnected) {
        onOfflineCommand?.(MESSAGES.ENGINE_OFFLINE_COMMAND);
        return;
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ command }));
      }
    },
    [isConnected, onOfflineCommand]
  );

  const resumeEngine = useCallback(() => {
    sendCommand(ENGINE_COMMANDS.RESUME);
  }, [sendCommand]);

  const pauseEngine = useCallback(() => {
    if (!isConnected) {
      sendCommand(ENGINE_COMMANDS.PAUSE);
      return;
    }
    if (status === ENGINE_STATUS.RUNNING) {
      setStatus(ENGINE_STATUS.PAUSING);
      sendCommand(ENGINE_COMMANDS.PAUSE);
    }
  }, [isConnected, sendCommand, status]);

  return {
    status,
    isConnected,
    metrics,
    populationJson,
    operations,
    resumeEngine,
    pauseEngine,
  };
}
