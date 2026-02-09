import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
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
  GitBranch,
  FolderGit2,
  Sparkles,
  FileCode2,
  Loader2,
  FileText,
  HelpCircle,
} from 'lucide-react';
import { useBoardStore } from '@/stores/boardStore';
import { api } from '@/api/client';
import type { AgentExecution, WorkflowType, TaskEvaluation, AvailablePlan } from '@/types';
import { ExecutionDetails } from './ExecutionDetails';
import { ClarificationDialog } from './ClarificationDialog';

interface AgentExecutionPanelProps {
  taskId: string;
  evaluation?: TaskEvaluation | null;
  onEvaluationUpdate?: (evaluation: TaskEvaluation | null) => void;
}

export function AgentExecutionPanel({
  taskId,
  evaluation,
  onEvaluationUpdate,
}: AgentExecutionPanelProps) {
  const {
    executions,
    currentExecution,
    executionLoading,
    fetchTaskExecutions,
    startAgentWorkflow,
    cancelExecution,
    setCurrentExecution,
    pendingClarification,
    submitClarification,
    skipClarification,
  } = useBoardStore();

  const [selectedExecution, setSelectedExecution] = useState<AgentExecution | null>(null);
  const [startingWorkflow, setStartingWorkflow] = useState(false);
  const [reEvaluating, setReEvaluating] = useState(false);
  
  // Plan selection state
  const [showPlanSelector, setShowPlanSelector] = useState(false);
  const [pendingWorkflowType, setPendingWorkflowType] = useState<WorkflowType | null>(null);
  const [availablePlans, setAvailablePlans] = useState<AvailablePlan[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [loadingPlans, setLoadingPlans] = useState(false);

  // Reset selected execution and fetch new data when taskId changes
  useEffect(() => {
    setSelectedExecution(null);
    if (taskId) {
      fetchTaskExecutions(taskId);
    }
  }, [taskId, fetchTaskExecutions]);

  useEffect(() => {
    // Auto-select current execution if exists
    if (currentExecution && currentExecution.task_id === taskId) {
      setSelectedExecution(currentExecution);
    } else if (executions.length > 0) {
      // Select most recent execution only if none selected
      setSelectedExecution((prev) => {
        if (prev) return prev;
        return executions[0] ?? null;
      });
    }
  }, [currentExecution, executions, taskId]);

  const handleStartWorkflow = async (workflowType: WorkflowType, planExecutionId?: string) => {
    setStartingWorkflow(true);
    try {
      const execution = await startAgentWorkflow(taskId, workflowType, undefined, planExecutionId);
      setSelectedExecution(execution);
      setCurrentExecution(execution);
    } catch (error) {
      console.error('Failed to start workflow:', error);
    } finally {
      setStartingWorkflow(false);
    }
  };

  const handleWorkflowButtonClick = async (workflowType: WorkflowType) => {
    // For development workflows, check if there are available plans
    if (workflowType === 'quick_development' || workflowType === 'development') {
      setLoadingPlans(true);
      try {
        const plans = await api.getTaskPlans(taskId);
        setAvailablePlans(plans);
        setPendingWorkflowType(workflowType);
        setSelectedPlanId(plans.length > 0 ? plans[0]?.execution_id ?? null : null);
        setShowPlanSelector(true);
      } catch (error) {
        console.error('Failed to fetch plans:', error);
        // If no plans available, start without a plan
        handleStartWorkflow(workflowType);
      } finally {
        setLoadingPlans(false);
      }
    } else {
      // For plan-only, start directly
      handleStartWorkflow(workflowType);
    }
  };

  const handleConfirmPlanSelection = () => {
    if (pendingWorkflowType) {
      handleStartWorkflow(pendingWorkflowType, selectedPlanId || undefined);
    }
    setShowPlanSelector(false);
    setPendingWorkflowType(null);
    setSelectedPlanId(null);
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
      case 'awaiting_clarification':
        return <HelpCircle className="h-4 w-4 text-amber-500 animate-pulse" />;
      case 'cancelled':
        return <AlertCircle className="h-4 w-4 text-muted-foreground" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    // Ensure UTC timezone if not specified
    const utcString = dateString.endsWith('Z') || dateString.includes('+') ? dateString : dateString + 'Z';
    const date = new Date(utcString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getWorkflowLabel = (workflowType: string) => {
    const labels: Record<string, string> = {
      development: 'Full Coding',
      quick_development: 'Quick Coding',
      architecture_only: 'Plan Only',
    };
    return labels[workflowType] || workflowType;
  };

  const getPhaseLabel = (phase: string) => {
    const labels: Record<string, string> = {
      architecture: 'Planning',
      development: 'Coding',
      review: 'Review',
    };
    return labels[phase] || phase;
  };

  const runningExecution = executions.find(
    (e) => e.status === 'running' || e.status === 'awaiting_clarification'
  );

  const [clarificationLoading, setClarificationLoading] = useState(false);

  const handleSubmitClarification = async (answers: Record<string, string | string[]>) => {
    if (!pendingClarification) return;
    setClarificationLoading(true);
    try {
      await submitClarification(pendingClarification.execution_id, answers);
      await fetchTaskExecutions(taskId);
    } catch (error) {
      console.error('Failed to submit clarification:', error);
    } finally {
      setClarificationLoading(false);
    }
  };

  const handleSkipClarification = async () => {
    if (!pendingClarification) return;
    setClarificationLoading(true);
    try {
      await skipClarification(pendingClarification.execution_id);
      await fetchTaskExecutions(taskId);
    } catch (error) {
      console.error('Failed to skip clarification:', error);
    } finally {
      setClarificationLoading(false);
    }
  };

  const handleReEvaluate = async () => {
    setReEvaluating(true);
    try {
      const result = await api.triggerTaskEvaluation(taskId);
      onEvaluationUpdate?.(result);
    } catch (error) {
      console.error('Failed to re-evaluate task:', error);
    } finally {
      setReEvaluating(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-4">
          {/* Task Evaluation Section */}
          <div className="bg-muted/50 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <h3 className="font-semibold text-sm">Task Evaluation</h3>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReEvaluate}
                disabled={reEvaluating}
              >
                {reEvaluating ? (
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-1" />
                )}
                Re-evaluate
              </Button>
            </div>

            {evaluation?.repository ? (
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-background rounded-md border">
                  <FolderGit2 className="h-5 w-5 text-primary mt-0.5" />
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{evaluation.repository.name}</span>
                      <Badge variant="outline" className={`text-xs ${getConfidenceColor(evaluation.repository.confidence)}`}>
                        {Math.round(evaluation.repository.confidence * 100)}% confidence
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground font-mono truncate">
                      {evaluation.repository.path}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {evaluation.repository.reasoning}
                    </p>
                  </div>
                </div>

                {/* Context info */}
                {(evaluation.context.technologies.length > 0 || evaluation.context.relevant_files.length > 0) && (
                  <div className="grid grid-cols-2 gap-3">
                    {evaluation.context.technologies.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">Technologies</p>
                        <div className="flex flex-wrap gap-1">
                          {evaluation.context.technologies.map((tech, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">
                              {tech}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {evaluation.context.relevant_files.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">Relevant Files</p>
                        <div className="flex flex-wrap gap-1">
                          {evaluation.context.relevant_files.slice(0, 3).map((file, i) => (
                            <Badge key={i} variant="outline" className="text-xs font-mono">
                              <FileCode2 className="h-3 w-3 mr-1" />
                              {file.split('/').pop()}
                            </Badge>
                          ))}
                          {evaluation.context.relevant_files.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{evaluation.context.relevant_files.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <p className="text-xs text-muted-foreground">
                  Evaluated {new Date(evaluation.evaluated_at.endsWith('Z') || evaluation.evaluated_at.includes('+') ? evaluation.evaluated_at : evaluation.evaluated_at + 'Z').toLocaleString()}
                </p>
              </div>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                <GitBranch className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No repository match found</p>
                <p className="text-xs mt-1">Click Re-evaluate to analyze the task</p>
              </div>
            )}
          </div>

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
                    {getWorkflowLabel(runningExecution.workflow_type)}
                  </Badge>
                  {runningExecution.current_phase && (
                    <Badge variant="default" className="text-xs">
                      {getPhaseLabel(runningExecution.current_phase)}
                    </Badge>
                  )}
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
                  onClick={() => handleWorkflowButtonClick('architecture_only')}
                  disabled={startingWorkflow || executionLoading || loadingPlans}
                  className="flex flex-col items-center gap-1 h-auto py-3"
                >
                  <Box className="h-4 w-4" />
                  <span className="text-xs">Plan Only</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleWorkflowButtonClick('quick_development')}
                  disabled={startingWorkflow || executionLoading || loadingPlans}
                  className="flex flex-col items-center gap-1 h-auto py-3"
                >
                  <Zap className="h-4 w-4" />
                  <span className="text-xs">Quick Coding</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleWorkflowButtonClick('development')}
                  disabled={startingWorkflow || executionLoading || loadingPlans}
                  className="flex flex-col items-center gap-1 h-auto py-3"
                >
                  <Workflow className="h-4 w-4" />
                  <span className="text-xs">Full Coding</span>
                </Button>
              </div>
            )}
          </div>

          {/* Clarification Dialog */}
          {pendingClarification && pendingClarification.task_id === taskId && (
            <ClarificationDialog
              questions={pendingClarification.questions}
              summary={pendingClarification.summary}
              confidence={pendingClarification.confidence}
              onSubmit={handleSubmitClarification}
              onSkip={handleSkipClarification}
              loading={clarificationLoading}
            />
          )}

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
                {/* Execution list with inline details */}
                {executions.slice(0, 5).map((execution) => (
                  <div key={execution.id}>
                    <button
                      onClick={() => setSelectedExecution(
                        selectedExecution?.id === execution.id ? null : execution
                      )}
                      className={`w-full text-left p-3 rounded-md border transition-colors ${
                        selectedExecution?.id === execution.id
                          ? 'border-primary bg-primary/5 rounded-b-none'
                          : 'border-border hover:bg-muted/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(execution.status)}
                          <div>
                            <div className="text-sm font-medium">
                              {getWorkflowLabel(execution.workflow_type)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {formatDateTime(execution.started_at)}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {execution.current_phase && (
                            <Badge variant="secondary" className="text-xs">
                              {getPhaseLabel(execution.current_phase)}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </button>
                    
                    {/* Inline execution details */}
                    {selectedExecution?.id === execution.id && (
                      <div className="border border-t-0 border-primary rounded-b-md bg-primary/5 p-3">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-sm">Execution Details</h4>
                          {execution.status === 'running' && (
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
                        <ExecutionDetails execution={execution} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Plan Selector Dialog */}
          <Dialog open={showPlanSelector} onOpenChange={setShowPlanSelector}>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Select a Plan
                </DialogTitle>
              </DialogHeader>
              
              <div className="py-4">
                {availablePlans.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    <FileText className="h-10 w-10 mx-auto mb-3 opacity-50" />
                    <p className="text-sm font-medium">No plans available</p>
                    <p className="text-xs mt-1">
                      Run "Plan Only" first to create an architecture plan, or proceed without a plan.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {availablePlans.map((plan) => (
                      <button
                        key={plan.execution_id}
                        onClick={() => setSelectedPlanId(plan.execution_id)}
                        className={`w-full text-left p-3 rounded-md border transition-colors ${
                          selectedPlanId === plan.execution_id
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:bg-muted/50'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <FileText className="h-4 w-4 mt-0.5 text-muted-foreground" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium">
                              {plan.plan_filename || 'Architecture Plan'}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                              {new Date(plan.created_at).toLocaleString()}
                            </div>
                            <div className="text-xs text-muted-foreground mt-2 line-clamp-2">
                              {plan.plan_preview}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <DialogFooter className="gap-2 sm:gap-0">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowPlanSelector(false);
                    setPendingWorkflowType(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedPlanId(null);
                    handleConfirmPlanSelection();
                  }}
                >
                  Skip (No Plan)
                </Button>
                <Button
                  onClick={handleConfirmPlanSelection}
                  disabled={availablePlans.length > 0 && !selectedPlanId}
                >
                  Start with Plan
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
    </div>
  );
}
