import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useQuiz, useSubmitQuiz, type QuestionResult } from "@/features/quizzes/hooks";

export function QuizPage() {
  const { id } = useParams<{ id: string }>();
  const { data: quiz, isLoading, isError } = useQuiz(id);
  const submit = useSubmitQuiz(id);

  // Map of question_id -> selected choice_id.
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const resultsByQuestion = useMemo(() => {
    const map: Record<string, QuestionResult> = {};
    for (const r of submit.data?.results ?? []) map[r.question_id] = r;
    return map;
  }, [submit.data]);

  if (isLoading) return <p className="text-muted-foreground">Loading quiz…</p>;
  if (isError || !quiz) return <p className="text-destructive">Quiz not found.</p>;

  const graded = submit.data;
  const allAnswered = quiz.questions.every((q) => answers[q.id]);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{quiz.title}</h1>
        {quiz.description && <p className="text-muted-foreground">{quiz.description}</p>}
      </div>

      {graded && (
        <Card className="border-primary/40">
          <CardContent className="py-4 text-lg font-semibold">
            Score: {graded.score} / {graded.total}
          </CardContent>
        </Card>
      )}

      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          submit.mutate(answers);
        }}
      >
        {quiz.questions.map((question, qi) => {
          const result = resultsByQuestion[question.id];
          return (
            <Card key={question.id}>
              <CardHeader>
                <CardTitle className="text-base">
                  {qi + 1}. {question.prompt}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {question.choices.map((choice) => {
                  const selected = answers[question.id] === choice.id;
                  // After grading, highlight the correct choice and a wrong pick.
                  const isCorrectChoice = result?.correct_choice_id === choice.id;
                  const isWrongPick =
                    result && selected && !result.correct && !isCorrectChoice;
                  return (
                    <label
                      key={choice.id}
                      className={cn(
                        "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm",
                        selected && !graded && "border-primary",
                        graded && isCorrectChoice && "border-green-500/60 bg-green-500/10",
                        isWrongPick && "border-destructive/60 bg-destructive/10",
                      )}
                    >
                      <input
                        type="radio"
                        name={question.id}
                        value={choice.id}
                        checked={selected}
                        disabled={Boolean(graded)}
                        onChange={() =>
                          setAnswers((prev) => ({ ...prev, [question.id]: choice.id }))
                        }
                      />
                      <span>{choice.text}</span>
                    </label>
                  );
                })}
                {result && (
                  <p
                    className={cn(
                      "text-sm font-medium",
                      result.correct ? "text-green-600" : "text-destructive",
                    )}
                  >
                    {result.correct ? "Correct" : "Incorrect"}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}

        {quiz.questions.length === 0 && (
          <p className="text-muted-foreground">This quiz has no questions yet.</p>
        )}

        {submit.isError && (
          <p className="text-sm text-destructive">
            {submit.error instanceof Error ? submit.error.message : "Submission failed"}
          </p>
        )}

        {!graded && quiz.questions.length > 0 && (
          <Button type="submit" disabled={!allAnswered || submit.isPending}>
            {submit.isPending ? "Submitting…" : "Submit quiz"}
          </Button>
        )}
      </form>
    </div>
  );
}
