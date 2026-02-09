import type {
  Board,
  Column,
  Task,
  CreateBoardInput,
  UpdateTaskInput,
  MoveTaskInput,
  WorkflowDefinition,
  WorkflowTransition,
  CreateWorkflowInput,
  UpdateWorkflowInput,
  CreateTransitionInput,
  UpdateTransitionInput,
  AllowedTarget,
  AllowedTransitionsMap,
  TaskActivity,
  TaskActivityListResponse,
  BoardActivityResponse,
  UpdateColumnInput,
  AgentExecution,
  StartAgentWorkflowInput,
  ExecutionStatusResponse,
  Repository,
  TaskEvaluation,
} from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT = 30000; // 30 seconds

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Custom error class for network errors
 */
export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

/**
 * Safely extract error message from unknown error
 */
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unknown error occurred';
}

/**
 * Makes a typed JSON request to the API with timeout support
 */
async function fetchJSON<T>(
  url: string,
  options?: RequestInit,
  timeout = DEFAULT_TIMEOUT
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_URL}${url}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      let errorCode: string | undefined;

      try {
        const errorData = await response.json();
        if (errorData.detail) {
          // Handle different detail formats consistently
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (Array.isArray(errorData.detail)) {
            // Pydantic validation errors - extract messages
            errorMessage = errorData.detail
              .map((err: { msg?: string; message?: string; loc?: string[] }) => 
                err.msg || err.message || JSON.stringify(err)
              )
              .join(', ');
          } else if (typeof errorData.detail === 'object') {
            // Object with message property
            errorMessage = errorData.detail.message || 
                          errorData.detail.msg || 
                          JSON.stringify(errorData.detail);
          }
          // Sanitize and truncate
          errorMessage = String(errorMessage).slice(0, 500);
        } else if (errorData.message) {
          // Alternative: top-level message property
          errorMessage = String(errorData.message).slice(0, 500);
        }
        errorCode = errorData.code;
      } catch {
        // Ignore JSON parse errors for error response
      }

      throw new ApiError(errorMessage, response.status, errorCode);
    }

    // Handle empty responses (e.g., 204 No Content for DELETE)
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) {
      return undefined as T;
    }

    const text = await response.text();
    if (!text) {
      return undefined as T;
    }

    return JSON.parse(text) as T;
  } catch (error) {
    clearTimeout(timeoutId);

    // Re-throw our custom errors
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }

    // Handle abort (timeout)
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new NetworkError('Request timed out. Please try again.');
    }

    // Handle network errors (offline, DNS failure, CORS, etc.)
    if (error instanceof TypeError) {
      throw new NetworkError('Network request failed. Please check your connection.');
    }

    // Unknown error
    throw new NetworkError(getErrorMessage(error));
  }
}

/**
 * Safely encode URL path parameter
 */
function encodeId(id: string): string {
  return encodeURIComponent(id);
}

