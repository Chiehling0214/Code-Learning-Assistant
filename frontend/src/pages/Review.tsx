import { useState } from "react";
import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { Markdown } from "@/components/Markdown";
import { ProgressBar } from "@/components/ProgressBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  useAnswerReview,
  useDueReviews,
  useNotebook,
  useSaveReviewNote,
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
  const [exerciseResult, setExerciseResult] = useState<boolean | null>(null);

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
            {exerciseResult === null ? (
              <>
                <Button
                  size="sm"
                  disabled={answer.isPending}
                  onClick={() => {
                    setExerciseResult(true);
                    answer.mutate(
                      { itemId: item.id, correct: true },
                      { onError: () => setExerciseResult(null) },
                    );
                  }}
                >
                  I solved it
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={answer.isPending}
                  onClick={() => {
                    setExerciseResult(false);
                    answer.mutate(
                      { itemId: item.id, correct: false },
                      { onError: () => setExerciseResult(null) },
                    );
                  }}
                >
                  Still stuck — show me tomorrow
                </Button>
              </>
            ) : (
              <div className="w-full space-y-3">
                <p className="text-sm font-medium">
                  {exerciseResult ? "Nice work — this review has been scheduled forward." : "No problem — this will return tomorrow."}
                </p>
                <Button size="sm" disabled={answer.isPending} onClick={onDone}>
                  {answer.isPending ? "Saving…" : "Next"}
                </Button>
              </div>
            )}
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
                answer.mutate(
                  { itemId: item.id, correct: c.is_correct },
                  { onError: () => setPicked(null) },
                );
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
            <Button size="sm" disabled={answer.isPending} onClick={onDone}>
              {answer.isPending ? "Saving…" : "Next"}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function DueQueue() {
  const { data, isLoading } = useDueReviews();
  const queryClient = useQueryClient();
  const [completed, setCompleted] = useState(0);

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
  const sessionTotal = completed + items.length;
  const goNext = () => {
    setCompleted((count) => count + 1);
    queryClient.setQueryData<{ due_count: number; items: ReviewItem[] }>(
      ["reviews-due"],
      (old) => old
        ? { due_count: Math.max(0, old.due_count - 1), items: old.items.filter((item) => item.id !== current.id) }
        : old,
    );
    queryClient.invalidateQueries({ queryKey: ["reviews-due"] });
  };
  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Review {completed + 1} of {sessionTotal}</span>
          <span>{items.length} remaining</span>
        </div>
        <ProgressBar percent={sessionTotal ? (completed / sessionTotal) * 100 : 100} />
      </div>
      <Flashcard key={current.id} item={current} onDone={goNext} />
    </div>
  );
}

function NotebookEntry({ item }: { item: ReviewItem }) {
  const saveNote = useSaveReviewNote();
  const [note, setNote] = useState(item.note);

  return (
    <li className={cn("rounded-lg border bg-card", item.retired && "opacity-70")}>
      <details className="group">
        <summary className="flex min-h-16 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium">
              {item.payload.kind === "exercise" ? item.payload.title : item.payload.prompt}
            </span>
            <span className="mt-1 block text-xs text-muted-foreground">
              {item.retired
                ? `Mastered after ${item.passes} passes`
                : `Next review ${new Date(item.due_at).toLocaleDateString()} · missed ${
                    item.lapses + 1
                  }×`}
            </span>
          </span>
          <span className="shrink-0 rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
            {item.retired ? "Mastered" : SOURCE_LABEL[item.source]}
          </span>
        </summary>
        <div className="space-y-4 border-t px-4 py-4">
          {item.payload.kind === "mcq" && item.payload.choices && (
            <div className="space-y-2 text-sm">
              <p className="font-medium">Answer</p>
              <p className="text-muted-foreground">
                {item.payload.choices.find((choice) => choice.is_correct)?.text ?? "—"}
              </p>
              {item.payload.explanation && (
                <p className="rounded-md bg-muted px-3 py-2 leading-6">
                  {item.payload.explanation}
                </p>
              )}
            </div>
          )}
          {item.payload.kind === "exercise" && item.payload.exercise_id && (
            <Button asChild variant="outline" size="sm">
              <Link to={`/exercises/${item.payload.exercise_id}`}>Retry exercise</Link>
            </Button>
          )}
          <div className="space-y-2">
            <label htmlFor={`note-${item.id}`} className="text-sm font-medium">
              My note
            </label>
            <textarea
              id={`note-${item.id}`}
              className="min-h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={note}
              maxLength={2000}
              placeholder="Write what confused you or a rule you want to remember…"
              onChange={(event) => setNote(event.target.value)}
            />
            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant="outline"
                disabled={saveNote.isPending || note === item.note}
                onClick={() => saveNote.mutate({ itemId: item.id, note })}
              >
                {saveNote.isPending ? "Saving…" : "Save note"}
              </Button>
              {saveNote.isSuccess && (
                <span className="text-xs text-muted-foreground" role="status">Saved</span>
              )}
            </div>
          </div>
        </div>
      </details>
    </li>
  );
}

