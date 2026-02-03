import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  FileCode,
  Cpu,
} from 'lucide-react';
import type { AgentOutput } from '@/types';

interface AgentOutputViewerProps {
  output: AgentOutput;
}

export function AgentOutputViewer({ output }: AgentOutputViewerProps) {
  const [showStructured, setShowStructured] = useState(false);
  const [showFiles, setShowFiles] = useState(false);

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
                {output.phase}
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

        {/* Output content */}
        {output.output_content && (
          <div className="prose prose-sm max-w-none">
            <div className="text-sm text-foreground whitespace-pre-wrap">
              {renderMarkdown(output.output_content)}
            </div>
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

        {/* Files created - collapsible */}
        {output.files_created && Array.isArray(output.files_created) && output.files_created.length > 0 && (
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
                <FileCode className="h-4 w-4" />
                Files Created
              </div>
              <Badge variant="secondary" className="text-xs">
                {output.files_created.length} files
              </Badge>
            </button>
            {showFiles && (
              <div className="px-3 pb-3 pt-1">
                <div className="space-y-2">
                  {output.files_created.map((file, index) => (
                    <div
                      key={index}
                      className="p-2 bg-muted rounded-md text-xs font-mono"
                    >
                      {typeof file === 'string' ? file : JSON.stringify(file)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
