import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Loader2,
  CheckCircle2,
  Circle,
  ArrowRight,
  Bot,
} from 'lucide-react';
import type { AgentExecution, AgentPhase } from '@/types';
import { AgentStatusBadge } from './AgentStatusBadge';

interface AgentStatusIndicatorProps {
  execution: AgentExecution | null;
  className?: string;
}

export function AgentStatusIndicator({
  execution,
  className,
}: AgentStatusIndicatorProps) {
  if (!execution) {
    return (
      <Card className={cn('border-dashed', className)}>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Bot className="h-12 w-12 text-muted-foreground/50 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">
              No active execution
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Agent workflow has not been started
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const phases: AgentPhase[] = ['architecture', 'development', 'review'];
  const currentPhaseIndex = execution.current_phase
    ? phases.indexOf(execution.current_phase as AgentPhase)
    : -1;

  const getPhaseStatus = (_phase: AgentPhase, index: number) => {
    if (index < currentPhaseIndex) return 'completed';
    if (index === currentPhaseIndex && execution.status === 'running')
      return 'active';
    if (index === currentPhaseIndex) return 'current';
    return 'pending';
  };

  const getPhaseLabel = (phase: AgentPhase) => {
    switch (phase) {
      case 'architecture':
        return 'Architecture';
      case 'development':
        return 'Development';
      case 'review':
        return 'Review';
      default:
        return phase;
    }
  };

  const getCurrentAgent = () => {
    if (!execution.outputs || execution.outputs.length === 0) return null;
    const latestOutput = execution.outputs[execution.outputs.length - 1];
    return latestOutput?.agent_name ?? null;
  };

  const currentAgent = getCurrentAgent();

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Agent Status</CardTitle>
          <AgentStatusBadge status={execution.status as any} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Phase Progress */}
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Phase</p>
          <div className="flex items-center gap-2">
            {phases.map((phase, index) => {
              const status = getPhaseStatus(phase, index);
              return (
                <div key={phase} className="flex items-center gap-2 flex-1">
                  <div className="flex items-center gap-1.5 flex-1">
                    {status === 'completed' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                    ) : status === 'active' ? (
                      <Loader2 className="h-4 w-4 text-blue-600 animate-spin flex-shrink-0" />
                    ) : status === 'current' ? (
                      <Circle className="h-4 w-4 text-blue-600 fill-blue-600 flex-shrink-0" />
                    ) : (
                      <Circle className="h-4 w-4 text-muted-foreground/30 flex-shrink-0" />
                    )}
                    <span
                      className={cn(
                        'text-xs font-medium',
                        status === 'completed' && 'text-green-600',
                        status === 'active' && 'text-blue-600',
                        status === 'current' && 'text-blue-600',
                        status === 'pending' && 'text-muted-foreground/50'
                      )}
                    >
                      {getPhaseLabel(phase)}
                    </span>
                  </div>
                  {index < phases.length - 1 && (
                    <ArrowRight
                      className={cn(
                        'h-3 w-3 flex-shrink-0',
                        index < currentPhaseIndex
                          ? 'text-green-600'
                          : 'text-muted-foreground/30'
                      )}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Iteration Count */}
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-muted-foreground">Progress</p>
          <Badge variant="outline" className="text-xs">
            Iteration {execution.iteration}/{execution.max_iterations}
          </Badge>
        </div>

        {/* Current Agent */}
        {execution.status === 'running' && currentAgent && (
          <div className="flex items-center justify-between pt-2 border-t">
            <p className="text-xs font-medium text-muted-foreground">
              Active Agent
            </p>
            <div className="flex items-center gap-1.5">
              <Bot className="h-3.5 w-3.5 text-blue-600" />
              <span className="text-xs font-medium text-blue-600">
                {currentAgent}
              </span>
            </div>
          </div>
        )}

        {/* Error Message */}
        {execution.error_message && (
          <div className="pt-2 border-t">
            <p className="text-xs font-medium text-red-600 mb-1">Error</p>
            <p className="text-xs text-muted-foreground line-clamp-2">
              {execution.error_message}
            </p>
          </div>
        )}

        {/* Workflow Type */}
        <div className="flex items-center justify-between pt-2 border-t">
          <p className="text-xs font-medium text-muted-foreground">Workflow</p>
          <Badge variant="secondary" className="text-xs">
            {execution.workflow_type.replace(/_/g, ' ')}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
