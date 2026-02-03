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
  color?: string | null;
  wip_limit?: number | null;
  triggers_agents: boolean;
  is_start_column: boolean;
  is_end_column: boolean;
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

// Workflow Types
export interface WorkflowDefinition {
  id: string;
  board_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  transitions?: WorkflowTransition[];
}

export interface WorkflowTransition {
  id: string;
  workflow_id: string;
  from_column_id: string;
  to_column_id: string;
  name: string | null;
  is_enabled: boolean;
  conditions: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkflowInput {
  name: string;
  description?: string;
  is_active?: boolean;
  settings?: Record<string, unknown>;
}

export interface UpdateWorkflowInput {
  name?: string;
  description?: string;
  is_active?: boolean;
  settings?: Record<string, unknown>;
}

export interface CreateTransitionInput {
  from_column_id: string;
  to_column_id: string;
  name?: string;
  is_enabled?: boolean;
  conditions?: Record<string, unknown>;
}

export interface UpdateTransitionInput {
  name?: string;
  is_enabled?: boolean;
  conditions?: Record<string, unknown>;
}

export interface AllowedTarget {
  column_id: string;
  column_name: string;
}

// Activity Types
export type ActivityType =
  | 'created'
  | 'updated'
  | 'moved'
  | 'deleted'
  | 'assigned'
  | 'unassigned'
  | 'priority_changed'
  | 'status_changed'
  | 'comment';

export interface TaskActivity {
  id: string;
  task_id: string;
  board_id: string;
  activity_type: ActivityType;
  actor: string;
  from_column_id: string | null;
  to_column_id: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  activity_metadata: Record<string, unknown>;
  created_at: string;
  from_column_name?: string | null;
  to_column_name?: string | null;
  task_title?: string | null;
}

export interface TaskActivityListResponse {
  items: TaskActivity[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface BoardActivityResponse {
  activities: TaskActivity[];
  total: number;
}

// Column settings update
export interface UpdateColumnInput {
  name?: string;
  color?: string;
  wip_limit?: number | null;
  triggers_agents?: boolean;
  is_start_column?: boolean;
  is_end_column?: boolean;
}

// Allowed transitions map
export type AllowedTransitionsMap = Record<string, string[]>;
