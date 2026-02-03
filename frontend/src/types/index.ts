export interface Board {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Column {
  id: string;
  board_id: string;
  name: string;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  column_id: string;
  title: string;
  description: string | null;
  assigned_to: string | null;
  status: string;
  priority: string | null;
  order: number;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface CreateBoardInput {
  name: string;
  description?: string;
}

export interface CreateColumnInput {
  name: string;
}

export interface CreateTaskInput {
  column_id: string;
  title: string;
  description?: string;
  assigned_to?: string;
  priority?: string;
}

export interface UpdateBoardInput {
  name?: string;
  description?: string;
}

export interface UpdateTaskInput {
  title?: string;
  description?: string;
  assigned_to?: string;
  status?: string;
  priority?: string;
}

export interface MoveTaskInput {
  column_id: string;
  order: number;
  version: number;
}

export type WSEvent =
  | { type: 'task_created'; data: Task }
  | { type: 'task_updated'; data: Task }
  | { type: 'task_moved'; data: Task }
  | { type: 'task_deleted'; data: { task_id: string } }
  | { type: 'column_created'; data: Column }
  | { type: 'column_updated'; data: Column }
  | { type: 'column_deleted'; data: { column_id: string } };
