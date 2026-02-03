import { useMemo, useCallback } from 'react';
import { createMachine, assign } from 'xstate';
import { useMachine } from '@xstate/react';
import type { Column, WorkflowDefinition, WorkflowTransition, AllowedTransitionsMap } from '@/types';

// Types for the workflow state machine
interface WorkflowContext {
  columns: Column[];
  workflow: WorkflowDefinition | null;
  transitions: WorkflowTransition[];
  allowedTransitions: AllowedTransitionsMap;
  currentColumnId: string | null;
  error: string | null;
}

type WorkflowEvent =
  | { type: 'LOAD'; columns: Column[]; workflow: WorkflowDefinition | null }
  | { type: 'SET_ALLOWED_TRANSITIONS'; transitions: AllowedTransitionsMap }
  | { type: 'SELECT_COLUMN'; columnId: string }
  | { type: 'CLEAR_SELECTION' }
  | { type: 'ADD_TRANSITION'; from: string; to: string }
  | { type: 'REMOVE_TRANSITION'; from: string; to: string }
  | { type: 'ERROR'; message: string }
  | { type: 'CLEAR_ERROR' };

// Create the workflow state machine
const createWorkflowMachine = () =>
  createMachine({
    id: 'workflow',
    initial: 'idle',
    types: {} as {
      context: WorkflowContext;
      events: WorkflowEvent;
    },
    context: {
      columns: [],
      workflow: null,
      transitions: [],
      allowedTransitions: {},
      currentColumnId: null,
      error: null,
    },
    states: {
      idle: {
        on: {
          LOAD: {
            target: 'ready',
            actions: assign({
              columns: ({ event }) => event.columns,
              workflow: ({ event }) => event.workflow,
              transitions: ({ event }) => event.workflow?.transitions || [],
              allowedTransitions: ({ event }) => {
                // Build allowed transitions map from workflow
                if (!event.workflow) {
                  // No workflow = all transitions allowed
                  const columnIds = event.columns.map((c) => c.id);
                  const map: AllowedTransitionsMap = {};
                  columnIds.forEach((id) => {
                    map[id] = [...columnIds];
                  });
                  return map;
                }
                // Build from transitions
                const map: AllowedTransitionsMap = {};
                event.columns.forEach((c) => {
                  map[c.id] = [];
                });
                (event.workflow.transitions || []).forEach((t) => {
                  const arr = map[t.from_column_id];
                  if (t.is_enabled && arr) {
                    arr.push(t.to_column_id);
                  }
                });
                return map;
              },
            }),
          },
        },
      },
      ready: {
        on: {
          LOAD: {
            actions: assign({
              columns: ({ event }) => event.columns,
              workflow: ({ event }) => event.workflow,
              transitions: ({ event }) => event.workflow?.transitions || [],
              allowedTransitions: ({ event }) => {
                if (!event.workflow) {
                  const columnIds = event.columns.map((c) => c.id);
                  const map: AllowedTransitionsMap = {};
                  columnIds.forEach((id) => {
                    map[id] = [...columnIds];
                  });
                  return map;
                }
                const map: AllowedTransitionsMap = {};
                event.columns.forEach((c) => {
                  map[c.id] = [];
                });
                (event.workflow.transitions || []).forEach((t) => {
                  const arr = map[t.from_column_id];
                  if (t.is_enabled && arr) {
                    arr.push(t.to_column_id);
                  }
                });
                return map;
              },
            }),
          },
          SET_ALLOWED_TRANSITIONS: {
            actions: assign({
              allowedTransitions: ({ event }) => event.transitions,
            }),
          },
          SELECT_COLUMN: {
            actions: assign({
              currentColumnId: ({ event }) => event.columnId,
            }),
          },
          CLEAR_SELECTION: {
            actions: assign({
              currentColumnId: () => null,
            }),
          },
          ADD_TRANSITION: {
            actions: assign({
              allowedTransitions: ({ context, event }) => {
                const map = { ...context.allowedTransitions };
                const existing = map[event.from] || [];
                if (!existing.includes(event.to)) {
                  map[event.from] = [...existing, event.to];
                }
                return map;
              },
            }),
          },
          REMOVE_TRANSITION: {
            actions: assign({
              allowedTransitions: ({ context, event }) => {
                const map = { ...context.allowedTransitions };
                const existing = map[event.from];
                if (existing) {
                  map[event.from] = existing.filter((id) => id !== event.to);
                }
                return map;
              },
            }),
          },
          ERROR: {
            actions: assign({
              error: ({ event }) => event.message,
            }),
          },
          CLEAR_ERROR: {
            actions: assign({
              error: () => null,
            }),
          },
        },
      },
    },
  });

/**
 * Hook for managing workflow state using XState
 */
export function useWorkflow() {
  const machine = useMemo(() => createWorkflowMachine(), []);
  const [state, send] = useMachine(machine);

  const load = useCallback(
    (columns: Column[], workflow: WorkflowDefinition | null) => {
      send({ type: 'LOAD', columns, workflow });
    },
    [send]
  );

  const setAllowedTransitions = useCallback(
    (transitions: AllowedTransitionsMap) => {
      send({ type: 'SET_ALLOWED_TRANSITIONS', transitions });
    },
    [send]
  );

  const selectColumn = useCallback(
    (columnId: string) => {
      send({ type: 'SELECT_COLUMN', columnId });
    },
    [send]
  );

  const clearSelection = useCallback(() => {
    send({ type: 'CLEAR_SELECTION' });
  }, [send]);

  const addTransition = useCallback(
    (from: string, to: string) => {
      send({ type: 'ADD_TRANSITION', from, to });
    },
    [send]
  );

  const removeTransition = useCallback(
    (from: string, to: string) => {
      send({ type: 'REMOVE_TRANSITION', from, to });
    },
    [send]
  );

  const isTransitionAllowed = useCallback(
    (fromColumnId: string, toColumnId: string): boolean => {
      // Same column always allowed
      if (fromColumnId === toColumnId) return true;

      const allowed = state.context.allowedTransitions[fromColumnId];
      if (!allowed) return true; // No restrictions
      return allowed.includes(toColumnId);
    },
    [state.context.allowedTransitions]
  );

  const getAllowedTargets = useCallback(
    (fromColumnId: string): string[] => {
      return state.context.allowedTransitions[fromColumnId] || [];
    },
    [state.context.allowedTransitions]
  );

  return {
    // State
    columns: state.context.columns,
    workflow: state.context.workflow,
    transitions: state.context.transitions,
    allowedTransitions: state.context.allowedTransitions,
    currentColumnId: state.context.currentColumnId,
    error: state.context.error,
    isReady: state.matches('ready'),

    // Actions
    load,
    setAllowedTransitions,
    selectColumn,
    clearSelection,
    addTransition,
    removeTransition,

    // Helpers
    isTransitionAllowed,
    getAllowedTargets,
  };
}

export type WorkflowHook = ReturnType<typeof useWorkflow>;
