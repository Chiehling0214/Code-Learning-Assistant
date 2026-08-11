import { Check, Circle, GitCompareArrows, X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";

import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";

type ItemType = "lesson" | "exercise" | "quiz";
type Snapshot = Record<string, unknown>;

function asRecord(value: unknown): Snapshot {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Snapshot)
    : {};
}

function asRecords(value: unknown): Snapshot[] {
  return Array.isArray(value) ? value.map(asRecord) : [];
}

function asText(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section>
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        {label}
      </p>
      {children}
    </section>
  );
}

function EmptyValue({ children = "Not provided" }: { children?: React.ReactNode }) {
  return <p className="text-sm italic text-muted-foreground">{children}</p>;
}

function TestCases({ testSpec }: { testSpec: unknown }) {
  const cases = asRecords(asRecord(testSpec).cases);
  if (!cases.length) return <EmptyValue>No test cases in this version.</EmptyValue>;
  return (
    <div className="space-y-2">
      {cases.map((testCase, index) => (
        <article key={index} className="rounded-lg border bg-background p-3">
          <div className="mb-2 flex items-center justify-between gap-2">
            <p className="text-xs font-semibold">Case {index + 1}</p>
            {testCase.hidden === true && (
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                Hidden
              </span>
            )}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <p className="mb-1 text-[11px] text-muted-foreground">Input</p>
              <pre className="min-h-9 whitespace-pre-wrap break-words rounded-md bg-muted/60 px-2.5 py-2 font-mono text-xs">
                {asText(testCase.input) || "(empty)"}
              </pre>
            </div>
            <div>
              <p className="mb-1 text-[11px] text-muted-foreground">Expected output</p>
              <pre className="min-h-9 whitespace-pre-wrap break-words rounded-md bg-muted/60 px-2.5 py-2 font-mono text-xs">
                {asText(testCase.expected) || "(empty)"}
              </pre>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function QuizQuestions({ questions }: { questions: unknown }) {
  const items = asRecords(questions);
  if (!items.length) return <EmptyValue>No questions in this version.</EmptyValue>;
  return (
    <div className="space-y-3">
      {items.map((question, questionIndex) => {
        const choices = asRecords(question.choices);
        return (
          <article key={questionIndex} className="rounded-lg border bg-background p-3.5">
            <p className="mb-2 text-xs font-semibold text-muted-foreground">
              Question {questionIndex + 1}
            </p>
            <Markdown content={asText(question.prompt) || "Untitled question"} />
            <div className="mt-3 space-y-1.5">
              {choices.map((choice, choiceIndex) => {
                const correct = choice.is_correct === true;
                return (
                  <div
                    key={choiceIndex}
                    className={`flex items-start gap-2 rounded-md border px-2.5 py-2 text-sm ${
                      correct ? "border-emerald-700/20 bg-emerald-700/[0.06]" : "bg-muted/30"
                    }`}
                  >
                    {correct ? (
                      <Check className="mt-0.5 size-3.5 shrink-0 text-emerald-700" />
                    ) : (
                      <Circle className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                    )}
                    <span>{asText(choice.text) || "Untitled choice"}</span>
                  </div>
                );
              })}
            </div>
            {asText(question.explanation) && (
              <div className="mt-3 border-t pt-3">
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Explanation
                </p>
                <Markdown content={asText(question.explanation)} className="text-sm" />
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

function SnapshotContent({ itemType, snapshot }: { itemType: ItemType; snapshot: Snapshot }) {
  const title = asText(snapshot.title);
  return (
    <div className="space-y-5">
      <Field label="Title">
        {title ? <p className="text-base font-semibold leading-6">{title}</p> : <EmptyValue />}
      </Field>

      {itemType === "lesson" && (
        <Field label="Lesson content">
          {asText(snapshot.content) ? (
            <Markdown content={asText(snapshot.content)} className="text-sm leading-6" />
          ) : (
            <EmptyValue>No lesson content in this version.</EmptyValue>
          )}
        </Field>
      )}

      {itemType === "exercise" && (
        <>
          <Field label="Instructions">
            {asText(snapshot.prompt) ? (
              <Markdown content={asText(snapshot.prompt)} className="text-sm leading-6" />
            ) : (
              <EmptyValue />
            )}
          </Field>
          <Field label="Starter code">
            {asText(snapshot.starter_code) ? (
              <pre className="overflow-x-auto whitespace-pre rounded-lg border bg-slate-950 p-3.5 font-mono text-xs leading-5 text-slate-100">
                <code>{asText(snapshot.starter_code)}</code>
              </pre>
            ) : (
              <EmptyValue>No starter code in this version.</EmptyValue>
            )}
          </Field>
          <Field label="Test cases">
            <TestCases testSpec={snapshot.test_spec} />
          </Field>
        </>
      )}

      {itemType === "quiz" && (
        <Field label="Questions">
          <QuizQuestions questions={snapshot.questions} />
        </Field>
      )}
    </div>
  );
}

function VersionPanel({
  label,
  badge,
  itemType,
  snapshot,
}: {
  label: string;
  badge: string;
  itemType: ItemType;
  snapshot: Snapshot;
}) {
  return (
    <section className="flex min-h-[18rem] flex-col p-4 sm:p-5">
      <div className="mb-4 flex items-center justify-between gap-2 border-b pb-3">
        <p className="text-sm font-semibold">{label}</p>
        <span className="rounded-full bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
          {badge}
        </span>
      </div>
      <SnapshotContent itemType={itemType} snapshot={snapshot} />
    </section>
  );
}

export function VersionCompareDialog({
  open,
  title,
  savedAt,
  itemType,
  currentSnapshot,
  savedSnapshot,
  onClose,
}: {
  open: boolean;
  title: string;
  savedAt: string;
  itemType: ItemType;
  currentSnapshot: Snapshot;
  savedSnapshot: Snapshot;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose, open]);

  if (!open) return null;
  return createPortal(
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/45 p-3 backdrop-blur-[2px] sm:p-6"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="version-compare-title"
        className="flex max-h-[92vh] w-full max-w-7xl flex-col overflow-hidden rounded-xl border bg-background shadow-2xl"
      >
        <header className="flex items-start justify-between gap-4 border-b px-4 py-3 sm:px-6 sm:py-4">
          <div className="flex min-w-0 gap-3">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <GitCompareArrows className="size-4" />
            </span>
            <div className="min-w-0">
              <h2 id="version-compare-title" className="truncate font-semibold">{title}</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Comparing the current content with the version saved {savedAt}.
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" aria-label="Close comparison dialog" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </header>
        <div className="grid min-h-0 flex-1 overflow-auto lg:grid-cols-2 lg:divide-x">
          <VersionPanel
            label="Current version"
            badge="Live"
            itemType={itemType}
            snapshot={currentSnapshot}
          />
          <div className="border-t lg:border-t-0">
            <VersionPanel
              label="Saved version"
              badge="History"
              itemType={itemType}
              snapshot={savedSnapshot}
            />
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
