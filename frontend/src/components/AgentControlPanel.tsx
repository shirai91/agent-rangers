import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Bot, Play, Code, FileCode, History, StopCircle } from 'lucide-react';
import type { AgentStatus } from '@/types';

type WorkflowType = 'development' | 'quick_development' | 'architecture_only';

const workflowLabels: Record<WorkflowType, string> = {
  development: 'Start Development Workflow',
  quick_development: 'Quick Development',
  architecture_only: 'Architecture Only',
};

interface AgentControlPanelProps {
  agentStatus: AgentStatus | null;
  onViewExecutions: () => void;
  onStartWorkflow: (workflowType: WorkflowType) => void;
  onCancelExecution?: () => void;
}

export function AgentControlPanel({
  agentStatus,
  onViewExecutions,
  onStartWorkflow,
  onCancelExecution,
}: AgentControlPanelProps) {
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [pendingWorkflowType, setPendingWorkflowType] = useState<WorkflowType | null>(null);

  const isRunning = agentStatus === 'running' || agentStatus === 'pending';
  const canStartWorkflow = !isRunning;

  const handleWorkflowClick = (workflowType: WorkflowType) => {
    setPendingWorkflowType(workflowType);
    setConfirmDialogOpen(true);
  };

  const handleConfirm = () => {
    if (pendingWorkflowType) {
      onStartWorkflow(pendingWorkflowType);
    }
    setConfirmDialogOpen(false);
    setPendingWorkflowType(null);
  };

  const handleCancel = () => {
    setConfirmDialogOpen(false);
    setPendingWorkflowType(null);
  };

  return (
    <>
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Bot className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem onClick={onViewExecutions}>
          <History className="mr-2 h-4 w-4" />
          View Executions
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => handleWorkflowClick('development')}
          disabled={!canStartWorkflow}
        >
          <Play className="mr-2 h-4 w-4" />
          Start Development Workflow
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => handleWorkflowClick('quick_development')}
          disabled={!canStartWorkflow}
        >
          <Code className="mr-2 h-4 w-4" />
          Quick Development
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => handleWorkflowClick('architecture_only')}
          disabled={!canStartWorkflow}
        >
          <FileCode className="mr-2 h-4 w-4" />
          Architecture Only
        </DropdownMenuItem>
        {isRunning && onCancelExecution && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onCancelExecution}>
              <StopCircle className="mr-2 h-4 w-4" />
              Cancel Execution
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>

    <Dialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Workflow</DialogTitle>
          <DialogDescription>
            Are you sure you want to start "{pendingWorkflowType ? workflowLabels[pendingWorkflowType] : ''}"?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={handleCancel}>
            No
          </Button>
          <Button onClick={handleConfirm}>
            Yes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </>
  );
}
