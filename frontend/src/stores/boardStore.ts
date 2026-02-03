import { create } from 'zustand';
import type {
  Board,
  Column,
  Task,
  CreateBoardInput,
  CreateColumnInput,
  CreateTaskInput,
  UpdateTaskInput,
  MoveTaskInput,
  WorkflowDefinition,
  AllowedTransitionsMap,
  TaskActivity,
  UpdateColumnInput,
  AgentExecution,
  WorkflowType,
} from '@/types';
import { api, ApiError, NetworkError } from '@/api/client';

/**
 * Safely extract error message from unknown error
 */
function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof NetworkError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unknown error occurred';
}

interface BoardState {
  boards: Board[];
  currentBoard: Board | null;
  columns: Column[];
  tasks: Task[];
  loading: boolean;
  error: string | null;

  // Workflow state
  activeWorkflow: WorkflowDefinition | null;
  allowedTransitions: AllowedTransitionsMap;
  workflowLoading: boolean;

  // Activity state
  activities: TaskActivity[];
  activitiesLoading: boolean;

  // Agent execution state
  executions: AgentExecution[];
  currentExecution: AgentExecution | null;
  executionLoading: boolean;

  // Actions
  fetchBoards: () => Promise<void>;
  fetchBoard: (id: string) => Promise<void>;
  createBoard: (data: CreateBoardInput) => Promise<Board>;
  deleteBoard: (id: string) => Promise<void>;

  createColumn: (boardId: string, data: CreateColumnInput) => Promise<Column>;
  updateColumn: (id: string, data: { name: string }) => Promise<Column>;
  updateColumnSettings: (id: string, data: UpdateColumnInput) => Promise<Column>;
  deleteColumn: (id: string) => Promise<void>;

  createTask: (boardId: string, data: CreateTaskInput) => Promise<Task>;
  updateTask: (id: string, data: UpdateTaskInput) => Promise<Task>;
  moveTask: (id: string, data: MoveTaskInput, originalTask?: Task) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;

  // Workflow actions
  fetchAllowedTransitions: (boardId: string) => Promise<void>;
  fetchActiveWorkflow: (boardId: string) => Promise<void>;
  isTransitionAllowed: (fromColumnId: string, toColumnId: string) => boolean;

  // Activity actions
  fetchBoardActivities: (boardId: string) => Promise<void>;
  fetchTaskActivities: (taskId: string) => Promise<TaskActivity[]>;

  // Agent execution actions
  startAgentWorkflow: (taskId: string, workflowType: WorkflowType, context?: Record<string, unknown>) => Promise<AgentExecution>;
  fetchTaskExecutions: (taskId: string) => Promise<AgentExecution[]>;
  fetchBoardExecutions: (boardId: string, statusFilter?: string) => Promise<void>;
  cancelExecution: (executionId: string) => Promise<void>;
  setCurrentExecution: (execution: AgentExecution | null) => void;

  // Optimistic updates
  optimisticMoveTask: (taskId: string, newColumnId: string, newOrder: number) => Task | null;
  revertOptimisticMove: (originalTask: Task) => void;
  clearError: () => void;

  // WebSocket handlers
  handleTaskCreated: (task: Task) => void;
  handleTaskUpdated: (task: Task) => void;
  handleTaskMoved: (task: Task) => void;
  handleTaskDeleted: (taskId: string) => void;
  handleColumnCreated: (column: Column) => void;
  handleColumnUpdated: (column: Column) => void;
  handleColumnDeleted: (columnId: string) => void;
  handleActivityCreated: (activity: TaskActivity) => void;
  handleAgentStarted: (data: { task_id: string; execution_id: string }) => void;
  handleAgentPhaseCompleted: (data: { execution_id: string; phase: string }) => void;
  handleAgentCompleted: (data: { task_id: string; execution_id: string }) => void;
  handleAgentFailed: (data: { task_id: string; error: string }) => void;

  // Reset
  reset: () => void;
}

