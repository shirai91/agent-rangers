import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  PlayCircle,
  StopCircle,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  Box,
  Workflow,
} from 'lucide-react';
import { useBoardStore } from '@/stores/boardStore';
import type { AgentExecution, WorkflowType } from '@/types';
import { ExecutionDetails } from './ExecutionDetails';

interface AgentExecutionPanelProps {
  taskId: string;
}

export function AgentExecutionPanel({
  taskId,
}: AgentExecutionPanelProps) {
  const {
    executions,
    currentExecution,
    executionLoading,
    fetchTaskExecutions,
    startAgentWorkflow,
    cancelExecution,
    setCurrentExecution,
  } = useBoardStore();

  const [selectedExecution, setSelectedExecution] = useState<AgentExecution | null>(null);
  const [startingWorkflow, setStartingWorkflow] = useState(false);

  useEffect(() => {
    if (taskId) {
      fetchTaskExecutions(taskId);
    }
  }, [taskId, fetchTaskExecutions]);

  useEffect(() => {
    // Auto-select current execution if exists
    if (currentExecution && currentExecution.task_id === taskId) {
      setSelectedExecution(currentExecution);
    } else if (executions.length > 0 && !selectedExecution) {
      // Select most recent execution
      const firstExecution = executions[0];
      if (firstExecution) {
        setSelectedExecution(firstExecution);
      }
    }
  }, [currentExecution, executions, taskId, selectedExecution]);

  const handleStartWorkflow = async (workflowType: WorkflowType) => {
    setStartingWorkflow(true);
    try {
      const execution = await startAgentWorkflow(taskId, workflowType);
      setSelectedExecution(execution);
      setCurrentExecution(execution);
    } catch (error) {
      console.error('Failed to start workflow:', error);
    } finally {
      setStartingWorkflow(false);
    }
  };

  const handleCancelExecution = async (executionId: string) => {
    try {
      await cancelExecution(executionId);
      // Refresh executions
      await fetchTaskExecutions(taskId);
    } catch (error) {
      console.error('Failed to cancel execution:', error);
    }
  };

  const handleRefresh = () => {
    fetchTaskExecutions(taskId);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-destructive" />;
      case 'running':
        return <PlayCircle className="h-4 w-4 text-blue-600 animate-pulse" />;
      case 'cancelled':
        return <AlertCircle className="h-4 w-4 text-muted-foreground" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const runningExecution = executions.find((e) => e.status === 'running');

  return (
    <div className="space-y-4">
          {/* Start workflow section */}
          <div className="bg-muted/50 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-sm">Start New Workflow</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Choose a workflow type to begin agent execution
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRefresh}
                disabled={executionLoading}
              >
                <RefreshCw className={`h-4 w-4 ${executionLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>

            {runningExecution ? (
              <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-md">
                <div className="flex items-center gap-2">
                  <PlayCircle className="h-4 w-4 text-blue-600 animate-pulse" />
                  <span className="text-sm font-medium">Workflow Running</span>
                  <Badge variant="secondary" className="text-xs">
                    {runningExecution.workflow_type}
                  </Badge>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleCancelExecution(runningExecution.id)}
                  disabled={executionLoading}
                >
                  <StopCircle className="h-4 w-4 mr-1" />
                  Cancel
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleStartWorkflow('architecture_only')}
                  disabled={startingWorkflow || executionLoading}
                  className="flex flex-col items-center gap-1 h-auto py-3"
                >
                  <Box className="h-4 w-4" />
                  <span className="text-xs">Architecture</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleStartWorkflow('quick_development')}
                  disabled={startingWorkflow || executionLoading}
                  className="flex flex-col items-center gap-1 h-auto py-3"
                >
                  <Zap className="h-4 w-4" />
                  <span className="text-xs">Quick Dev</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleStartWorkflow('development')}
                  disabled={startingWorkflow || executionLoading}
                  className="flex flex-col items-center gap-1 h-auto py-3"
                >
                  <Workflow className="h-4 w-4" />
                  <span className="text-xs">Full Dev</span>
                </Button>
              </div>
            )}
          </div>

          {/* Execution history */}
          <div>
            <h3 className="font-semibold text-sm mb-3">Execution History</h3>

            {executionLoading && !executions.length ? (
              <div className="space-y-3">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </div>
            ) : executions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <PlayCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No executions yet</p>
                <p className="text-xs mt-1">Start a workflow to see execution history</p>
              </div>
            ) : (
              <div className="space-y-2">
                {/* Execution list */}
                <div className="space-y-2 mb-4">
                  {executions.slice(0, 5).map((execution) => (
                    <button
                      key={execution.id}
                      onClick={() => setSelectedExecution(execution)}
                      className={`w-full text-left p-3 rounded-md border transition-colors ${
                        selectedExecution?.id === execution.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:bg-muted/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(execution.status)}
                          <div>
                            <div className="text-sm font-medium">
                              {execution.workflow_type.replace(/_/g, ' ')}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {formatDateTime(execution.started_at)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {execution.current_phase && (
                            <Badge variant="secondary" className="text-xs">
                              {execution.current_phase}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {/* Selected execution details */}
                {selectedExecution && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-sm">Execution Details</h4>
                      {selectedExecution.status === 'running' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleRefresh}
                        >
                          <RefreshCw className="h-3 w-3 mr-1" />
                          Refresh
                        </Button>
                      )}
                    </div>
                    <ExecutionDetails execution={selectedExecution} />
                  </div>
                )}
              </div>
            )}
          </div>
    </div>
  );
}
