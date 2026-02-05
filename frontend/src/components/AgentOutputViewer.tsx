import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  FileCode,
  FilePlus,
  FileEdit,
  Cpu,
  Eye,
  ExternalLink,
  Loader2,
  GitBranch,
  AlertCircle,
  GitCommit,
} from 'lucide-react';
import type { AgentOutput } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface GitCommit {
  committed: boolean;
  commit_hash?: string;
  files_committed?: number;
  message?: string;
  reason?: string;
}

interface GitChanges {
  created: string[];
  modified: string[];
  deleted: string[];
  all_changed: string[];
  diff_stats: string[];
  is_git_repo: boolean;
  error?: string;
  commit?: GitCommit;
  // Absolute paths for file viewing
  created_absolute?: string[];
  modified_absolute?: string[];
  working_directory?: string;
}

interface BranchInfo {
  name: string | null;
  source: string | null;
  checkout_success: boolean | null;
  created?: boolean;
}

interface AgentOutputViewerProps {
  output: AgentOutput;
}

interface FileRowProps {
  filePath: string;
  variant: 'created' | 'modified' | 'default';
  onView: () => void;
  rawUrl: string;
}

function FileRow({ filePath, variant, onView, rawUrl }: FileRowProps) {
  const fileName = filePath.split('/').pop() || filePath;
  
  const iconColor = {
    created: 'text-green-600',
    modified: 'text-yellow-600',
    default: 'text-muted-foreground',
  }[variant];

  const Icon = variant === 'created' ? FilePlus : variant === 'modified' ? FileEdit : FileCode;

  return (
    <div className="p-2 bg-muted rounded-md flex items-center justify-between gap-2">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Icon className={`h-4 w-4 flex-shrink-0 ${iconColor}`} />
        <span className="text-xs font-mono truncate" title={filePath}>
          {fileName}
        </span>
      </div>
      <div className="flex items-center gap-1 flex-shrink-0">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2"
          onClick={onView}
        >
          <Eye className="h-3 w-3 mr-1" />
          View
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2"
          asChild
        >
          <a
            href={rawUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="h-3 w-3 mr-1" />
            Raw
          </a>
        </Button>
      </div>
    </div>
  );
}

export function AgentOutputViewer({ output }: AgentOutputViewerProps) {
  const [showContent, setShowContent] = useState(false);
  const [showStructured, setShowStructured] = useState(false);
  const [showFiles, setShowFiles] = useState(true);
  const [viewingFile, setViewingFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  // Check if path is a workspace path or absolute project path
  const isWorkspacePath = (filePath: string): boolean => {
    return filePath.includes('/tmp/workspaces/');
  };

  // Extract task_id from file path (format: /tmp/workspaces/{task_id}/...)
  const extractTaskId = (filePath: string): string | null => {
    const match = filePath.match(/\/tmp\/workspaces\/([^\/]+)/);
    return match?.[1] ?? null;
  };

  // Extract relative path from full path
  const extractRelativePath = (filePath: string): string => {
    const match = filePath.match(/\/tmp\/workspaces\/[^\/]+\/(.+)/);
    return match?.[1] ?? filePath;
  };

  // Load file content
  const loadFileContent = async (filePath: string) => {
    setFileLoading(true);
    setFileError(null);
    setViewingFile(filePath);

    try {
      let response: Response;
      
      if (isWorkspacePath(filePath)) {
        // Old workspace path format
        const taskId = extractTaskId(filePath);
        const relativePath = extractRelativePath(filePath);
        
        if (!taskId) {
          throw new Error('Could not extract task ID from file path');
        }
        
        response = await fetch(
          `${API_URL}/api/agents/workspaces/${taskId}/files/${relativePath}`
        );
      } else {
        // Absolute project path - use new endpoint
        response = await fetch(
          `${API_URL}/api/agents/files/read?path=${encodeURIComponent(filePath)}`
        );
      }
      
      if (!response.ok) {
        throw new Error(`Failed to load file: ${response.statusText}`);
      }
      
      const data = await response.json();
      setFileContent(data.content);
    } catch (err) {
      setFileError(err instanceof Error ? err.message : 'Failed to load file');
    } finally {
      setFileLoading(false);
    }
  };

  // Get raw file URL for direct viewing in browser
  const getRawFileUrl = (filePath: string): string => {
    if (isWorkspacePath(filePath)) {
      const taskId = extractTaskId(filePath);
      const relativePath = extractRelativePath(filePath);
      return `${API_URL}/api/agents/workspaces/${taskId}/raw/${relativePath}`;
    } else {
      return `${API_URL}/api/agents/files/raw?path=${encodeURIComponent(filePath)}`;
    }
  };

  const getStatusBadge = () => {
    switch (output.status) {
      case 'completed':
        return (
          <Badge variant="default" className="bg-green-600 text-white">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Completed
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive">
            <XCircle className="h-3 w-3 mr-1" />
            Failed
          </Badge>
        );
      case 'running':
        return (
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            Running
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {output.status}
          </Badge>
        );
    }
  };

  const getPhaseLabel = (phase: string) => {
    const labels: Record<string, string> = {
      architecture: 'Planning',
      development: 'Coding',
      review: 'Review',
    };
    return labels[phase] || phase;
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const formatTokens = (tokens: number | null) => {
    if (!tokens) return 'N/A';
    return tokens.toLocaleString();
  };

  const renderMarkdown = (content: string) => {
    // Simple markdown rendering for code blocks
    const lines = content.split('\n');
    const elements: JSX.Element[] = [];
    let inCodeBlock = false;
    let codeBlockContent: string[] = [];
    let codeBlockLanguage = '';

    lines.forEach((line, index) => {
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // End code block
          elements.push(
            <div key={`code-${index}`} className="my-3">
              <div className="bg-muted rounded-md overflow-hidden">
                {codeBlockLanguage && (
                  <div className="px-4 py-2 bg-muted-foreground/10 text-xs font-mono text-muted-foreground border-b">
                    {codeBlockLanguage}
                  </div>
                )}
                <pre className="p-4 overflow-x-auto">
                  <code className="text-sm font-mono">
                    {codeBlockContent.join('\n')}
                  </code>
                </pre>
              </div>
            </div>
          );
          codeBlockContent = [];
          codeBlockLanguage = '';
          inCodeBlock = false;
        } else {
          // Start code block
          codeBlockLanguage = line.slice(3).trim();
          inCodeBlock = true;
        }
      } else if (inCodeBlock) {
        codeBlockContent.push(line);
      } else {
        // Regular line
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('#')) {
          const level = trimmedLine.match(/^#+/)?.[0].length || 1;
          const text = trimmedLine.replace(/^#+\s*/, '');
          const className = level === 1
            ? 'text-lg font-semibold mt-4 mb-2'
            : 'text-base font-semibold mt-3 mb-2';
          elements.push(
            <div key={`heading-${index}`} className={className}>
              {text}
            </div>
          );
        } else if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
          elements.push(
            <div key={`li-${index}`} className="ml-4 my-1">
              <span className="mr-2">•</span>
              {trimmedLine.slice(2)}
            </div>
          );
        } else if (trimmedLine) {
          elements.push(
            <div key={`p-${index}`} className="my-2">
              {line}
            </div>
          );
        } else {
          elements.push(<div key={`br-${index}`} className="h-2" />);
        }
      }
    });

    return elements;
  };

  return (
    <Card className="mb-3">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              {output.agent_name}
              <Badge variant="outline" className="text-xs font-normal">
                {getPhaseLabel(output.phase)}
              </Badge>
              {output.iteration > 1 && (
                <Badge variant="secondary" className="text-xs font-normal">
                  Iteration {output.iteration}
                </Badge>
              )}
            </CardTitle>
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>{formatDuration(output.duration_ms)}</span>
              </div>
              {output.tokens_used !== null && (
                <div>
                  <span>{formatTokens(output.tokens_used)} tokens</span>
                </div>
              )}
            </div>
          </div>
          <div>{getStatusBadge()}</div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Error message */}
        {output.error_message && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <div className="flex items-start gap-2">
              <XCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
              <div className="text-sm text-destructive">
                {output.error_message}
              </div>
            </div>
          </div>
        )}

        {/* Output content - collapsible, hidden by default */}
        {output.output_content && (
          <div className="border rounded-md">
            <button
              onClick={() => setShowContent(!showContent)}
              className="w-full px-3 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2 text-sm font-medium">
                {showContent ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                Output Content
              </div>
              <Badge variant="secondary" className="text-xs">
                {output.output_content.length} chars
              </Badge>
            </button>
            {showContent && (
              <div className="px-3 pb-3 pt-1">
                <div className="prose prose-sm max-w-none">
                  <div className="text-sm text-foreground whitespace-pre-wrap">
                    {renderMarkdown(output.output_content)}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Structured output - collapsible */}
        {output.output_structured && Object.keys(output.output_structured).length > 0 && (
          <div className="border rounded-md">
            <button
              onClick={() => setShowStructured(!showStructured)}
              className="w-full px-3 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2 text-sm font-medium">
                {showStructured ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                Structured Output
              </div>
              <Badge variant="secondary" className="text-xs">
                {Object.keys(output.output_structured).length} fields
              </Badge>
            </button>
            {showStructured && (
              <div className="px-3 pb-3 pt-1">
                <pre className="p-3 bg-muted rounded-md overflow-x-auto">
                  <code className="text-xs font-mono">
                    {JSON.stringify(output.output_structured, null, 2)}
                  </code>
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Branch info */}
        {(() => {
          const branchInfo = output.output_structured?.branch as BranchInfo | undefined;
          if (!branchInfo?.name) return null;
          
          const sourceLabel = {
            'task_text': 'from task',
            'llm_suggestion': 'detected',
            'default': 'default',
          }[branchInfo.source || 'default'] || branchInfo.source;
          
          return (
            <div className="flex items-center gap-2 text-xs p-2 bg-muted/50 rounded-md">
              <GitBranch className="h-4 w-4 text-purple-600" />
              <span className="font-medium">Branch:</span>
              <code className="bg-muted px-1.5 py-0.5 rounded">{branchInfo.name}</code>
              {branchInfo.created && (
                <Badge variant="default" className="text-xs bg-green-600">
                  NEW
                </Badge>
              )}
              <Badge variant="outline" className="text-xs">
                {sourceLabel}
              </Badge>
              {branchInfo.checkout_success === false && (
                <Badge variant="destructive" className="text-xs">
                  checkout failed
                </Badge>
              )}
            </div>
          );
        })()}

        {/* Files Changed - collapsible (with git tracking support) */}
        {(() => {
          const gitChanges = output.output_structured?.git_changes as GitChanges | undefined;
          const hasGitChanges = gitChanges?.is_git_repo && !gitChanges?.error;
          const filesCreated = output.files_created || [];
          const totalFiles = hasGitChanges 
            ? (gitChanges.created?.length || 0) + (gitChanges.modified?.length || 0)
            : filesCreated.length;
          
          if (totalFiles === 0) return null;

          return (
            <div className="border rounded-md">
              <button
                onClick={() => setShowFiles(!showFiles)}
                className="w-full px-3 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-2 text-sm font-medium">
                  {showFiles ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  {hasGitChanges ? (
                    <GitBranch className="h-4 w-4 text-green-600" />
                  ) : (
                    <FileCode className="h-4 w-4" />
                  )}
                  Files Changed
                  {hasGitChanges && (
                    <Badge variant="outline" className="text-xs ml-1 text-green-600 border-green-600">
                      git tracked
                    </Badge>
                  )}
                </div>
                <Badge variant="secondary" className="text-xs">
                  {totalFiles} files
                </Badge>
              </button>
              {showFiles && (
                <div className="px-3 pb-3 pt-1">
                  <div className="space-y-3">
                    {/* Git-tracked changes */}
                    {hasGitChanges ? (
                      <>
                        {/* Created files - use absolute paths if available */}
                        {gitChanges.created && gitChanges.created.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-2 text-xs font-medium text-green-600">
                              <FilePlus className="h-3 w-3" />
                              Created ({gitChanges.created.length})
                            </div>
                            <div className="space-y-1">
                              {gitChanges.created.map((file, index) => {
                                // Use absolute path if available, otherwise construct from working_directory
                                const absolutePath = gitChanges.created_absolute?.[index] 
                                  || (gitChanges.working_directory ? `${gitChanges.working_directory}/${file}` : file);
                                return (
                                  <FileRow 
                                    key={`created-${index}`}
                                    filePath={absolutePath}
                                    variant="created"
                                    onView={() => loadFileContent(absolutePath)}
                                    rawUrl={getRawFileUrl(absolutePath)}
                                  />
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Modified files - use absolute paths if available */}
                        {gitChanges.modified && gitChanges.modified.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-2 text-xs font-medium text-yellow-600">
                              <FileEdit className="h-3 w-3" />
                              Modified ({gitChanges.modified.length})
                            </div>
                            <div className="space-y-1">
                              {gitChanges.modified.map((file, index) => {
                                // Use absolute path if available, otherwise construct from working_directory
                                const absolutePath = gitChanges.modified_absolute?.[index]
                                  || (gitChanges.working_directory ? `${gitChanges.working_directory}/${file}` : file);
                                return (
                                  <FileRow 
                                    key={`modified-${index}`}
                                    filePath={absolutePath}
                                    variant="modified"
                                    onView={() => loadFileContent(absolutePath)}
                                    rawUrl={getRawFileUrl(absolutePath)}
                                  />
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Diff stats */}
                        {gitChanges.diff_stats && gitChanges.diff_stats.length > 0 && (
                          <div className="mt-3 pt-3 border-t">
                            <div className="text-xs font-medium text-muted-foreground mb-2">
                              Diff Summary
                            </div>
                            <pre className="text-xs font-mono bg-muted p-2 rounded overflow-x-auto">
                              {gitChanges.diff_stats.join('\n')}
                            </pre>
                          </div>
                        )}

                        {/* Commit info */}
                        {gitChanges.commit && (
                          <div className="mt-3 pt-3 border-t">
                            {gitChanges.commit.committed ? (
                              <div className="flex items-center gap-2 text-xs">
                                <CheckCircle2 className="h-4 w-4 text-green-600" />
                                <span className="font-medium text-green-600">Auto-committed</span>
                                {gitChanges.commit.commit_hash && (
                                  <code className="bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                                    {gitChanges.commit.commit_hash.slice(0, 7)}
                                  </code>
                                )}
                                <span className="text-muted-foreground">
                                  ({gitChanges.commit.files_committed} files)
                                </span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <AlertCircle className="h-4 w-4" />
                                <span>Not committed: {gitChanges.commit.reason}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    ) : (
                      /* Fallback: non-git tracked files */
                      <div className="space-y-1">
                        {filesCreated.map((file, index) => {
                          const filePath = typeof file === 'string' ? file : JSON.stringify(file);
                          return (
                            <FileRow 
                              key={index}
                              filePath={filePath}
                              variant="default"
                              onView={() => loadFileContent(filePath)}
                              rawUrl={getRawFileUrl(filePath)}
                            />
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })()}

        {/* File Viewer Dialog */}
        <Dialog open={viewingFile !== null} onOpenChange={() => {
          setViewingFile(null);
          setFileContent(null);
          setFileError(null);
        }}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileCode className="h-5 w-5" />
                {viewingFile?.split('/').pop()}
              </DialogTitle>
            </DialogHeader>
            <div className="flex-1 overflow-auto">
              {fileLoading && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">Loading file...</span>
                </div>
              )}
              {fileError && (
                <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-md">
                  <div className="flex items-center gap-2 text-destructive">
                    <XCircle className="h-4 w-4" />
                    {fileError}
                  </div>
                </div>
              )}
              {fileContent && !fileLoading && (
                <div className="bg-muted rounded-md overflow-hidden">
                  <div className="px-4 py-2 bg-muted-foreground/10 text-xs font-mono text-muted-foreground border-b flex items-center justify-between">
                    <span>{viewingFile?.split('/').pop()}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs"
                      asChild
                    >
                      <a
                        href={viewingFile ? getRawFileUrl(viewingFile) : '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        Open in new tab
                      </a>
                    </Button>
                  </div>
                  <pre className="p-4 overflow-auto max-h-[60vh]">
                    <code className="text-sm font-mono whitespace-pre-wrap">
                      {fileContent}
                    </code>
                  </pre>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
