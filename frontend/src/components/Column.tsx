import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Plus, MoreVertical, Trash2, Edit, Settings } from 'lucide-react';
import { TaskCard } from './TaskCard';
import type { Column as ColumnType, Task } from '@/types';
import { useBoardStore } from '@/stores/boardStore';
import { Badge } from '@/components/ui/badge';

interface ColumnProps {
  column: ColumnType;
  tasks: Task[];
  onCreateTask: (columnId: string) => void;
  onEditTask: (task: Task) => void;
  onEditColumn: (column: ColumnType) => void;
  onColumnSettings: (column: ColumnType) => void;
  isValidDropTarget?: boolean;
  isDragging?: boolean;
}

export function Column({
  column,
  tasks,
  onCreateTask,
  onEditTask,
  onEditColumn,
  onColumnSettings,
  isValidDropTarget = true,
  isDragging = false,
}: ColumnProps) {
  const { deleteColumn } = useBoardStore();
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
  });

  // Determine visual state based on drag state and validity
  const getDropZoneClass = () => {
    if (!isDragging) return '';
    if (isOver && isValidDropTarget) return 'ring-2 ring-primary bg-primary/5';
    if (isOver && !isValidDropTarget) return 'ring-2 ring-destructive bg-destructive/5';
    if (!isValidDropTarget) return 'opacity-50';
    return 'ring-1 ring-dashed ring-muted-foreground/30';
  };

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete column "${column.name}"? All tasks in this column will be deleted.`)) {
      try {
        await deleteColumn(column.id);
      } catch (error) {
        console.error('Failed to delete column:', error);
      }
    }
  };

  const taskIds = tasks.map((task) => task.id);

  return (
    <div className="flex-shrink-0 w-80 h-full">
      <Card className={`flex flex-col h-full transition-all duration-200 ${getDropZoneClass()}`}>
        <CardHeader className="p-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold">
                {column.name}
              </CardTitle>
              <Badge variant="secondary" className="text-xs">
                {tasks.length}
              </Badge>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onCreateTask(column.id)}
                className="h-8 w-8"
              >
                <Plus className="h-4 w-4" />
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onEditColumn(column)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit Name
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onColumnSettings(column)}>
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
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
        <CardContent className="p-4 pt-0 flex-1 min-h-0 overflow-y-auto">
          <div
            ref={setNodeRef}
            className={`space-y-3 ${tasks.length === 0 ? 'min-h-[200px] h-full' : ''}`}
          >
            <SortableContext
              items={taskIds}
              strategy={verticalListSortingStrategy}
            >
              {tasks.map((task) => (
                <TaskCard key={task.id} task={task} onEdit={onEditTask} />
              ))}
            </SortableContext>
            {tasks.length === 0 ? (
              <div className="flex items-center justify-center h-full text-sm text-muted-foreground border-2 border-dashed rounded-lg">
                Drop tasks here or click + to add
              </div>
            ) : (
              /* Drop zone at bottom - always visible when there are tasks */
              <div className={`h-16 mt-2 rounded-lg border-2 border-dashed transition-colors ${
                isOver && isValidDropTarget 
                  ? 'border-primary bg-primary/10' 
                  : 'border-transparent hover:border-muted-foreground/30'
              }`} />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
