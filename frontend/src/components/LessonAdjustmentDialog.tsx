import { ArrowLeft, BookOpen, BriefcaseBusiness, Gauge, Lightbulb, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";

import { Markdown } from "@/components/Markdown";
import { UpgradePrompt } from "@/components/UpgradePrompt";
import { Button } from "@/components/ui/button";
import {
  useApplyLessonAdjustment,
  usePreviewLessonAdjustment,
  type Lesson,
  type LessonAdjustmentPreset,
} from "@/features/content/hooks";

const OPTIONS: Array<{
  value: LessonAdjustmentPreset;
  title: string;
  description: string;
  icon: typeof BookOpen;
}> = [
  {
    value: "simpler",
    title: "Explain more simply",
    description: "Shorter steps and less jargon.",
    icon: BookOpen,
  },
  {
    value: "examples",
    title: "Add practical examples",
    description: "Show the same idea in concrete code.",
    icon: Lightbulb,
  },
  {
    value: "challenge",
    title: "Make it more challenging",
    description: "Add nuance without changing the topic.",
    icon: Gauge,
  },
  {
    value: "practical",
    title: "Focus on real-world use",
    description: "Connect the topic to common projects.",
    icon: BriefcaseBusiness,
  },
];

export function LessonAdjustmentDialog({
  open,
  lesson,
  onClose,
  onApplied,
}: {
  open: boolean;
  lesson: Lesson;
  onClose: () => void;
  onApplied: () => void;
}) {
  const [preset, setPreset] = useState<LessonAdjustmentPreset>("simpler");
  const [instructions, setInstructions] = useState("");
  const preview = usePreviewLessonAdjustment();
  const apply = useApplyLessonAdjustment();
  const pending = preview.isPending || apply.isPending;
  const resetPreview = preview.reset;
  const resetApply = apply.reset;
  const closeDialog = useCallback(() => {
    resetPreview();
    resetApply();
    setPreset("simpler");
    setInstructions("");
    onClose();
  }, [onClose, resetApply, resetPreview]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !pending) closeDialog();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [closeDialog, open, pending]);

  if (!open) return null;
  return createPortal(
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/45 p-3 backdrop-blur-[2px] sm:p-6"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !pending) closeDialog();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="lesson-adjustment-title"
        className="flex max-h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-xl border bg-background shadow-2xl"
      >
        <header className="flex items-start justify-between gap-4 border-b px-4 py-4 sm:px-6">
          <div>
            <h2 id="lesson-adjustment-title" className="font-semibold">Adjust this lesson</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              The topic “{lesson.title}” stays the same. Your original lesson is unchanged until you keep the preview.
            </p>
          </div>
          <Button variant="ghost" size="icon" aria-label="Close lesson adjustment" disabled={pending} onClick={closeDialog}>
            <X className="size-4" />
          </Button>
        </header>

        {!preview.data ? (
          <div className="min-h-0 overflow-y-auto p-4 sm:p-6">
            <fieldset>
              <legend className="text-sm font-semibold">How should this lesson change?</legend>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {OPTIONS.map((option) => {
                  const Icon = option.icon;
                  const selected = preset === option.value;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      aria-pressed={selected}
                      onClick={() => setPreset(option.value)}
                      className={`flex items-start gap-3 rounded-lg border p-3.5 text-left transition-colors ${
                        selected ? "border-primary/50 bg-primary/[0.06]" : "hover:bg-muted/40"
                      }`}
                    >
                      <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
                        <Icon className="size-4" />
                      </span>
                      <span>
                        <span className="block text-sm font-semibold">{option.title}</span>
                        <span className="mt-0.5 block text-xs leading-5 text-muted-foreground">
                          {option.description}
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </fieldset>

            <label className="mt-5 block" htmlFor="lesson-adjustment-notes">
              <span className="text-sm font-semibold">Anything specific?</span>
              <span className="ml-1 text-xs text-muted-foreground">Optional</span>
            </label>
            <textarea
              id="lesson-adjustment-notes"
              rows={4}
              maxLength={1000}
              value={instructions}
              disabled={pending}
              onChange={(event) => setInstructions(event.target.value)}
              placeholder="For example: use an online shopping example and explain the loop step by step."
              className="mt-2 w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm leading-6 outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:ring-2 focus:ring-primary/10 disabled:opacity-60"
            />
            <div className="mt-1 flex justify-between text-xs text-muted-foreground">
              <span>This uses one daily content-generation request.</span>
              <span>{instructions.length}/1000</span>
            </div>
            {preview.isError && (
              <p role="alert" className="mt-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {preview.error instanceof Error ? preview.error.message : "Could not generate a preview."}
              </p>
            )}
            <UpgradePrompt error={preview.error} />
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" disabled={pending} onClick={closeDialog}>Cancel</Button>
              <Button
                disabled={pending}
                onClick={() => preview.mutate({ lessonId: lesson.id, preset, instructions })}
              >
                {preview.isPending ? "Generating preview…" : "Generate preview"}
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="grid min-h-0 flex-1 overflow-y-auto lg:grid-cols-2 lg:divide-x">
              <section className="p-4 sm:p-6">
                <p className="mb-4 text-sm font-semibold">Original lesson</p>
                <Markdown content={lesson.content} className="text-sm leading-6" />
              </section>
              <section className="border-t p-4 sm:p-6 lg:border-t-0">
                <p className="mb-4 text-sm font-semibold">Adjusted preview</p>
                <Markdown content={preview.data.content} className="text-sm leading-6" />
              </section>
            </div>
            {apply.isError && (
              <p role="alert" className="mx-4 mb-3 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive sm:mx-6">
                {apply.error instanceof Error ? apply.error.message : "Could not keep this version."}
              </p>
            )}
            <footer className="flex flex-wrap items-center justify-between gap-2 border-t px-4 py-3 sm:px-6">
              <Button variant="ghost" disabled={pending} onClick={() => preview.reset()}>
                <ArrowLeft className="size-4" /> Change request
              </Button>
              <div className="flex gap-2">
                <Button variant="outline" disabled={pending} onClick={closeDialog}>Use original lesson</Button>
                <Button
                  disabled={pending}
                  onClick={() => apply.mutate(
                    { lessonId: lesson.id, adjustmentId: preview.data.adjustment_id },
                    { onSuccess: () => { onApplied(); closeDialog(); } },
                  )}
                >
                  {apply.isPending ? "Saving…" : "Keep new version"}
                </Button>
              </div>
            </footer>
          </>
        )}
      </div>
    </div>,
    document.body,
  );
}