export const api = {
  // Boards
  getBoards: () => fetchJSON<Board[]>('/api/boards'),

  getBoard: (id: string) => fetchJSON<Board>(`/api/boards/${encodeId(id)}`),

  createBoard: (data: CreateBoardInput) =>
    fetchJSON<Board>('/api/boards', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateBoard: (id: string, data: { name?: string; description?: string }) =>
    fetchJSON<Board>(`/api/boards/${encodeId(id)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteBoard: (id: string) =>
    fetchJSON<void>(`/api/boards/${encodeId(id)}`, {
      method: 'DELETE',
    }),

  // Columns
  getColumns: (boardId: string) =>
    fetchJSON<Column[]>(`/api/boards/${encodeId(boardId)}/columns`),

  createColumn: (boardId: string, data: { name: string }) =>
    fetchJSON<Column>(`/api/boards/${encodeId(boardId)}/columns`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateColumn: (id: string, data: { name: string }) =>
    fetchJSON<Column>(`/api/columns/${encodeId(id)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteColumn: (id: string) =>
    fetchJSON<void>(`/api/columns/${encodeId(id)}`, {
      method: 'DELETE',
    }),

  // Tasks
  getTasks: (boardId: string) =>
    fetchJSON<Task[]>(`/api/boards/${encodeId(boardId)}/tasks`),

  getTask: (id: string) => fetchJSON<Task>(`/api/tasks/${encodeId(id)}`),

  createTask: (boardId: string, data: { column_id: string; title: string; description?: string; assigned_to?: string; priority?: number }) =>
    fetchJSON<Task>(`/api/boards/${encodeId(boardId)}/tasks`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateTask: (id: string, data: UpdateTaskInput) =>
    fetchJSON<Task>(`/api/tasks/${encodeId(id)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  moveTask: (id: string, data: MoveTaskInput) =>
    fetchJSON<Task>(`/api/tasks/${encodeId(id)}/move`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteTask: (id: string) =>
    fetchJSON<void>(`/api/tasks/${encodeId(id)}`, {
      method: 'DELETE',
    }),

  // Workflows
  getWorkflows: (boardId: string) =>
    fetchJSON<WorkflowDefinition[]>(`/api/boards/${encodeId(boardId)}/workflows`),

  getActiveWorkflow: (boardId: string) =>
    fetchJSON<WorkflowDefinition>(`/api/boards/${encodeId(boardId)}/workflows/active`),

  createWorkflow: (boardId: string, data: CreateWorkflowInput) =>
    fetchJSON<WorkflowDefinition>(`/api/boards/${encodeId(boardId)}/workflows`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getWorkflow: (id: string) =>
    fetchJSON<WorkflowDefinition>(`/api/workflows/${encodeId(id)}`),

  updateWorkflow: (id: string, data: UpdateWorkflowInput) =>
    fetchJSON<WorkflowDefinition>(`/api/workflows/${encodeId(id)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteWorkflow: (id: string) =>
    fetchJSON<void>(`/api/workflows/${encodeId(id)}`, {
      method: 'DELETE',
    }),

  // Transitions
  getTransitions: (workflowId: string) =>
    fetchJSON<WorkflowTransition[]>(`/api/workflows/${encodeId(workflowId)}/transitions`),

  createTransition: (workflowId: string, data: CreateTransitionInput) =>
    fetchJSON<WorkflowTransition>(`/api/workflows/${encodeId(workflowId)}/transitions`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateTransition: (id: string, data: UpdateTransitionInput) =>
    fetchJSON<WorkflowTransition>(`/api/transitions/${encodeId(id)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteTransition: (id: string) =>
    fetchJSON<void>(`/api/transitions/${encodeId(id)}`, {
      method: 'DELETE',
    }),

  // Allowed Targets
  getAllowedTargets: (boardId: string, columnId: string) =>
    fetchJSON<AllowedTarget[]>(
      `/api/boards/${encodeId(boardId)}/columns/${encodeId(columnId)}/allowed-targets`
    ),

  getAllowedTransitions: (boardId: string) =>
    fetchJSON<AllowedTransitionsMap>(`/api/boards/${encodeId(boardId)}/allowed-transitions`),

  // Activities
  getTaskActivities: (taskId: string, page = 1, pageSize = 50) =>
    fetchJSON<TaskActivityListResponse>(
      `/api/tasks/${encodeId(taskId)}/activities?page=${page}&page_size=${pageSize}`
    ),

  getBoardActivities: (boardId: string, page = 1, pageSize = 50) =>
    fetchJSON<BoardActivityResponse>(
      `/api/boards/${encodeId(boardId)}/activities?page=${page}&page_size=${pageSize}`
    ),

  getRecentBoardActivities: (boardId: string, limit = 20) =>
    fetchJSON<TaskActivity[]>(
      `/api/boards/${encodeId(boardId)}/activities/recent?limit=${limit}`
    ),

  // Column Settings Update
  updateColumnSettings: (id: string, data: UpdateColumnInput) =>
    fetchJSON<Column>(`/api/columns/${encodeId(id)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // Agent Workflow
  startAgentWorkflow: (taskId: string, data: StartAgentWorkflowInput) =>
    fetchJSON<AgentExecution>(`/api/agents/tasks/${encodeId(taskId)}/agent/start`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getTaskPlans: (taskId: string) =>
    fetchJSON<Array<{ execution_id: string; created_at: string; plan_filename: string | null; plan_preview: string; task_title: string }>>(`/api/agents/tasks/${encodeId(taskId)}/plans`),

  getExecution: (executionId: string) =>
    fetchJSON<AgentExecution>(`/api/agents/executions/${encodeId(executionId)}`),

  getExecutionStatus: (executionId: string) =>
    fetchJSON<ExecutionStatusResponse>(`/api/agents/executions/${encodeId(executionId)}/status`),

  cancelExecution: (executionId: string) =>
    fetchJSON<void>(`/api/agents/executions/${encodeId(executionId)}`, {
      method: 'DELETE',
    }),

  submitClarification: (executionId: string, answers: Record<string, unknown>) =>
    fetchJSON<AgentExecution>(`/api/agents/executions/${encodeId(executionId)}/clarify`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    }),

  skipClarification: (executionId: string) =>
    fetchJSON<AgentExecution>(`/api/agents/executions/${encodeId(executionId)}/skip-clarification`, {
      method: 'POST',
    }),

  getTaskExecutions: (taskId: string, limit?: number) =>
    fetchJSON<AgentExecution[]>(
      `/api/agents/tasks/${encodeId(taskId)}/executions${limit ? `?limit=${limit}` : ''}`
    ),

  getBoardExecutions: (boardId: string, statusFilter?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status', statusFilter);
    if (limit) params.append('limit', limit.toString());
    const queryString = params.toString();
    return fetchJSON<AgentExecution[]>(
      `/api/agents/boards/${encodeId(boardId)}/executions${queryString ? `?${queryString}` : ''}`
    );
  },

  // Board Settings - Working Directory
  setWorkingDirectory: (boardId: string, directory: string) =>
    fetchJSON<Board>(`/api/boards/${encodeId(boardId)}/working-directory`, {
      method: 'PATCH',
      body: JSON.stringify({ working_directory: directory }),
    }),

  // Repository Scanning
  getRepositories: (boardId: string) =>
    fetchJSON<Repository[]>(`/api/boards/${encodeId(boardId)}/repositories`),

  scanRepositories: (boardId: string) =>
    fetchJSON<Repository[]>(`/api/boards/${encodeId(boardId)}/repositories/scan`, {
      method: 'POST',
    }),

  // Task Evaluation
  getTaskEvaluation: (taskId: string) =>
    fetchJSON<TaskEvaluation>(`/api/tasks/${encodeId(taskId)}/evaluation`),

  triggerTaskEvaluation: (taskId: string) =>
    fetchJSON<TaskEvaluation>(`/api/tasks/${encodeId(taskId)}/evaluation`, {
      method: 'POST',
    }),
};
