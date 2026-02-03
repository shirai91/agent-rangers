import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  PlayCircle,
  AlertCircle,
  Workflow,
  BarChart3,
} from 'lucide-react';
import type { AgentExecution } from '@/types';
import { AgentOutputViewer } from './AgentOutputViewer';

interface ExecutionDetailsProps {
  execution: AgentExecution;
}

export function ExecutionDetails({ execution }: ExecutionDetailsProps) {
  const [showOutputs, setShowOutputs] = useState(true);
  const [showContext, setShowContext] = useState(false);
  const [showResultSummary, setShowResultSummary] = useState(false);

  const getStatusBadge = () => {
    switch (execution.status) {
      case 'completed':
        return (
          <Badge variant="default" className="bg-green-600 text-white">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Completed
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Failed
          </Badge>
        );
      case 'running':
        return (
          <Badge variant="secondary" className="animate-pulse">
            <PlayCircle className="h-3 w-3 mr-1" />
            Running
          </Badge>
        );
      case 'cancelled':
        return (
          <Badge variant="outline">
            <AlertCircle className="h-3 w-3 mr-1" />
            Cancelled
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {execution.status}
          </Badge>
        );
    }
  };

  const getWorkflowTypeBadge = () => {
    const typeMap: Record<string, { label: string; className: string }> = {
      development: { label: 'Full Development', className: 'bg-blue-600 text-white' },
      quick_development: { label: 'Quick Dev', className: 'bg-purple-600 text-white' },
      architecture_only: { label: 'Architecture', className: 'bg-orange-600 text-white' },
    };

    const config = typeMap[execution.workflow_type] || {
      label: execution.workflow_type,
      className: ''
    };

    return (
      <Badge variant="default" className={config.className}>
        <Workflow className="h-3 w-3 mr-1" />
        {config.label}
      </Badge>
    );
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

  const calculateDuration = () => {
    if (!execution.started_at) return 'N/A';
    const start = new Date(execution.started_at);
    const end = execution.completed_at ? new Date(execution.completed_at) : new Date();
    const durationMs = end.getTime() - start.getTime();

    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const getPhaseProgress = () => {
    const phases = ['architecture', 'development', 'review'];
    const currentPhaseIndex = execution.current_phase
      ? phases.indexOf(execution.current_phase)
      : -1;

    return {
      current: currentPhaseIndex + 1,
      total: phases.length,
      percentage: execution.status === 'completed'
        ? 100
        : currentPhaseIndex >= 0
          ? Math.round(((currentPhaseIndex + 1) / phases.length) * 100)
          : 0,
    };
  };

  const progress = getPhaseProgress();

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base font-semibold flex items-center gap-2 flex-wrap">
              {getWorkflowTypeBadge()}
              {getStatusBadge()}
            </CardTitle>
            <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>Started: {formatDateTime(execution.started_at)}</span>
              </div>
              {execution.completed_at && (
                <div className="flex items-center gap-1">
                  <span>Duration: {calculateDuration()}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                <BarChart3 className="h-3 w-3" />
                <span>Iteration {execution.iteration}/{execution.max_iterations}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        {execution.status === 'running' && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
              <span>Progress</span>
              <span>{progress.percentage}%</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary rounded-full h-2 transition-all duration-300"
                style={{ width: `${progress.percentage}%` }}
              />
            </div>
            {execution.current_phase && (
              <div className="text-xs text-muted-foreground mt-1">
                Current phase: {execution.current_phase}
              </div>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Error message */}
        {execution.error_message && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <div className="flex items-start gap-2">
              <XCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-sm font-medium text-destructive mb-1">
                  Execution Failed
                </div>
                <div className="text-sm text-destructive/90">
                  {execution.error_message}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Result summary - collapsible */}
        {execution.result_summary && Object.keys(execution.result_summary).length > 0 && (
          <div className="border rounded-md">
            <button
              onClick={() => setShowResultSummary(!showResultSummary)}
              className="w-full px-3 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2 text-sm font-medium">
                {showResultSummary ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                <CheckCircle2 className="h-4 w-4" />
                Result Summary
              </div>
            </button>
            {showResultSummary && (
              <div className="px-3 pb-3 pt-1">
                <pre className="p-3 bg-muted rounded-md overflow-x-auto">
                  <code className="text-xs font-mono">
                    {JSON.stringify(execution.result_summary, null, 2)}
                  </code>
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Context - collapsible */}
        {execution.context && Object.keys(execution.context).length > 0 && (
          <div className="border rounded-md">
            <button
              onClick={() => setShowContext(!showContext)}
              className="w-full px-3 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2 text-sm font-medium">
                {showContext ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                Execution Context
              </div>
              <Badge variant="secondary" className="text-xs">
                {Object.keys(execution.context).length} fields
              </Badge>
            </button>
            {showContext && (
              <div className="px-3 pb-3 pt-1">
                <pre className="p-3 bg-muted rounded-md overflow-x-auto">
                  <code className="text-xs font-mono">
                    {JSON.stringify(execution.context, null, 2)}
                  </code>
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Agent outputs - collapsible */}
        {execution.outputs && execution.outputs.length > 0 && (
          <div className="border rounded-md">
            <button
              onClick={() => setShowOutputs(!showOutputs)}
              className="w-full px-3 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2 text-sm font-medium">
                {showOutputs ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                Agent Outputs
              </div>
              <Badge variant="secondary" className="text-xs">
                {execution.outputs.length} outputs
              </Badge>
            </button>
            {showOutputs && (
              <div className="px-3 pb-3 pt-1 space-y-2 max-h-[600px] overflow-y-auto">
                {execution.outputs.map((output) => (
                  <AgentOutputViewer key={output.id} output={output} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {(!execution.outputs || execution.outputs.length === 0) && execution.status === 'running' && (
          <div className="text-center py-6 text-muted-foreground">
            <PlayCircle className="h-8 w-8 mx-auto mb-2 animate-pulse" />
            <div className="text-sm">Execution in progress...</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
