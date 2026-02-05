import { useState, useEffect } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { MoreVertical, Trash2, Edit, GripVertical, GitBranch, Loader2 } from 'lucide-react';
import type { Task, AgentStatus, WorkflowType, TaskEvaluation } from '@/types';
import { useBoardStore } from '@/stores/boardStore';
import { api } from '@/api/client';
import { AgentStatusBadge } from './AgentStatusBadge';
import { AgentControlPanel } from './AgentControlPanel';
import { AgentExecutionPanel } from './AgentExecutionPanel';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
}

export function TaskCard({ task, onEdit }: TaskCardProps) {
  const { deleteTask, startAgentWorkflow, cancelExecution } = useBoardStore();
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [evaluation, setEvaluation] = useState<TaskEvaluation | null>(null);
  const [evaluationLoading, setEvaluationLoading] = useState(false);
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  // Fetch evaluation on mount
  useEffect(() => {
    let mounted = true;
    setEvaluationLoading(true);
    api.getTaskEvaluation(task.id)
      .then((result) => {
        if (mounted) {
          setEvaluation(result);
        }
      })
      .catch(() => {
        // No evaluation available, that's fine
        if (mounted) {
          setEvaluation(null);
        }
      })
      .finally(() => {
        if (mounted) {
          setEvaluationLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [task.id]);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleDelete = async () => {
    try {
      await deleteTask(task.id);
      setShowDeleteDialog(false);
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const getPriorityColor = (priority: number | null) => {
    // Priority mapping: 0=none, 1=low, 2=medium, 3=high, 4=critical
    switch (priority) {
      case 4: // critical
        return 'destructive';
      case 3: // high
        return 'destructive';
      case 2: // medium
        return 'default';
      case 1: // low
        return 'secondary';
      default: // 0 or null (none)
        return 'outline';
    }
  };

  const getPriorityLabel = (priority: number | null): string => {
    // Priority mapping: 0=none, 1=low, 2=medium, 3=high, 4=critical
    switch (priority) {
      case 4:
        return 'Critical';
      case 3:
        return 'High';
      case 2:
        return 'Medium';
      case 1:
        return 'Low';
      default:
        return 'None';
    }
  };

  const handleStartWorkflow = async (workflowType: WorkflowType) => {
    try {
      await startAgentWorkflow(task.id, workflowType);
    } catch (error) {
      console.error('Failed to start agent workflow:', error);
    }
  };

  const handleCancelExecution = async () => {
    if (task.current_execution_id) {
      try {
        await cancelExecution(task.current_execution_id);
      } catch (error) {
        console.error('Failed to cancel execution:', error);
      }
    }
  };

  const handleViewExecutions = () => {
    setShowExecutionPanel(true);
  };

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger if clicking on buttons, dropdowns, or grip handle
    const target = e.target as HTMLElement;
    if (
      target.closest('button') ||
      target.closest('[role="menu"]') ||
      target.closest('[data-grip-handle]')
    ) {
      return;
    }
    // Open execution history panel on card click
    setShowExecutionPanel(true);
  };

  return (
    <div ref={setNodeRef} style={style}>
      <Card 
        className="mb-2 cursor-pointer hover:shadow-md transition-shadow"
        onClick={handleCardClick}
      >
        <CardHeader className="p-4 pb-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1 min-w-0">
              <button
                data-grip-handle
                className="mt-1 cursor-grab active:cursor-grabbing touch-none text-muted-foreground hover:text-foreground"
                {...attributes}
                {...listeners}
              >
                <GripVertical className="h-4 w-4" />
              </button>
              <div className="flex-1 min-w-0">
                <CardTitle className="text-sm font-medium break-words">
                  {task.title}
                </CardTitle>
                {/* Repository badge from evaluation */}
                {evaluationLoading ? (
                  <div className="mt-1">
                    <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                  </div>
                ) : evaluation?.repository ? (
                  <div className="mt-1">
                    <Badge variant="outline" className="text-xs font-normal gap-1">
                      <GitBranch className="h-3 w-3" />
                      {evaluation.repository.name}
                    </Badge>
                  </div>
                ) : null}
                {task.agent_status && (
                  <div className="mt-1">
                    <AgentStatusBadge status={task.agent_status as AgentStatus} />
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <AgentControlPanel
                agentStatus={task.agent_status as AgentStatus | null}
                onViewExecutions={handleViewExecutions}
                onStartWorkflow={handleStartWorkflow}
                onCancelExecution={task.current_execution_id ? handleCancelExecution : undefined}
              />
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onEdit(task)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setShowDeleteDialog(true)}
                    className="text-red-600 focus:text-red-600 focus:bg-red-50"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-4 pt-2">
          {task.description && (
            <p className="text-sm text-muted-foreground mb-3 line-clamp-3">
              {task.description}
            </p>
          )}
          <div className="flex items-center gap-2 flex-wrap">
            {task.priority !== null && task.priority !== 0 && (
              <Badge variant={getPriorityColor(task.priority)}>
                {getPriorityLabel(task.priority)}
              </Badge>
            )}
            {task.assigned_to && (
              <Badge variant="outline" className="text-xs">
                {task.assigned_to}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showExecutionPanel} onOpenChange={setShowExecutionPanel}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Agent Executions - {task.title}</DialogTitle>
          </DialogHeader>
          <AgentExecutionPanel
            taskId={task.id}
            evaluation={evaluation}
            onEvaluationUpdate={setEvaluation}
          />
        </DialogContent>
      </Dialog>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{task.title}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleDelete}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
