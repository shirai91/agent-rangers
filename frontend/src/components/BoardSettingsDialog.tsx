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
import { api } from '@/api/client';
import { useBoardStore } from '@/stores/boardStore';
import { FolderSearch, Loader2, GitBranch, FileCode } from 'lucide-react';
import type { Board, Repository } from '@/types';

interface BoardSettingsDialogProps {
  board: Board | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function BoardSettingsDialog({
  board,
  open,
  onOpenChange,
}: BoardSettingsDialogProps) {
  const { setCurrentBoard } = useBoardStore();
  const [workingDirectory, setWorkingDirectory] = useState('');
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (board && open) {
      setWorkingDirectory(board.working_directory || '');
      setRepositories([]);
      setError(null);
      // Load existing repositories if working directory is set
      if (board.working_directory) {
        loadRepositories();
      }
    }
  }, [board, open]);

  const loadRepositories = async () => {
    if (!board) return;
    try {
      const repos = await api.getRepositories(board.id);
      setRepositories(repos);
    } catch (err) {
      // Silently fail if no repos found yet
      setRepositories([]);
    }
  };

  const handleSave = async () => {
    if (!board) return;

    setLoading(true);
    setError(null);

    try {
      const updatedBoard = await api.setWorkingDirectory(board.id, workingDirectory.trim());
      setCurrentBoard(updatedBoard);
      onOpenChange(false);
    } catch (err) {
      setError('Failed to update working directory');
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    if (!board) return;

    setScanning(true);
    setError(null);

    try {
      // First save the working directory if changed
      if (workingDirectory.trim() !== (board.working_directory || '')) {
        const updatedBoard = await api.setWorkingDirectory(board.id, workingDirectory.trim());
        setCurrentBoard(updatedBoard);
      }

      // Then scan for repositories
      const repos = await api.scanRepositories(board.id);
      setRepositories(repos);
    } catch (err) {
      setError('Failed to scan repositories. Make sure the directory exists and is accessible.');
    } finally {
      setScanning(false);
    }
  };

  const getLanguageColor = (language: string | null): string => {
    const colors: Record<string, string> = {
      TypeScript: 'bg-blue-500',
      JavaScript: 'bg-yellow-500',
      Python: 'bg-green-500',
      Go: 'bg-cyan-500',
      Rust: 'bg-orange-500',
      Java: 'bg-red-500',
      'C#': 'bg-purple-500',
      Ruby: 'bg-red-400',
      PHP: 'bg-indigo-500',
    };
    return colors[language || ''] || 'bg-gray-500';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>Board Settings</DialogTitle>
          <DialogDescription>
            Configure the working directory and manage repositories for this board.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <div className="p-2 bg-destructive/10 text-destructive text-sm rounded">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="working-directory">Working Directory</Label>
            <div className="flex gap-2">
              <Input
                id="working-directory"
                value={workingDirectory}
                onChange={(e) => setWorkingDirectory(e.target.value)}
                placeholder="/path/to/your/project"
                className="flex-1"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={handleScan}
                disabled={scanning || !workingDirectory.trim()}
              >
                {scanning ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FolderSearch className="mr-2 h-4 w-4" />
                )}
                Scan
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              The root directory where AI agents will work. This path should be accessible from the server.
            </p>
          </div>

          {repositories.length > 0 && (
            <div className="space-y-2">
              <Label>Repositories ({repositories.length})</Label>
              <div className="border rounded-md max-h-[240px] overflow-y-auto">
                {repositories.map((repo) => (
                  <div
                    key={repo.path}
                    className="p-3 border-b last:border-b-0 hover:bg-muted/50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <GitBranch className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{repo.name}</span>
                      </div>
                      {repo.primary_language && (
                        <span className="flex items-center gap-1 text-xs">
                          <span
                            className={`w-2 h-2 rounded-full ${getLanguageColor(repo.primary_language)}`}
                          />
                          {repo.primary_language}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 font-mono">
                      {repo.path}
                    </p>
                    {repo.remote_url && (
                      <p className="text-xs text-muted-foreground mt-1 truncate">
                        {repo.remote_url}
                      </p>
                    )}
                    {Object.keys(repo.file_counts).length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {Object.entries(repo.file_counts)
                          .sort(([, a], [, b]) => b - a)
                          .slice(0, 5)
                          .map(([ext, count]) => (
                            <span
                              key={ext}
                              className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-muted rounded text-xs"
                            >
                              <FileCode className="h-3 w-3" />
                              {ext}: {count}
                            </span>
                          ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {scanning && (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Scanning for repositories...
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
