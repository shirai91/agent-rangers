import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useBoardStore } from '@/stores/boardStore';
import type { Task } from '@/types';

interface CreateTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  boardId: string;
  columnId: string | null;
  editTask?: Task | null;
}

export function CreateTaskDialog({ open, onOpenChange, boardId, columnId, editTask }: CreateTaskDialogProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assignedTo, setAssignedTo] = useState('');
  const [priority, setPriority] = useState('');
  const [loading, setLoading] = useState(false);
  const { createTask, updateTask } = useBoardStore();

  useEffect(() => {
    if (editTask) {
      setTitle(editTask.title);
      setDescription(editTask.description || '');
      setAssignedTo(editTask.assigned_to || '');
      setPriority(editTask.priority || '');
    } else {
      setTitle('');
      setDescription('');
      setAssignedTo('');
      setPriority('');
    }
  }, [editTask, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    try {
      if (editTask) {
        await updateTask(editTask.id, {
          title: title.trim(),
          description: description.trim() || undefined,
          assigned_to: assignedTo.trim() || undefined,
          priority: priority || undefined,
        });
      } else if (columnId) {
        await createTask(boardId, {
          column_id: columnId,
          title: title.trim(),
          description: description.trim() || undefined,
          assigned_to: assignedTo.trim() || undefined,
          priority: priority || undefined,
        });
      }
      setTitle('');
      setDescription('');
      setAssignedTo('');
      setPriority('');
      onOpenChange(false);
    } catch (error) {
      console.error(`Failed to ${editTask ? 'update' : 'create'} task:`, error);
      alert(`Failed to ${editTask ? 'update' : 'create'} task. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editTask ? 'Edit Task' : 'Create New Task'}</DialogTitle>
          <DialogDescription>
            {editTask ? 'Update the task details.' : 'Add a new task to the column.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                placeholder="Enter task title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                placeholder="Enter task description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="assignedTo">Assigned To</Label>
              <Input
                id="assignedTo"
                placeholder="Enter assignee name (optional)"
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <select
                id="priority"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">Select priority (optional)</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !title.trim()}>
              {loading ? (editTask ? 'Updating...' : 'Creating...') : (editTask ? 'Update Task' : 'Create Task')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
