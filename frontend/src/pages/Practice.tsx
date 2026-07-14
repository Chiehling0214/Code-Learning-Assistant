import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { UpgradePrompt } from "@/components/UpgradePrompt";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useGeneratePractice, usePracticeHistory } from "@/features/practice/hooks";
import { useTracks } from "@/features/tracks/hooks";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

const inputClass =
  "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

const VERDICT_STYLE: Record<string, string> = {
  passed: "text-green-600",
  failed: "text-destructive",
  error: "text-muted-foreground",
};

export function PracticePage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { data: tracks = [] } = useTracks();
  const generate = useGeneratePractice();

  const [language, setLanguage] = useState(params.get("language") ?? "");
  const [topic, setTopic] = useState(params.get("topic") ?? "");
  const [difficulty, setDifficulty] = useState("");

  // Default to the first studied language once tracks load.
  useEffect(() => {
    if (!language && tracks.length) setLanguage(tracks[0].language_slug);
  }, [tracks, language]);

  const { data: history = [] } = usePracticeHistory(language || undefined);

  const start = (withTopic: boolean) => {
    if (!language || generate.isPending) return;
    generate.mutate(
      {
        language,
        topic: withTopic ? topic.trim() || undefined : undefined,
        difficulty: difficulty || undefined,
      },
      { onSuccess: (drill) => navigate(`/exercises/${drill.exercise_id}`) },
    );
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Practice</h1>
        <p className="text-muted-foreground">
          Generate a drill on any topic — or let us target your weak spots.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">New drill</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-2 sm:grid-cols-3">
            <select
              className={inputClass}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {tracks.map((t) => (
                <option key={t.id} value={t.language_slug}>
                  {t.language_name}
                </option>
              ))}
            </select>
            <input
              className={inputClass}
              placeholder="Topic (e.g. recursion) — optional"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            <select
              className={inputClass}
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            >
              <option value="">My level</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button disabled={generate.isPending || !language} onClick={() => start(true)}>
              {generate.isPending ? "Generating…" : "Generate drill"}
            </Button>
            <Button
              variant="outline"
              disabled={generate.isPending || !language}
              onClick={() => start(false)}
            >
              🎯 Train my weak spots
            </Button>
          </div>

          {generate.isError &&
            (generate.error instanceof ApiError && generate.error.status === 402 ? (
              <UpgradePrompt error={generate.error} />
            ) : (
              <p className="text-sm text-destructive">
                {generate.error instanceof Error
                  ? generate.error.message
                  : "Could not generate a drill."}
              </p>
            ))}
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Past drills</h2>
        {history.length === 0 ? (
          <p className="text-sm text-muted-foreground">No drills yet — generate your first one.</p>
        ) : (
          history.map((drill) => (
            <Card key={drill.exercise_id} className="transition-colors hover:bg-accent">
              <Link to={`/exercises/${drill.exercise_id}`}>
                <CardContent className="flex items-center justify-between py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{drill.title}</p>
                    <p className="text-xs text-muted-foreground">{drill.topic}</p>
                  </div>
                  <span
                    className={cn(
                      "shrink-0 text-xs font-medium",
                      VERDICT_STYLE[drill.last_verdict ?? ""] ?? "text-muted-foreground",
                    )}
                  >
                    {drill.last_verdict ?? "not tried"}
                  </span>
                </CardContent>
              </Link>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
