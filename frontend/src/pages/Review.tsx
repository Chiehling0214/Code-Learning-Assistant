import { useState } from "react";
import { Link } from "react-router-dom";

import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  useAnswerReview,
  useDueReviews,
  useNotebook,
  type ReviewItem,
} from "@/features/review/hooks";

const SOURCE_LABEL: Record<ReviewItem["source"], string> = {
  quiz: "Quiz",
  placement: "Placement",
  exercise: "Exercise",
};

/** One flashcard: an MCQ to re-answer, or an exercise to retry. */
function Flashcard({
  item,
  onDone,
}: {
  item: ReviewItem;
  onDone: () => void;
}) {
  const answer = useAnswerReview();
  const [picked, setPicked] = useState<string | null>(null);

  const p = item.payload;
  const revealed = picked !== null;

  if (p.kind === "exercise") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Retry this exercise — {p.title ?? "exercise"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {p.prompt && <Markdown content={p.prompt} />}
          <div className="flex flex-wrap gap-2">
            {p.exercise_id && (
              <Button asChild variant="outline" size="sm">
                <Link to={`/exercises/${p.exercise_id}`}>Open the exercise</Link>
              </Button>
            )}
            <Button
              size="sm"
              disabled={answer.isPending}
              onClick={() => answer.mutate({ itemId: item.id, correct: true }, { onSuccess: onDone })}
            >
              I solved it
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={answer.isPending}
              onClick={() =>
                answer.mutate({ itemId: item.id, correct: false }, { onSuccess: onDone })
              }
            >
              Still stuck — show me tomorrow
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const correctChoice = p.choices?.find((c) => c.is_correct);
  const pickedCorrect = revealed && picked === correctChoice?.id;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          {SOURCE_LABEL[item.source]}
          {p.quiz_title ? ` — ${p.quiz_title}` : ""}
        </CardTitle>
        <Markdown content={p.prompt ?? ""} />
      </CardHeader>
      <CardContent className="space-y-2">
        {(p.choices ?? []).map((c) => {
          const isCorrect = revealed && c.is_correct;
          const isWrongPick = revealed && picked === c.id && !c.is_correct;
          return (
            <button
              key={c.id}
              type="button"
              disabled={revealed || answer.isPending}
              onClick={() => {
                setPicked(c.id);
                answer.mutate({ itemId: item.id, correct: c.is_correct });
              }}
              className={cn(
                "block w-full rounded-md border px-3 py-2 text-left text-sm transition-colors",
                !revealed && "hover:bg-accent",
                isCorrect && "border-green-500/60 bg-green-500/10",
                isWrongPick && "border-destructive/60 bg-destructive/10",
              )}
            >
              {c.text}
            </button>
          );
        })}

        {revealed && (
          <>
            <p
              className={cn(
                "text-sm font-medium",
                pickedCorrect ? "text-green-600" : "text-destructive",
              )}
            >
              {pickedCorrect ? "Correct — nice recovery!" : "Not yet — it'll come back tomorrow."}
            </p>
            {p.explanation && (
              <div className="rounded-md bg-muted p-3 text-sm">
                <span className="font-medium">Explanation. </span>
                {p.explanation}
              </div>
            )}
            <Button size="sm" onClick={onDone}>
              Next
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function DueQueue() {
  const { data, isLoading } = useDueReviews();
  // Bump to force a fresh card after each answer (the refetched list drops it).
  const [, setDoneCount] = useState(0);

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading reviews…</p>;
  const items = data?.items ?? [];
  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="py-6 text-sm text-muted-foreground">
          Nothing due right now — anything you get wrong will come back here on a
          spaced schedule. 🎉
        </CardContent>
      </Card>
    );
  }
  const current = items[0];
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">{items.length} due</p>
      <Flashcard key={current.id} item={current} onDone={() => setDoneCount((n) => n + 1)} />
    </div>
  );
}

function Notebook() {
  const { data: items = [], isLoading } = useNotebook();
  if (isLoading) return <p className="text-sm text-muted-foreground">Loading notebook…</p>;
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No mistakes captured yet.</p>;
  }
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.id}
          className={cn("rounded-md border p-3", item.retired && "opacity-60")}
        >
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-sm font-medium">
              {item.payload.kind === "exercise"
                ? item.payload.title
                : item.payload.prompt}
            </p>
            <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {item.retired ? "mastered" : SOURCE_LABEL[item.source]}
            </span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.retired
              ? `Mastered after ${item.passes} passes`
              : `Next review ${new Date(item.due_at).toLocaleDateString()} · missed ${
                  item.lapses + 1
                }×`}
          </p>
        </li>
      ))}
    </ul>
  );
}

export function ReviewPage() {
  const [tab, setTab] = useState<"due" | "notebook">("due");

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Review</h1>
        <p className="text-muted-foreground">
          Your mistakes come back on a spaced schedule until you've mastered them.
        </p>
      </div>

      <div className="flex gap-2">
        <Button size="sm" variant={tab === "due" ? "default" : "outline"} onClick={() => setTab("due")}>
          Due now
        </Button>
        <Button
          size="sm"
          variant={tab === "notebook" ? "default" : "outline"}
          onClick={() => setTab("notebook")}
        >
          Mistakes notebook
        </Button>
      </div>

      {tab === "due" ? <DueQueue /> : <Notebook />}
    </div>
  );
}
