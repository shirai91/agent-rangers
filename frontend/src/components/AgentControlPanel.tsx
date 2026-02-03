import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Bot, Play, Code, FileCode, History, StopCircle } from 'lucide-react';
import type { AgentStatus } from '@/types';

interface AgentControlPanelProps {
  agentStatus: AgentStatus | null;
  onViewExecutions: () => void;
  onStartWorkflow: (workflowType: 'development' | 'quick_development' | 'architecture_only') => void;
  onCancelExecution?: () => void;
}

export function AgentControlPanel({
  agentStatus,
  onViewExecutions,
  onStartWorkflow,
  onCancelExecution,
}: AgentControlPanelProps) {
  const isRunning = agentStatus === 'running' || agentStatus === 'pending';
  const canStartWorkflow = !isRunning;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <Bot className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem
          onClick={() => onStartWorkflow('development')}
          disabled={!canStartWorkflow}
        >
          <Play className="mr-2 h-4 w-4" />
          Start Development Workflow
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => onStartWorkflow('quick_development')}
          disabled={!canStartWorkflow}
        >
          <Code className="mr-2 h-4 w-4" />
          Quick Development
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => onStartWorkflow('architecture_only')}
          disabled={!canStartWorkflow}
        >
          <FileCode className="mr-2 h-4 w-4" />
          Architecture Only
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onViewExecutions}>
          <History className="mr-2 h-4 w-4" />
          View Executions
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
  );
}
