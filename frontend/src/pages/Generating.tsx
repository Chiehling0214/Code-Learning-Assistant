import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ProgressBar } from "@/components/ProgressBar";
import { useGenerateCourse, useGenerationStatus } from "@/features/curriculum/hooks";

/** Kicks off AI course generation for a track and shows live progress. */
export function GeneratingPage() {
  const { id: trackId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const generate = useGenerateCourse(trackId);
  const started = useRef(false);
  // Drives the status poll. Set via state (not a ref) so flipping it re-renders
  // and actually enables the polling query.
  const [polling, setPolling] = useState(false);

  // Start generation once on mount, then begin polling regardless of how the
  // POST settles (the job row exists as soon as generation is kicked off).
  useEffect(() => {
    if (trackId && !started.current) {
      started.current = true;
      generate.mutate();
      setPolling(true);
    }
  }, [trackId, generate]);

  const { data: polled } = useGenerationStatus(trackId, polling);
  // Prefer live poll data; fall back to the initial POST response so the counter
  // reads "0 / 6" immediately rather than "0 / …".
  const job = polled ?? generate.data;

  // Move on once the course is built.
  useEffect(() => {
    if (job?.status === "done") {
      const t = setTimeout(() => navigate("/dashboard", { replace: true }), 800);
      return () => clearTimeout(t);
    }
  }, [job, navigate]);

  const total = job?.total ?? 0;
  const completed = job?.completed ?? 0;
  const failed = job?.status === "error" || generate.isError;
  const isDone = job?.status === "done";

  // Smoothly animate the bar. With only ~2 batches the raw percent jumps
  // 0 → 50 → 100, so instead we creep toward just past the current milestone
  // (capped below 100) while a batch is in flight, then ease to 100 when done.
  const [display, setDisplay] = useState(6);
  useEffect(() => {
    if (failed) return;
    const realPercent = total > 0 ? (completed / total) * 100 : 0;
    const perLesson = total > 0 ? 100 / total : 8;
    const id = setInterval(() => {
      setDisplay((cur) => {
        if (isDone) return Math.min(100, cur + (100 - cur) * 0.25 + 1);
        // Trickle toward the next lesson's mark, but never reach 100 early.
        const target = total > 0 ? Math.min(96, realPercent + perLesson * 0.85) : 9;
        if (cur >= target) return cur; // hold until the next batch lands
        return Math.min(target, cur + Math.max(0.4, (target - cur) * 0.12));
      });
    }, 300);
    return () => clearInterval(id);
  }, [failed, isDone, total, completed]);
  const percent = Math.round(display);

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-6 p-6">
      <div className="space-y-2 text-center">
        <h1 className="text-3xl font-bold tracking-tight">Building your course…</h1>
        <p className="text-muted-foreground">
          Our AI is creating lessons, exercises, and quizzes tailored to your level. This can take
          a minute.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-3 py-6">
          {failed ? (
            <>
              <p className="text-sm text-destructive">
                Generation ran into a problem. You can head to your dashboard and try again later.
              </p>
              <Button onClick={() => navigate("/dashboard", { replace: true })}>
                Go to dashboard
              </Button>
            </>
          ) : job?.status === "done" ? (
            <p className="text-sm font-medium text-green-600">Done! Taking you to your dashboard…</p>
          ) : (
            <>
              <ProgressBar percent={percent} />
              <p className="text-center text-xs text-muted-foreground">
                {completed} / {total || "…"} lessons ready
              </p>
              <Button variant="outline" onClick={() => navigate("/dashboard")}>
                Continue in the background
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
