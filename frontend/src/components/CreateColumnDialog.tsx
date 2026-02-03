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
import type { Column } from '@/types';

interface CreateColumnDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  boardId: string;
  editColumn?: Column | null;
}

export function CreateColumnDialog({ open, onOpenChange, boardId, editColumn }: CreateColumnDialogProps) {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const { createColumn, updateColumn } = useBoardStore();

  useEffect(() => {
    if (editColumn) {
      setName(editColumn.name);
    } else {
      setName('');
    }
  }, [editColumn, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      if (editColumn) {
        await updateColumn(editColumn.id, { name: name.trim() });
      } else {
        await createColumn(boardId, {
          name: name.trim(),
        });
      }
      setName('');
      onOpenChange(false);
    } catch (error) {
      console.error(`Failed to ${editColumn ? 'update' : 'create'} column:`, error);
      alert(`Failed to ${editColumn ? 'update' : 'create'} column. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editColumn ? 'Edit Column' : 'Create New Column'}</DialogTitle>
          <DialogDescription>
            {editColumn ? 'Update the column name.' : 'Add a new column to your board.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="Enter column name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoFocus
              />
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
            <Button type="submit" disabled={loading || !name.trim()}>
              {loading ? (editColumn ? 'Updating...' : 'Creating...') : (editColumn ? 'Update Column' : 'Create Column')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