export const useBoardStore = create<BoardState>((set, get) => ({
  boards: [],
  currentBoard: null,
  columns: [],
  tasks: [],
  loading: false,
  error: null,

  // Workflow state
  activeWorkflow: null,
  allowedTransitions: {},
  workflowLoading: false,

  // Activity state
  activities: [],
  activitiesLoading: false,

  // Agent execution state
  executions: [],
  currentExecution: null,
  executionLoading: false,

  fetchBoards: async () => {
    set({ loading: true, error: null });
    try {
      const boards = await api.getBoards();
      set({ boards, loading: false });
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
    }
  },

  fetchBoard: async (id: string) => {
    set({ loading: true, error: null, workflowLoading: true });
    try {
      const [board, columns, tasks, allowedTransitions] = await Promise.all([
        api.getBoard(id),
        api.getColumns(id),
        api.getTasks(id),
        api.getAllowedTransitions(id),
      ]);
      set({
        currentBoard: board,
        columns,
        tasks,
        allowedTransitions,
        loading: false,
        workflowLoading: false,
      });

      // Try to fetch active workflow (optional)
      try {
        const workflow = await api.getActiveWorkflow(id);
        set({ activeWorkflow: workflow });
      } catch {
        // No active workflow is fine
        set({ activeWorkflow: null });
      }
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false, workflowLoading: false });
    }
  },

  createBoard: async (data: CreateBoardInput) => {
    set({ loading: true, error: null });
    try {
      const board = await api.createBoard(data);
      set((state) => ({
        boards: [...state.boards, board],
        loading: false,
      }));
      return board;
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  deleteBoard: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await api.deleteBoard(id);
      set((state) => ({
        boards: state.boards.filter((b) => b.id !== id),
        currentBoard: state.currentBoard?.id === id ? null : state.currentBoard,
        loading: false,
      }));
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  createColumn: async (boardId: string, data: CreateColumnInput) => {
    set({ loading: true, error: null });
    try {
      const column = await api.createColumn(boardId, data);
      set((state) => ({
        columns: [...state.columns, column],
        loading: false,
      }));
      return column;
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  updateColumn: async (id: string, data: { name: string }) => {
    set({ loading: true, error: null });
    try {
      const column = await api.updateColumn(id, data);
      set((state) => ({
        columns: state.columns.map((c) => (c.id === id ? column : c)),
        loading: false,
      }));
      return column;
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  updateColumnSettings: async (id: string, data: UpdateColumnInput) => {
    set({ loading: true, error: null });
    try {
      const column = await api.updateColumnSettings(id, data);
      set((state) => ({
        columns: state.columns.map((c) => (c.id === id ? column : c)),
        loading: false,
      }));
      return column;
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  deleteColumn: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await api.deleteColumn(id);
      set((state) => ({
        columns: state.columns.filter((c) => c.id !== id),
        tasks: state.tasks.filter((t) => t.column_id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  createTask: async (boardId: string, data: CreateTaskInput) => {
    set({ loading: true, error: null });
    try {
      const task = await api.createTask(boardId, data);
      set((state) => ({
        tasks: [...state.tasks, task],
        loading: false,
      }));
      return task;
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  updateTask: async (id: string, data: UpdateTaskInput) => {
    set({ loading: true, error: null });
    try {
      const task = await api.updateTask(id, data);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? task : t)),
        loading: false,
      }));
      return task;
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  moveTask: async (id: string, data: MoveTaskInput, originalTask?: Task) => {
    try {
      const updatedTask = await api.moveTask(id, data);
      // Update local state with the server response (includes new version)
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? updatedTask : t)),
      }));
    } catch (error) {
      // Revert optimistic update using the original task state
      if (originalTask) {
        get().revertOptimisticMove(originalTask);
      }
      set({ error: getErrorMessage(error) });
      throw error;
    }
  },

  deleteTask: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await api.deleteTask(id);
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  // Workflow actions
  fetchAllowedTransitions: async (boardId: string) => {
    set({ workflowLoading: true });
    try {
      const allowedTransitions = await api.getAllowedTransitions(boardId);
      set({ allowedTransitions, workflowLoading: false });
    } catch (error) {
      set({ workflowLoading: false });
    }
  },

  fetchActiveWorkflow: async (boardId: string) => {
    set({ workflowLoading: true });
    try {
      const workflow = await api.getActiveWorkflow(boardId);
      set({ activeWorkflow: workflow, workflowLoading: false });
    } catch {
      // No active workflow is fine
      set({ activeWorkflow: null, workflowLoading: false });
    }
  },

  isTransitionAllowed: (fromColumnId: string, toColumnId: string): boolean => {
    // Same column always allowed
    if (fromColumnId === toColumnId) return true;

    const { allowedTransitions } = get();
    // If no transitions defined, all are allowed
    if (Object.keys(allowedTransitions).length === 0) return true;

    const allowed = allowedTransitions[fromColumnId];
    if (!allowed) return true; // No restrictions for this column
    return allowed.includes(toColumnId);
  },

  // Activity actions
  fetchBoardActivities: async (boardId: string) => {
    set({ activitiesLoading: true });
    try {
      const response = await api.getRecentBoardActivities(boardId, 50);
      set({ activities: response, activitiesLoading: false });
    } catch (error) {
      set({ activitiesLoading: false });
    }
  },

  fetchTaskActivities: async (taskId: string) => {
    try {
      const response = await api.getTaskActivities(taskId);
      return response.items;
    } catch {
      return [];
    }
  },

  // Agent execution actions
  startAgentWorkflow: async (taskId: string, workflowType: WorkflowType, context?: Record<string, unknown>) => {
    set({ executionLoading: true, error: null });
    try {
      const execution = await api.startAgentWorkflow(taskId, {
        workflow_type: workflowType,
        context,
      });
      set((state) => ({
        executions: [execution, ...state.executions],
        currentExecution: execution,
        executionLoading: false,
      }));
      return execution;
    } catch (error) {
      set({ error: getErrorMessage(error), executionLoading: false });
      throw error;
    }
  },

  fetchTaskExecutions: async (taskId: string) => {
    set({ executionLoading: true });
    try {
      const executions = await api.getTaskExecutions(taskId);
      set({ executions, executionLoading: false });
      return executions;
    } catch (error) {
      set({ executionLoading: false });
      return [];
    }
  },

  fetchBoardExecutions: async (boardId: string, statusFilter?: string) => {
    set({ executionLoading: true });
    try {
      const executions = await api.getBoardExecutions(boardId, statusFilter);
      set({ executions, executionLoading: false });
    } catch (error) {
      set({ executionLoading: false });
    }
  },

  cancelExecution: async (executionId: string) => {
    set({ executionLoading: true, error: null });
    try {
      await api.cancelExecution(executionId);
      set((state) => ({
        executions: state.executions.map((e) =>
          e.id === executionId ? { ...e, status: 'cancelled' } : e
        ),
        currentExecution:
          state.currentExecution?.id === executionId
            ? { ...state.currentExecution, status: 'cancelled' }
            : state.currentExecution,
        executionLoading: false,
      }));
    } catch (error) {
      set({ error: getErrorMessage(error), executionLoading: false });
      throw error;
    }
  },

  setCurrentExecution: (execution: AgentExecution | null) => {
    set({ currentExecution: execution });
  },

  optimisticMoveTask: (taskId: string, newColumnId: string, newOrder: number) => {
    // Find and return the original task before updating
    const originalTask = get().tasks.find((t) => t.id === taskId) || null;

    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId
          ? { ...task, column_id: newColumnId, order: newOrder }
          : task
      ),
    }));

    return originalTask;
  },

  revertOptimisticMove: (originalTask: Task) => {
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === originalTask.id ? originalTask : task
      ),
    }));
  },

  clearError: () => {
    set({ error: null });
  },

  handleTaskCreated: (task: Task) => {
    set((state) => {
      const exists = state.tasks.some((t) => t.id === task.id);
      if (exists) return state;
      return { tasks: [...state.tasks, task] };
    });
  },

  handleTaskUpdated: (task: Task) => {
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
    }));
  },

  handleTaskMoved: (task: Task) => {
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
    }));
  },

  handleTaskDeleted: (taskId: string) => {
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== taskId),
    }));
  },

  handleColumnCreated: (column: Column) => {
    set((state) => {
      const exists = state.columns.some((c) => c.id === column.id);
      if (exists) return state;
      return { columns: [...state.columns, column] };
    });
  },

  handleColumnUpdated: (column: Column) => {
    set((state) => ({
      columns: state.columns.map((c) => (c.id === column.id ? column : c)),
    }));
  },

  handleColumnDeleted: (columnId: string) => {
    set((state) => ({
      columns: state.columns.filter((c) => c.id !== columnId),
      tasks: state.tasks.filter((t) => t.column_id !== columnId),
    }));
  },

  handleActivityCreated: (activity: TaskActivity) => {
    set((state) => ({
      activities: [activity, ...state.activities].slice(0, 100), // Keep last 100
    }));
  },

  handleAgentStarted: (data: { task_id: string; execution_id: string }) => {
    // Fetch the full execution details
    api.getExecution(data.execution_id)
      .then((execution) => {
        set((state) => {
          const exists = state.executions.some((e) => e.id === execution.id);
          if (exists) {
            return {
              executions: state.executions.map((e) =>
                e.id === execution.id ? execution : e
              ),
            };
          }
          return {
            executions: [execution, ...state.executions],
          };
        });
      })
      .catch(() => {
        // Silently handle error - execution will be fetched later
      });
  },

  handleAgentPhaseCompleted: (data: { execution_id: string; phase: string }) => {
    // Fetch updated execution details
    api.getExecution(data.execution_id)
      .then((execution) => {
        set((state) => ({
          executions: state.executions.map((e) =>
            e.id === execution.id ? execution : e
          ),
          currentExecution:
            state.currentExecution?.id === execution.id
              ? execution
              : state.currentExecution,
        }));
      })
      .catch(() => {
        // Silently handle error
      });
  },

  handleAgentCompleted: (data: { task_id: string; execution_id: string }) => {
    // Fetch updated execution details
    api.getExecution(data.execution_id)
      .then((execution) => {
        set((state) => ({
          executions: state.executions.map((e) =>
            e.id === execution.id ? execution : e
          ),
          currentExecution:
            state.currentExecution?.id === execution.id
              ? execution
              : state.currentExecution,
        }));
      })
      .catch(() => {
        // Silently handle error
      });

    // Also refresh the task to get updated agent status
    api.getTask(data.task_id)
      .then((task) => {
        get().handleTaskUpdated(task);
      })
      .catch(() => {
        // Silently handle error
      });
  },

  handleAgentFailed: (data: { task_id: string; error: string }) => {
    // Refresh task to get updated agent status
    api.getTask(data.task_id)
      .then((task) => {
        get().handleTaskUpdated(task);
      })
      .catch(() => {
        // Silently handle error
      });
  },

  reset: () => {
    set({
      boards: [],
      currentBoard: null,
      columns: [],
      tasks: [],
      loading: false,
      error: null,
      activeWorkflow: null,
      allowedTransitions: {},
      workflowLoading: false,
      activities: [],
      activitiesLoading: false,
      executions: [],
      currentExecution: null,
      executionLoading: false,
    });
  },
}));
