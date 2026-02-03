import type {
  Board,
  Column,
  Task,
  CreateBoardInput,
  UpdateTaskInput,
  MoveTaskInput,
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
          // Sanitize error message to prevent XSS
          errorMessage = String(errorData.detail).slice(0, 500);
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

  createTask: (boardId: string, data: { column_id: string; title: string; description?: string; assigned_to?: string; priority?: string }) =>
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
};
