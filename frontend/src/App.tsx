import { useEffect, useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useBoardStore } from '@/stores/boardStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Board } from '@/components/Board';
import { CreateBoardDialog } from '@/components/CreateBoardDialog';
import { CreateColumnDialog } from '@/components/CreateColumnDialog';
import { CreateTaskDialog } from '@/components/CreateTaskDialog';
import { WorkflowEditor } from '@/components/WorkflowEditor';
import { ActivityFeed } from '@/components/ActivityFeed';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ArrowLeft, Plus, MoreVertical, Trash2, LayoutDashboard, Settings, Activity } from 'lucide-react';
import type { Task, Column } from '@/types';

function BoardsListView() {
  const navigate = useNavigate();
  const [createBoardOpen, setCreateBoardOpen] = useState(false);

  const {
    boards,
    loading,
    fetchBoards,
    deleteBoard,
  } = useBoardStore();

  useEffect(() => {
    fetchBoards();
  }, [fetchBoards]);

  const handleSelectBoard = (boardId: string) => {
    navigate(`/boards/${boardId}`);
  };

  const handleDeleteBoard = async (boardId: string) => {
    if (window.confirm('Are you sure you want to delete this board? All columns and tasks will be deleted.')) {
      try {
        await deleteBoard(boardId);
      } catch (error) {
        console.error('Failed to delete board:', error);
        alert('Failed to delete board. Please try again.');
      }
    }
  };

  return (
    <>
      <header className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <LayoutDashboard className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Agent Rangers</h1>
                <p className="text-sm text-muted-foreground">
                  AI Multi-Agent Kanban Framework
                </p>
              </div>
            </div>
            <Button onClick={() => setCreateBoardOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Board
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto">
        <div className="p-6">
          <div className="mb-6">
            <h2 className="text-3xl font-bold">Your Boards</h2>
            <p className="text-muted-foreground mt-2">
              Select a board to manage tasks
            </p>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-full" />
                  </CardHeader>
                </Card>
              ))}
            </div>
          ) : boards.length === 0 ? (
            <Card className="text-center py-12">
              <CardContent>
                <LayoutDashboard className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No boards yet</h3>
                <p className="text-muted-foreground mb-4">
                  Create your first board to get started
                </p>
                <Button onClick={() => setCreateBoardOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Board
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {boards.map((board) => (
                <Card
                  key={board.id}
                  className="hover:shadow-lg transition-shadow cursor-pointer"
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div
                        className="flex-1 min-w-0"
                        onClick={() => handleSelectBoard(board.id)}
                      >
                        <CardTitle className="break-words">{board.name}</CardTitle>
                        {board.description && (
                          <CardDescription className="mt-2">
                            {board.description}
                          </CardDescription>
                        )}
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleDeleteBoard(board.id)}>
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      <CreateBoardDialog
        open={createBoardOpen}
        onOpenChange={setCreateBoardOpen}
        onSuccess={() => fetchBoards()}
      />
    </>
  );
}

function BoardView() {
  const { boardId } = useParams<{ boardId: string }>();
  const navigate = useNavigate();
  const [createColumnOpen, setCreateColumnOpen] = useState(false);
  const [createTaskOpen, setCreateTaskOpen] = useState(false);
  const [selectedColumnId, setSelectedColumnId] = useState<string | null>(null);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [editingColumn, setEditingColumn] = useState<Column | null>(null);
  const [workflowEditorOpen, setWorkflowEditorOpen] = useState(false);
  const [activityFeedOpen, setActivityFeedOpen] = useState(false);

  const {
    currentBoard,
    loading,
    error,
    fetchBoard,
  } = useBoardStore();

  // Connect to WebSocket when viewing a board
  useWebSocket(boardId || null);

  useEffect(() => {
    if (boardId) {
      fetchBoard(boardId).catch((err) => {
        console.error('Failed to load board:', err);
      });
    }
  }, [boardId, fetchBoard]);

  const handleBackToBoards = () => {
    navigate('/');
  };

  const handleCreateColumn = () => {
    setEditingColumn(null);
    setCreateColumnOpen(true);
  };

  const handleEditColumn = (column: Column) => {
    setEditingColumn(column);
    setCreateColumnOpen(true);
  };

  const handleCreateTask = (columnId: string) => {
    setSelectedColumnId(columnId);
    setEditingTask(null);
    setCreateTaskOpen(true);
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
    setSelectedColumnId(task.column_id);
    setCreateTaskOpen(true);
  };

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>Error</CardTitle>
            <CardDescription className="text-destructive">{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleBackToBoards}>
              Back to Boards
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading || !currentBoard) {
    return (
      <>
        <header className="border-b">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <LayoutDashboard className="h-8 w-8 text-primary" />
                <div>
                  <h1 className="text-2xl font-bold">Agent Rangers</h1>
                  <p className="text-sm text-muted-foreground">
                    AI Multi-Agent Kanban Framework
                  </p>
                </div>
              </div>
              <Button variant="outline" onClick={handleBackToBoards}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Boards
              </Button>
            </div>
          </div>
        </header>
        <main className="container mx-auto">
          <div className="flex flex-col h-[calc(100vh-80px)]">
            <div className="border-b px-6 py-4">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-72 mt-2" />
            </div>
            <div className="flex gap-4 p-6">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="w-80 flex-shrink-0">
                  <CardHeader>
                    <Skeleton className="h-6 w-32" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-24 w-full mb-2" />
                    <Skeleton className="h-24 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <header className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <LayoutDashboard className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">Agent Rangers</h1>
                <p className="text-sm text-muted-foreground">
                  AI Multi-Agent Kanban Framework
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={handleBackToBoards}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Boards
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto">
        <div className="flex flex-col h-[calc(100vh-80px)]">
          <div className="border-b px-6 py-4 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">{currentBoard.name}</h2>
              {currentBoard.description && (
                <p className="text-muted-foreground mt-1">
                  {currentBoard.description}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setActivityFeedOpen(true)}>
                <Activity className="mr-2 h-4 w-4" />
                Activity
              </Button>
              <Button variant="outline" onClick={() => setWorkflowEditorOpen(true)}>
                <Settings className="mr-2 h-4 w-4" />
                Workflow
              </Button>
            </div>
          </div>

          <Board
            onCreateColumn={handleCreateColumn}
            onCreateTask={handleCreateTask}
            onEditTask={handleEditTask}
            onEditColumn={handleEditColumn}
          />
        </div>
      </main>

      <CreateColumnDialog
        open={createColumnOpen}
        onOpenChange={(open) => {
          setCreateColumnOpen(open);
          if (!open) setEditingColumn(null);
        }}
        boardId={currentBoard.id}
        editColumn={editingColumn}
      />

      <CreateTaskDialog
        open={createTaskOpen}
        onOpenChange={(open) => {
          setCreateTaskOpen(open);
          if (!open) {
            setEditingTask(null);
            setSelectedColumnId(null);
          }
        }}
        boardId={currentBoard.id}
        columnId={selectedColumnId}
        editTask={editingTask}
      />

      {/* Workflow Editor Dialog */}
      <Dialog open={workflowEditorOpen} onOpenChange={setWorkflowEditorOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Workflow Settings</DialogTitle>
            <DialogDescription>
              Define allowed transitions between columns
            </DialogDescription>
          </DialogHeader>
          <WorkflowEditor boardId={currentBoard.id} />
        </DialogContent>
      </Dialog>

      {/* Activity Feed Dialog */}
      <Dialog open={activityFeedOpen} onOpenChange={setActivityFeedOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Activity Feed</DialogTitle>
            <DialogDescription>
              Recent activity on this board
            </DialogDescription>
          </DialogHeader>
          <ActivityFeed boardId={currentBoard.id} />
        </DialogContent>
      </Dialog>
    </>
  );
}

function App() {
  const { error } = useBoardStore();

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>Error</CardTitle>
            <CardDescription className="text-destructive">{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => window.location.reload()}>
              Reload Page
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/" element={<BoardsListView />} />
        <Route path="/boards/:boardId" element={<BoardView />} />
      </Routes>
    </div>
  );
}

export default App;
