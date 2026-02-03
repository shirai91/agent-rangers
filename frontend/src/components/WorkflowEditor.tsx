import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  ArrowRight,
  Plus,
  Trash2,
  Workflow,
  Check,
  X,
} from 'lucide-react';
import { api } from '@/api/client';
import { useBoardStore } from '@/stores/boardStore';
import type { WorkflowDefinition, WorkflowTransition } from '@/types';

interface WorkflowEditorProps {
  boardId: string;
}

export function WorkflowEditor({ boardId }: WorkflowEditorProps) {
  const { columns, fetchAllowedTransitions } = useBoardStore();
  const [workflow, setWorkflow] = useState<WorkflowDefinition | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showAddTransitionDialog, setShowAddTransitionDialog] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('Default Workflow');
  const [selectedFromColumn, setSelectedFromColumn] = useState<string>('');
  const [selectedToColumn, setSelectedToColumn] = useState<string>('');

  const sortedColumns = [...columns].sort((a, b) => a.order - b.order);

  const loadWorkflow = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const workflows = await api.getWorkflows(boardId);
      const active = workflows.find((w) => w.is_active) || workflows[0] || null;
      setWorkflow(active);
    } catch (err) {
      setError('Failed to load workflow');
    } finally {
      setLoading(false);
    }
  }, [boardId]);

  useEffect(() => {
    loadWorkflow();
  }, [loadWorkflow]);

  const handleCreateWorkflow = async () => {
    try {
      const newWorkflow = await api.createWorkflow(boardId, {
        name: newWorkflowName,
        is_active: true,
      });
      setWorkflow(newWorkflow);
      setShowCreateDialog(false);
      setNewWorkflowName('Default Workflow');
      await fetchAllowedTransitions(boardId);
    } catch (err) {
      setError('Failed to create workflow');
    }
  };

  const handleAddTransition = async () => {
    if (!workflow || !selectedFromColumn || !selectedToColumn) return;

    try {
      await api.createTransition(workflow.id, {
        from_column_id: selectedFromColumn,
        to_column_id: selectedToColumn,
      });
      await loadWorkflow();
      await fetchAllowedTransitions(boardId);
      setShowAddTransitionDialog(false);
      setSelectedFromColumn('');
      setSelectedToColumn('');
    } catch (err) {
      setError('Failed to add transition');
    }
  };

  const handleDeleteTransition = async (transitionId: string) => {
    try {
      await api.deleteTransition(transitionId);
      await loadWorkflow();
      await fetchAllowedTransitions(boardId);
    } catch (err) {
      setError('Failed to delete transition');
    }
  };

  const handleToggleWorkflow = async () => {
    if (!workflow) return;

    try {
      await api.updateWorkflow(workflow.id, { is_active: !workflow.is_active });
      await loadWorkflow();
      await fetchAllowedTransitions(boardId);
    } catch (err) {
      setError('Failed to update workflow');
    }
  };

  const getColumnName = (columnId: string) => {
    return columns.find((c) => c.id === columnId)?.name || 'Unknown';
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Loading workflow...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Workflow className="h-4 w-4" />
            Workflow Rules
          </CardTitle>
          {workflow && (
            <Button
              variant={workflow.is_active ? 'default' : 'outline'}
              size="sm"
              onClick={handleToggleWorkflow}
            >
              {workflow.is_active ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Active
                </>
              ) : (
                <>
                  <X className="h-3 w-3 mr-1" />
                  Inactive
                </>
              )}
            </Button>
          )}
        </div>
        {workflow && (
          <p className="text-sm text-muted-foreground">{workflow.name}</p>
        )}
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-2 bg-destructive/10 text-destructive text-sm rounded">
            {error}
          </div>
        )}

        {!workflow ? (
          <div className="text-center py-4">
            <p className="text-sm text-muted-foreground mb-4">
              No workflow defined. Create one to control task transitions.
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Workflow
            </Button>
          </div>
        ) : (
          <>
            {/* Transition List */}
            <div className="space-y-2 mb-4">
              {(workflow.transitions || []).length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No transitions defined. All moves are allowed.
                </p>
              ) : (
                (workflow.transitions || []).map((transition) => (
                  <TransitionRow
                    key={transition.id}
                    transition={transition}
                    getColumnName={getColumnName}
                    onDelete={() => handleDeleteTransition(transition.id)}
                  />
                ))
              )}
            </div>

            {/* Add Transition Button */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setShowAddTransitionDialog(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Transition
            </Button>
          </>
        )}
      </CardContent>

      {/* Create Workflow Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Workflow</DialogTitle>
            <DialogDescription>
              Create a new workflow to define allowed task transitions.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="workflow-name">Workflow Name</Label>
              <Input
                id="workflow-name"
                value={newWorkflowName}
                onChange={(e) => setNewWorkflowName(e.target.value)}
                placeholder="Enter workflow name"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateWorkflow}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Transition Dialog */}
      <Dialog
        open={showAddTransitionDialog}
        onOpenChange={setShowAddTransitionDialog}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Transition</DialogTitle>
            <DialogDescription>
              Define an allowed transition between columns.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>From Column</Label>
              <select
                className="w-full p-2 border rounded-md"
                value={selectedFromColumn}
                onChange={(e) => setSelectedFromColumn(e.target.value)}
              >
                <option value="">Select column...</option>
                {sortedColumns.map((col) => (
                  <option key={col.id} value={col.id}>
                    {col.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-center">
              <ArrowRight className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <Label>To Column</Label>
              <select
                className="w-full p-2 border rounded-md"
                value={selectedToColumn}
                onChange={(e) => setSelectedToColumn(e.target.value)}
              >
                <option value="">Select column...</option>
                {sortedColumns.map((col) => (
                  <option key={col.id} value={col.id}>
                    {col.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAddTransitionDialog(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddTransition}
              disabled={!selectedFromColumn || !selectedToColumn}
            >
              Add Transition
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

interface TransitionRowProps {
  transition: WorkflowTransition;
  getColumnName: (id: string) => string;
  onDelete: () => void;
}

function TransitionRow({
  transition,
  getColumnName,
  onDelete,
}: TransitionRowProps) {
  return (
    <div className="flex items-center justify-between p-2 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-2 text-sm">
        <Badge variant="outline">{getColumnName(transition.from_column_id)}</Badge>
        <ArrowRight className="h-4 w-4 text-muted-foreground" />
        <Badge variant="outline">{getColumnName(transition.to_column_id)}</Badge>
      </div>
      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onDelete}>
        <Trash2 className="h-4 w-4 text-destructive" />
      </Button>
    </div>
  );
}

export { TransitionRow };
