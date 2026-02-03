import { useState, useMemo, useRef, useCallback } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import { Column } from './Column';
import { TaskCard } from './TaskCard';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { useBoardStore } from '@/stores/boardStore';
import { calculateNewOrder } from '@/lib/utils';
import type { Task, Column as ColumnType } from '@/types';

interface BoardProps {
  onCreateColumn: () => void;
  onCreateTask: (columnId: string) => void;
  onEditTask: (task: Task) => void;
  onEditColumn: (column: ColumnType) => void;
}

export function Board({ onCreateColumn, onCreateTask, onEditTask, onEditColumn }: BoardProps) {
  const { columns, tasks, optimisticMoveTask, moveTask, isTransitionAllowed } = useBoardStore();
  const [activeTask, setActiveTask] = useState<Task | null>(null);
  // Store original task state for rollback on failed moves
  const originalTaskRef = useRef<Task | null>(null);

  // Check if a column is a valid drop target for the currently dragged task
  const isValidDropTarget = useCallback(
    (targetColumnId: string): boolean => {
      if (!activeTask) return true;
      return isTransitionAllowed(activeTask.column_id, targetColumnId);
    },
    [activeTask, isTransitionAllowed]
  );

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const sortedColumns = useMemo(() => {
    return [...columns].sort((a, b) => a.order - b.order);
  }, [columns]);

  const tasksByColumn = useMemo(() => {
    const grouped: Record<string, Task[]> = {};
    sortedColumns.forEach((column) => {
      grouped[column.id] = tasks
        .filter((task) => task.column_id === column.id)
        .sort((a, b) => a.order - b.order);
    });
    return grouped;
  }, [tasks, sortedColumns]);

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const task = tasks.find((t) => t.id === active.id);
    if (task) {
      setActiveTask(task);
      // Capture original state for potential rollback
      originalTaskRef.current = { ...task };
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const activeTaskItem = tasks.find((t) => t.id === activeId);
    if (!activeTaskItem) return;

    // Check if we're over a column
    const overColumn = columns.find((c) => c.id === overId);
    if (overColumn && activeTaskItem.column_id !== overColumn.id) {
      // Check workflow validation before allowing the move
      if (!isTransitionAllowed(activeTaskItem.column_id, overColumn.id)) {
        return; // Don't allow the optimistic move if workflow forbids it
      }

      // Moving to a different column
      const tasksInTargetColumn = tasksByColumn[overColumn.id] || [];
      const lastTask = tasksInTargetColumn[tasksInTargetColumn.length - 1];
      const newOrder = lastTask?.order !== undefined ? lastTask.order + 1 : 1;

      optimisticMoveTask(activeId, overColumn.id, newOrder);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);
    const originalTask = originalTaskRef.current;
    originalTaskRef.current = null;

    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const activeTaskItem = tasks.find((t) => t.id === activeId);
    if (!activeTaskItem) return;

    // Check if dropped on a task
    const overTask = tasks.find((t) => t.id === overId);
    if (overTask) {
      const targetColumnId = overTask.column_id;
      const tasksInColumn = tasksByColumn[targetColumnId] || [];
      const oldIndex = tasksInColumn.findIndex((t) => t.id === activeId);
      const newIndex = tasksInColumn.findIndex((t) => t.id === overId);

      if (oldIndex !== -1 && newIndex !== -1) {
        // Reordering within the same column or moving to different column
        const reorderedTasks = arrayMove(tasksInColumn, oldIndex, newIndex);
        const taskIndex = reorderedTasks.findIndex((t) => t.id === activeId);

        const prevTask = taskIndex > 0 ? reorderedTasks[taskIndex - 1] : null;
        const nextTask = taskIndex < reorderedTasks.length - 1 ? reorderedTasks[taskIndex + 1] : null;

        const newOrder = calculateNewOrder(
          prevTask?.order ?? null,
          nextTask?.order ?? null
        );

        optimisticMoveTask(activeId, targetColumnId, newOrder);

        try {
          await moveTask(activeId, { column_id: targetColumnId, order: newOrder, version: activeTaskItem.version }, originalTask ?? undefined);
        } catch (error) {
          console.error('Failed to move task:', error);
        }
      }
    } else {
      // Check if dropped on a column
      const overColumn = columns.find((c) => c.id === overId);
      if (overColumn) {
        const tasksInColumn = tasksByColumn[overColumn.id] || [];
        const lastTask = tasksInColumn[tasksInColumn.length - 1];
        const newOrder = lastTask?.order !== undefined ? lastTask.order + 1 : 1;

        optimisticMoveTask(activeId, overColumn.id, newOrder);

        try {
          await moveTask(activeId, { column_id: overColumn.id, order: newOrder, version: activeTaskItem.version }, originalTask ?? undefined);
        } catch (error) {
          console.error('Failed to move task:', error);
        }
      }
    }
  };

  return (
    <div className="flex-1 overflow-x-auto overflow-y-hidden">
      <div className="flex gap-4 p-6 h-full">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          {sortedColumns.map((column) => (
            <Column
              key={column.id}
              column={column}
              tasks={tasksByColumn[column.id] || []}
              onCreateTask={onCreateTask}
              onEditTask={onEditTask}
              onEditColumn={onEditColumn}
              isValidDropTarget={isValidDropTarget(column.id)}
              isDragging={activeTask !== null}
            />
          ))}

          <DragOverlay>
            {activeTask ? (
              <div className="rotate-3">
                <TaskCard task={activeTask} onEdit={() => {}} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>

        <div className="flex-shrink-0 w-80">
          <Button
            variant="outline"
            className="w-full h-full min-h-[100px] border-dashed"
            onClick={onCreateColumn}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Column
          </Button>
        </div>
      </div>
    </div>
  );
}