function Notebook() {
  const { data: items = [], isLoading } = useNotebook();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<"all" | "active" | "mastered">("active");
  const [source, setSource] = useState<"all" | ReviewItem["source"]>("all");
  if (isLoading) return <p className="text-sm text-muted-foreground">Loading notebook…</p>;
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No mistakes captured yet.</p>;
  }
  const normalized = query.trim().toLowerCase();
  const filtered = items.filter((item) => {
    const matchesStatus =
      status === "all" || (status === "mastered" ? item.retired : !item.retired);
    const matchesSource = source === "all" || item.source === source;
    const text = item.payload.kind === "exercise" ? item.payload.title : item.payload.prompt;
    return matchesStatus && matchesSource && (!normalized || text?.toLowerCase().includes(normalized));
  });
  return (
    <div className="space-y-4">
      <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
        <label className="sr-only" htmlFor="mistake-search">Search mistakes</label>
        <input
          id="mistake-search"
          type="search"
          className="min-h-10 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          placeholder="Search mistakes…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <label className="sr-only" htmlFor="mistake-status">Status</label>
        <select
          id="mistake-status"
          className="min-h-10 rounded-md border border-input bg-background px-2 text-sm"
          value={status}
          onChange={(event) => setStatus(event.target.value as typeof status)}
        >
          <option value="active">Needs review</option>
          <option value="mastered">Mastered</option>
          <option value="all">All statuses</option>
        </select>
        <label className="sr-only" htmlFor="mistake-source">Source</label>
        <select
          id="mistake-source"
          className="min-h-10 rounded-md border border-input bg-background px-2 text-sm"
          value={source}
          onChange={(event) => setSource(event.target.value as typeof source)}
        >
          <option value="all">All sources</option>
          <option value="quiz">Quiz</option>
          <option value="exercise">Exercise</option>
          <option value="placement">Placement</option>
        </select>
      </div>
      {filtered.length === 0 ? (
        <p className="rounded-lg border px-4 py-6 text-sm text-muted-foreground">
          No mistakes match these filters.
        </p>
      ) : (
        <ul className="space-y-2">
          {filtered.map((item) => <NotebookEntry key={item.id} item={item} />)}
        </ul>
      )}
    </div>
  );
}

export function ReviewPage() {
  const [tab, setTab] = useState<"due" | "notebook">("due");

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <p className="page-kicker">Spaced review</p>
        <h1 className="page-heading">Make the hard parts stick.</h1>
        <p className="mt-2 text-muted-foreground">
          Your mistakes come back on a spaced schedule until you've mastered them.
        </p>
      </div>

      <div className="flex gap-2" role="tablist" aria-label="Review sections">
        <Button
          size="sm"
          role="tab"
          aria-selected={tab === "due"}
          variant={tab === "due" ? "default" : "outline"}
          onClick={() => setTab("due")}
        >
          Due now
        </Button>
        <Button
          size="sm"
          role="tab"
          aria-selected={tab === "notebook"}
          variant={tab === "notebook" ? "default" : "outline"}
          onClick={() => setTab("notebook")}
        >
          Mistakes notebook
        </Button>
      </div>

      <div role="tabpanel">
        {tab === "due" ? <DueQueue /> : <Notebook />}
      </div>
    </div>
  );
}
