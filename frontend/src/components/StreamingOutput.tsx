import { Loader2 } from 'lucide-react';
import { useBoardStore } from '@/stores/boardStore';

interface StreamingOutputProps {
  executionId: string;
}

export function StreamingOutput({ executionId }: StreamingOutputProps) {
  // Get just the current milestone string from the store
  const milestone = useBoardStore((state) => state.executionMilestones[executionId]);

  if (!milestone) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground py-4">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm">Starting...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 py-4">
      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      <span className="text-sm font-medium">{milestone}</span>
    </div>
  );
}

// Compact version is now identical to main version
export function StreamingOutputCompact({ executionId }: { executionId: string }) {
  return <StreamingOutput executionId={executionId} />;
}
