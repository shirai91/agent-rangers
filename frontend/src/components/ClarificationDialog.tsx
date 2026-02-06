import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { HelpCircle, Send, SkipForward, Loader2 } from 'lucide-react';
import type { ClarificationQuestion } from '@/types';

interface ClarificationDialogProps {
  questions: ClarificationQuestion[];
  summary: string;
  confidence: number;
  onSubmit: (answers: Record<string, string | string[]>) => void;
  onSkip: () => void;
  loading?: boolean;
}

export function ClarificationDialog({
  questions,
  summary,
  confidence,
  onSubmit,
  onSkip,
  loading = false,
}: ClarificationDialogProps) {
  const [answers, setAnswers] = useState<Record<string, string | string[]>>(() => {
    const initial: Record<string, string | string[]> = {};
    questions.forEach((q) => {
      if (q.type === 'multiple_choice') {
        initial[q.id] = [];
      } else {
        initial[q.id] = '';
      }
    });
    return initial;
  });

  const handleSingleChoice = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleMultipleChoice = (questionId: string, value: string) => {
    setAnswers((prev) => {
      const current = prev[questionId] as string[];
      const updated = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      return { ...prev, [questionId]: updated };
    });
  };

  const handleFreeText = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const isAnswerValid = (question: ClarificationQuestion): boolean => {
    const answer = answers[question.id];
    if (!question.required) return true;

    if (question.type === 'free_text') {
      return typeof answer === 'string' && answer.trim().length > 0;
    }
    if (question.type === 'single_choice') {
      return typeof answer === 'string' && answer.length > 0;
    }
    if (question.type === 'multiple_choice') {
      return Array.isArray(answer) && answer.length > 0;
    }
    return false;
  };

  const canSubmit = questions.every((q) => isAnswerValid(q));

  const handleSubmit = () => {
    if (canSubmit && !loading) {
      onSubmit(answers);
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6 bg-background border rounded-lg shadow-lg max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="p-2 bg-blue-500/10 rounded-full">
          <HelpCircle className="h-5 w-5 text-blue-500" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h2 className="text-xl font-semibold">Clarification Needed</h2>
            <Badge variant="outline" className="text-xs">
              {Math.round(confidence * 100)}% confidence
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{summary}</p>
        </div>
      </div>

      {/* Questions */}
      <div className="flex flex-col gap-4">
        {questions.map((question) => (
          <div
            key={question.id}
            className="border rounded-lg p-4 bg-card"
          >
            <Label className="text-base font-medium mb-2 block">
              {question.question}
              {question.required && (
                <span className="text-destructive ml-1">*</span>
              )}
            </Label>

            {question.context && (
              <p className="text-sm text-muted-foreground mb-3">
                {question.context}
              </p>
            )}

            {question.type === 'single_choice' && (
              <div className="flex flex-col gap-2">
                {question.options.map((option) => {
                  const isSelected = answers[question.id] === option;
                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() => handleSingleChoice(question.id, option)}
                      disabled={loading}
                      className={`
                        px-4 py-3 text-left rounded-md border transition-colors
                        ${
                          isSelected
                            ? 'border-primary bg-primary/5 text-foreground'
                            : 'border-border hover:bg-muted/50 text-foreground'
                        }
                        ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                    >
                      {option}
                    </button>
                  );
                })}
              </div>
            )}

            {question.type === 'multiple_choice' && (
              <div className="flex flex-col gap-2">
                {question.options.map((option) => {
                  const isSelected = (answers[question.id] as string[]).includes(option);
                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() => handleMultipleChoice(question.id, option)}
                      disabled={loading}
                      className={`
                        px-4 py-3 text-left rounded-md border transition-colors
                        ${
                          isSelected
                            ? 'border-primary bg-primary/5 text-foreground'
                            : 'border-border hover:bg-muted/50 text-foreground'
                        }
                        ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      `}
                    >
                      {option}
                    </button>
                  );
                })}
              </div>
            )}

            {question.type === 'free_text' && (
              <Textarea
                value={answers[question.id] as string}
                onChange={(e) => handleFreeText(question.id, e.target.value)}
                disabled={loading}
                placeholder="Enter your answer..."
                className="min-h-[100px]"
              />
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <Button
          variant="outline"
          onClick={onSkip}
          disabled={loading}
          className="gap-2"
        >
          <SkipForward className="h-4 w-4" />
          Skip & Let AI Decide
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={!canSubmit || loading}
          className="gap-2"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          Submit Answers
        </Button>
      </div>
    </div>
  );
}
