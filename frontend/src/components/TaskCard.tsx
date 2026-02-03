import { useState } from 'react';
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
import { MoreVertical, Trash2, Edit, GripVertical } from 'lucide-react';
import type { Task, AgentStatus, WorkflowType } from '@/types';
import { useBoardStore } from '@/stores/boardStore';
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
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await deleteTask(task.id);
      } catch (error) {
        console.error('Failed to delete task:', error);
      }
    }
  };

  const getPriorityColor = (priority: string | null) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      case 'low':
        return 'secondary';
      default:
        return 'outline';
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

  return (
    <div ref={setNodeRef} style={style}>
      <Card className="mb-2 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow">
        <CardHeader className="p-4 pb-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1 min-w-0">
              <button
                className="mt-1 cursor-grab touch-none text-muted-foreground hover:text-foreground"
                {...attributes}
                {...listeners}
              >
                <GripVertical className="h-4 w-4" />
              </button>
              <div className="flex-1 min-w-0">
                <CardTitle className="text-sm font-medium break-words">
                  {task.title}
                </CardTitle>
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
                  <DropdownMenuItem onClick={handleDelete}>
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
            {task.priority && (
              <Badge variant={getPriorityColor(task.priority)}>
                {task.priority}
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
          <AgentExecutionPanel taskId={task.id} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
