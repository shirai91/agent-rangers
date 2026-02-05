import { useEffect, useRef, useCallback } from 'react';
import { useBoardStore } from '@/stores/boardStore';
import type { WSEvent } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000;

export function useWebSocket(boardId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttemptsRef = useRef(0);
  const isIntentionalCloseRef = useRef(false);

  // Get store handlers - these are stable references from Zustand
  const handleTaskCreated = useBoardStore((state) => state.handleTaskCreated);
  const handleTaskUpdated = useBoardStore((state) => state.handleTaskUpdated);
  const handleTaskMoved = useBoardStore((state) => state.handleTaskMoved);
  const handleTaskDeleted = useBoardStore((state) => state.handleTaskDeleted);
  const handleColumnCreated = useBoardStore((state) => state.handleColumnCreated);
  const handleColumnUpdated = useBoardStore((state) => state.handleColumnUpdated);
  const handleColumnDeleted = useBoardStore((state) => state.handleColumnDeleted);
  const handleExecutionStarted = useBoardStore((state) => state.handleExecutionStarted);
  const handleExecutionUpdated = useBoardStore((state) => state.handleExecutionUpdated);
  const handleExecutionCompleted = useBoardStore((state) => state.handleExecutionCompleted);
  const handleExecutionMilestone = useBoardStore((state) => state.handleExecutionMilestone);

  // Validate boardId format (basic UUID validation)
  const isValidBoardId = useCallback((id: string): boolean => {
    const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return UUID_REGEX.test(id);
  }, []);

  // Message handler using refs to avoid stale closures
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);

      // Runtime validation of message structure
      if (!data || typeof data.type !== 'string') {
        console.error('Invalid WebSocket message format');
        return;
      }

      const message = data as WSEvent;

      switch (message.type) {
        case 'task_created':
          handleTaskCreated(message.data);
          break;
        case 'task_updated':
          handleTaskUpdated(message.data);
          break;
        case 'task_moved':
          handleTaskMoved(message.data);
          break;
        case 'task_deleted':
          handleTaskDeleted(message.data.task_id);
          break;
        case 'column_created':
          handleColumnCreated(message.data);
          break;
        case 'column_updated':
          handleColumnUpdated(message.data);
          break;
        case 'column_deleted':
          handleColumnDeleted(message.data.column_id);
          break;
        case 'execution_started': {
          const startedData = message.data ?? message.payload;
          if (startedData) handleExecutionStarted(startedData);
          break;
        }
        case 'execution_updated': {
          const updatedData = message.data ?? message.payload;
          if (updatedData) handleExecutionUpdated(updatedData);
          break;
        }
        case 'execution_completed': {
          const completedData = message.data ?? message.payload;
          if (completedData) handleExecutionCompleted(completedData);
          break;
        }
        case 'execution_milestone': {
          const milestoneData = message.data ?? message.payload;
          if (milestoneData) handleExecutionMilestone(milestoneData);
          break;
        }
        default:
          console.warn('Unknown WebSocket message type:', message);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [
    handleTaskCreated,
    handleTaskUpdated,
    handleTaskMoved,
    handleTaskDeleted,
    handleColumnCreated,
    handleColumnUpdated,
    handleColumnDeleted,
    handleExecutionStarted,
    handleExecutionUpdated,
    handleExecutionCompleted,
    handleExecutionMilestone,
  ]);

  useEffect(() => {
    if (!boardId) {
      return;
    }

    // Validate boardId before connecting
    if (!isValidBoardId(boardId)) {
      console.error('Invalid board ID format');
      return;
    }

    // Reset intentional close flag
    isIntentionalCloseRef.current = false;

    const connect = () => {
      // Check for both OPEN and CONNECTING states to prevent duplicate connections
      if (
        wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING
      ) {
        return;
      }

      const ws = new WebSocket(`${WS_URL}/ws/boards/${encodeURIComponent(boardId)}`);
      wsRef.current = ws;

      // Connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket connection timeout');
          ws.close();
        }
      }, 10000);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        console.log('WebSocket connected');
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        clearTimeout(connectionTimeout);
        // Don't log error if this was an intentional close (e.g., React StrictMode unmount)
        if (!isIntentionalCloseRef.current) {
          console.error('WebSocket error:', error);
        }
      };

      ws.onclose = () => {
        clearTimeout(connectionTimeout);
        // Don't log if this was an intentional close (e.g., React StrictMode unmount)
        if (!isIntentionalCloseRef.current) {
          console.log('WebSocket disconnected');
        }

        // Don't reconnect if this was an intentional close
        if (isIntentionalCloseRef.current) {
          return;
        }

        // Attempt reconnection with exponential backoff
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;

          // Exponential backoff with jitter
          const delay = Math.min(
            BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current - 1) +
            Math.random() * 1000,
            30000 // max delay
          );

          console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current} in ${Math.round(delay)}ms`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else {
          console.error('Max reconnection attempts reached');
        }
      };
    };

    connect();

    return () => {
      // Mark as intentional close to prevent reconnection
      isIntentionalCloseRef.current = true;

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = undefined;
      }

      if (wsRef.current) {
        // Only close if not already closed
        if (wsRef.current.readyState !== WebSocket.CLOSED) {
          wsRef.current.close();
        }
        wsRef.current = null;
      }
    };
  }, [boardId, isValidBoardId, handleMessage]);

  return wsRef.current;
}
