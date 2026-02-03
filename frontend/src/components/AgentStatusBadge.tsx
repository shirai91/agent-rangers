import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { Loader2, CheckCircle2, XCircle, Clock, Ban } from 'lucide-react';
import type { AgentStatus } from '@/types';

interface AgentStatusBadgeProps {
  status: AgentStatus | null | undefined;
  className?: string;
}

export function AgentStatusBadge({ status, className }: AgentStatusBadgeProps) {
  if (!status) {
    return null;
  }

  const getStatusConfig = (status: AgentStatus) => {
    switch (status) {
      case 'pending':
        return {
          icon: Clock,
          label: 'Pending',
          className: 'bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-100',
        };
      case 'running':
        return {
          icon: Loader2,
          label: 'Running',
          className: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-100',
          animate: true,
        };
      case 'completed':
        return {
          icon: CheckCircle2,
          label: 'Completed',
          className: 'bg-green-100 text-green-800 border-green-200 hover:bg-green-100',
        };
      case 'failed':
        return {
          icon: XCircle,
          label: 'Failed',
          className: 'bg-red-100 text-red-800 border-red-200 hover:bg-red-100',
        };
      case 'cancelled':
        return {
          icon: Ban,
          label: 'Cancelled',
          className: 'bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-100',
        };
      default:
        return {
          icon: Clock,
          label: status,
          className: 'bg-gray-100 text-gray-800 border-gray-200',
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        'flex items-center gap-1 font-medium',
        config.className,
        className
      )}
    >
      <Icon
        className={cn('h-3 w-3', config.animate && 'animate-spin')}
      />
      {config.label}
    </Badge>
  );
}
