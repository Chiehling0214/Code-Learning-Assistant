import { ArrowRight, CheckCircle2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { AskTeacherPanel } from "@/components/AskTeacherPanel";
import { Markdown } from "@/components/Markdown";
import { ProgressBar } from "@/components/ProgressBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useRecordLearningActivity } from "@/features/progress/hooks";
import { useQuiz, useSubmitQuiz, type QuestionResult } from "@/features/quizzes/hooks";
import { cn } from "@/lib/utils";

type QuizPhase = "answering" | "review" | "summary";

export function QuizPage() {
  const { id } = useParams<{ id: string }>();
  const { data: quiz, isLoading, isError } = useQuiz(id);
  const submit = useSubmitQuiz(id);
  const { mutate: recordActivity } = useRecordLearningActivity();
  const recordedActivity = useRef<string>();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [phase, setPhase] = useState<QuizPhase>("answering");

  useEffect(() => {
    if (quiz?.id && recordedActivity.current !== quiz.id) {
      recordedActivity.current = quiz.id;
      recordActivity({ item_type: "quiz", item_id: quiz.id });
    }
  }, [quiz?.id, recordActivity]);

  const resultsByQuestion = useMemo(() => {
    const map: Record<string, QuestionResult> = {};
    for (const result of submit.data?.results ?? []) map[result.question_id] = result;
    return map;
  }, [submit.data]);

  const reviewContext = useMemo(() => {
    if (!quiz || !submit.data) return "";
    const lines: string[] = [`The learner just took the quiz "${quiz.title}":`];
    quiz.questions.forEach((question, index) => {
      const result = resultsByQuestion[question.id];
      lines.push(`\nQuestion ${index + 1}: ${question.prompt}`);
      question.choices.forEach((choice) => {
        const marks = [
          result?.correct_choice_id === choice.id ? "correct answer" : "",
          result?.selected_choice_id === choice.id ? "learner's pick" : "",
        ].filter(Boolean).join(", ");
        lines.push(`- ${choice.text}${marks ? ` (${marks})` : ""}`);
      });
      if (result) lines.push(`Result: ${result.correct ? "correct" : "incorrect"}.`);
      if (result?.explanation) lines.push(`Explanation: ${result.explanation}`);
    });
    return lines.join("\n").slice(0, 18000);
  }, [quiz, resultsByQuestion, submit.data]);

  if (isLoading) return <p className="text-muted-foreground">Loading quiz…</p>;
  if (isError || !quiz) return <p className="text-destructive">Quiz not found.</p>;

  const total = quiz.questions.length;
  const question = quiz.questions[currentIndex];
  const result = question ? resultsByQuestion[question.id] : undefined;
  const selectedChoiceId = question ? answers[question.id] : undefined;
  const stepPercent = total ? ((currentIndex + 1) / total) * 100 : 0;

  const submitAnswers = () => {
    submit.mutate(answers, {
      onSuccess: () => {
        setCurrentIndex(0);
        setPhase("review");
      },
    });
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <p className="page-kicker">Knowledge check</p>
        <h1 className="page-heading">{quiz.title}</h1>
        {quiz.description && <p className="mt-2 text-muted-foreground">{quiz.description}</p>}
      </header>

      {total === 0 ? (
        <Card><CardContent className="py-6 text-muted-foreground">This quiz has no questions yet.</CardContent></Card>
      ) : phase === "summary" && submit.data ? (
        <>
          <Card className="border-primary/30">
            <CardContent className="flex flex-col items-center py-8 text-center">
              <CheckCircle2 className="size-8 text-primary" />
              <p className="mt-4 text-sm font-medium text-muted-foreground">Quiz complete</p>
              <p className="mt-1 text-3xl font-semibold">{submit.data.score} / {submit.data.total}</p>
              <Button asChild variant="outline" className="mt-6">
                <Link to={`/lessons/${quiz.lesson_id}`}>Back to lesson</Link>
              </Button>
            </CardContent>
          </Card>
          <AskTeacherPanel
            title="Ask about a question"
            placeholder="e.g. Why is my answer to question 1 wrong?"
            context={reviewContext}
          />
        </>
      ) : question ? (
        <>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>{phase === "review" ? "Reviewing answers" : "Question"} {currentIndex + 1} of {total}</span>
              <span>{Math.round(stepPercent)}%</span>
            </div>
            <ProgressBar percent={stepPercent} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Question {currentIndex + 1}</CardTitle>
              <Markdown content={question.prompt} />
            </CardHeader>
            <CardContent className="space-y-3">
              {question.choices.map((choice) => {
                const selected = selectedChoiceId === choice.id;
                const isCorrectChoice = phase === "review" && result?.correct_choice_id === choice.id;
                const isWrongPick = phase === "review" && selected && result && !result.correct;
                return (
                  <button
                    key={choice.id}
                    type="button"
                    disabled={phase === "review"}
                    onClick={() => setAnswers((current) => ({ ...current, [question.id]: choice.id }))}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left text-sm transition-colors",
                      phase === "answering" && "hover:bg-accent/60",
                      selected && phase === "answering" && "border-primary bg-primary/[0.04]",
                      isCorrectChoice && "border-green-600/50 bg-green-600/10",
                      isWrongPick && "border-destructive/60 bg-destructive/10",
                    )}
                  >
                    <span className={cn("size-3.5 shrink-0 rounded-full border", selected && "border-[4px] border-primary")} />
                    <span>{choice.text}</span>
                  </button>
                );
              })}

              {phase === "review" && result && (
                <div className="space-y-3 pt-2">
                  <p className={cn("text-sm font-semibold", result.correct ? "text-green-700" : "text-destructive")}>
                    {result.correct ? "Correct" : "Incorrect"}
                  </p>
                  {result.explanation && (
                    <div className="rounded-lg bg-muted p-4 text-sm leading-6">
                      <span className="font-semibold">Explanation. </span>{result.explanation}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {submit.isError && (
            <p className="text-sm text-destructive">
              {submit.error instanceof Error ? submit.error.message : "Submission failed"}
            </p>
          )}

          <div className="flex justify-end">
            {phase === "answering" ? (
              <Button
                disabled={!selectedChoiceId || submit.isPending}
                onClick={() => currentIndex === total - 1 ? submitAnswers() : setCurrentIndex((index) => index + 1)}
              >
                {submit.isPending ? "Submitting…" : currentIndex === total - 1 ? "Submit answers" : "Next question"}
                {!submit.isPending && <ArrowRight className="size-4" />}
              </Button>
            ) : (
              <Button onClick={() => {
                if (currentIndex === total - 1) setPhase("summary");
                else setCurrentIndex((index) => index + 1);
              }}>
                {currentIndex === total - 1 ? "Finish review" : "Next answer"}
                <ArrowRight className="size-4" />
              </Button>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}
