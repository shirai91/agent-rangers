import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ArrowRight,
  Plus,
  Pencil,
  Trash2,
  Clock,
  User,
} from 'lucide-react';
import { useBoardStore } from '@/stores/boardStore';
import type { TaskActivity } from '@/types';

interface ActivityFeedProps {
  boardId: string;
}

export function ActivityFeed({ boardId }: ActivityFeedProps) {
  const { activities, activitiesLoading, fetchBoardActivities } = useBoardStore();

  useEffect(() => {
    fetchBoardActivities(boardId);
  }, [boardId, fetchBoardActivities]);

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Activity Feed
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[400px] overflow-y-auto">
          <div className="px-4 pb-4 space-y-3">
            {activitiesLoading ? (
              <div className="text-sm text-muted-foreground text-center py-4">
                Loading activities...
              </div>
            ) : activities.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-4">
                No activity yet
              </div>
            ) : (
              activities.map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ActivityItemProps {
  activity: TaskActivity;
}

function ActivityItem({ activity }: ActivityItemProps) {
  const getActivityIcon = () => {
    switch (activity.activity_type) {
      case 'created':
        return <Plus className="h-3 w-3 text-green-600" />;
      case 'updated':
        return <Pencil className="h-3 w-3 text-blue-600" />;
      case 'moved':
        return <ArrowRight className="h-3 w-3 text-purple-600" />;
      case 'deleted':
        return <Trash2 className="h-3 w-3 text-red-600" />;
      default:
        return <Clock className="h-3 w-3 text-gray-600" />;
    }
  };

  const getActivityDescription = () => {
    switch (activity.activity_type) {
      case 'created':
        return (
          <span>
            Created task{' '}
            <span className="font-medium">
              {activity.task_title || 'Unknown'}
            </span>
          </span>
        );
      case 'updated':
        const fields = activity.new_value
          ? Object.keys(activity.new_value).join(', ')
          : 'fields';
        return (
          <span>
            Updated {fields} on{' '}
            <span className="font-medium">
              {activity.task_title || 'Unknown'}
            </span>
          </span>
        );
      case 'moved':
        return (
          <span>
            Moved{' '}
            <span className="font-medium">
              {activity.task_title || 'Unknown'}
            </span>{' '}
            from{' '}
            <Badge variant="outline" className="text-xs">
              {activity.from_column_name || 'Unknown'}
            </Badge>{' '}
            to{' '}
            <Badge variant="outline" className="text-xs">
              {activity.to_column_name || 'Unknown'}
            </Badge>
          </span>
        );
      case 'deleted':
        return (
          <span>
            Deleted task{' '}
            <span className="font-medium">
              {String(activity.old_value?.title || 'Unknown')}
            </span>
          </span>
        );
      default:
        return <span>{activity.activity_type}</span>;
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString();
  };

  return (
    <div className="flex items-start gap-3 text-sm">
      <div className="mt-1 p-1.5 rounded-full bg-muted">
        {getActivityIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-foreground">{getActivityDescription()}</div>
        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
          <User className="h-3 w-3" />
          <span>{activity.actor}</span>
          <span>·</span>
          <span>{formatTime(activity.created_at)}</span>
        </div>
      </div>
    </div>
  );
}

export { ActivityItem };
