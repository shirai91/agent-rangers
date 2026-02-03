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

interface ColumnSettingsDialogProps {
  column: Column | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ColumnSettingsDialog({
  column,
  open,
  onOpenChange,
}: ColumnSettingsDialogProps) {
  const { updateColumnSettings } = useBoardStore();
  const [name, setName] = useState('');
  const [color, setColor] = useState('');
  const [wipLimit, setWipLimit] = useState<string>('');
  const [triggersAgents, setTriggersAgents] = useState(false);
  const [isStartColumn, setIsStartColumn] = useState(false);
  const [isEndColumn, setIsEndColumn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (column) {
      setName(column.name);
      setColor(column.color || '');
      setWipLimit(column.wip_limit?.toString() || '');
      setTriggersAgents(column.triggers_agents);
      setIsStartColumn(column.is_start_column);
      setIsEndColumn(column.is_end_column);
    }
  }, [column]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!column) return;

    setLoading(true);
    setError(null);

    try {
      await updateColumnSettings(column.id, {
        name: name.trim(),
        color: color || undefined,
        wip_limit: wipLimit ? parseInt(wipLimit, 10) : null,
        triggers_agents: triggersAgents,
        is_start_column: isStartColumn,
        is_end_column: isEndColumn,
      });
      onOpenChange(false);
    } catch (err) {
      setError('Failed to update column settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Column Settings</DialogTitle>
          <DialogDescription>
            Configure column properties and workflow settings.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            {error && (
              <div className="p-2 bg-destructive/10 text-destructive text-sm rounded">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="column-name">Name</Label>
              <Input
                id="column-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Column name"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="column-color">Color</Label>
              <div className="flex gap-2">
                <Input
                  id="column-color"
                  type="color"
                  value={color || '#6366f1'}
                  onChange={(e) => setColor(e.target.value)}
                  className="w-14 h-10 p-1"
                />
                <Input
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  placeholder="#6366f1"
                  pattern="^#[0-9A-Fa-f]{6}$"
                  className="flex-1"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="wip-limit">WIP Limit</Label>
              <Input
                id="wip-limit"
                type="number"
                min="0"
                value={wipLimit}
                onChange={(e) => setWipLimit(e.target.value)}
                placeholder="No limit"
              />
              <p className="text-xs text-muted-foreground">
                Maximum tasks allowed in this column (0 or empty = unlimited)
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <Label className="text-sm font-medium">Workflow Settings</Label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isStartColumn}
                  onChange={(e) => setIsStartColumn(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300"
                />
                <div>
                  <span className="text-sm">Start Column</span>
                  <p className="text-xs text-muted-foreground">
                    New tasks are created in this column
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isEndColumn}
                  onChange={(e) => setIsEndColumn(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300"
                />
                <div>
                  <span className="text-sm">End Column</span>
                  <p className="text-xs text-muted-foreground">
                    Tasks are considered complete in this column
                  </p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={triggersAgents}
                  onChange={(e) => setTriggersAgents(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300"
                />
                <div>
                  <span className="text-sm">Triggers AI Agents</span>
                  <p className="text-xs text-muted-foreground">
                    Moving a task here starts AI agent processing
                  </p>
                </div>
              </label>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !name.trim()}>
              {loading ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
