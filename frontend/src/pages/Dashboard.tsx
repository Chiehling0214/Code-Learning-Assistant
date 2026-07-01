import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { UpgradePrompt } from "@/components/UpgradePrompt";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCourses, useLanguages } from "@/features/content/hooks";
import { useAddTrack, useRemoveTrack, useTracks } from "@/features/tracks/hooks";
import { ApiError, apiFetch } from "@/lib/api";

interface Readiness {
  status: string;
  database: string;
}

const inputClass =
  "h-9 rounded-md border border-input bg-background px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

function LanguagesSection() {
  const navigate = useNavigate();
  const { data: tracks = [] } = useTracks();
  const { data: languages = [] } = useLanguages();
  const addTrack = useAddTrack();
  const removeTrack = useRemoveTrack();
  const [selected, setSelected] = useState("");

  const trackedIds = new Set(tracks.map((t) => t.language_id));
  const available = languages.filter((l) => !trackedIds.has(l.id));
  const atLimit = addTrack.error instanceof ApiError && addTrack.error.status === 402;

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Your languages</h2>
      <div className="flex flex-wrap gap-2">
        {tracks.map((track) => (
          <span
            key={track.id}
            className="flex items-center gap-2 rounded-full border px-3 py-1 text-sm"
          >
            {track.language_name}
            <button
              className="text-muted-foreground hover:text-destructive"
              title="Remove"
              onClick={() => removeTrack.mutate(track.id)}
            >
              ×
            </button>
          </span>
        ))}
        {tracks.length === 0 && (
          <span className="text-sm text-muted-foreground">No languages yet.</span>
        )}
      </div>

      {available.length > 0 && (
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (selected)
              addTrack.mutate(selected, {
                // Same flow as onboarding: new language → placement test.
                onSuccess: (track) => {
                  setSelected("");
                  navigate(`/tracks/${track.id}/placement`);
                },
              });
          }}
        >
          <select
            className={inputClass}
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">Add a language…</option>
            {available.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
          <Button type="submit" size="sm" disabled={!selected || addTrack.isPending}>
            Add
          </Button>
        </form>
      )}

      {atLimit && <UpgradePrompt message="You've reached your plan's language limit." />}
    </div>
  );
}

export function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<Readiness>("/health"),
  });
  const { data: courses = [], isLoading: coursesLoading } = useCourses();
  const { data: tracks = [] } = useTracks();

  const apiStatus = isLoading ? "checking…" : isError ? "unreachable" : (data?.status ?? "unknown");

  // Only show courses for languages the learner has chosen to study.
  const trackedLanguageIds = new Set(tracks.map((t) => t.language_id));
  const myCourses = courses.filter((c) => trackedLanguageIds.has(c.language_id));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back to CodePath AI.</p>
      </div>

      <LanguagesSection />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">API status</CardTitle>
            <CardDescription>Live backend health check.</CardDescription>
          </CardHeader>
          <CardContent>
            <span className="font-mono text-sm">{apiStatus}</span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              <Link to="/today" className="hover:underline">
                Today's plan
              </Link>
            </CardTitle>
          </CardHeader>
          <CardContent />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              <Link to="/progress" className="hover:underline">
                Your progress
              </Link>
            </CardTitle>
          </CardHeader>
          <CardContent />
        </Card>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Courses</h2>
        {coursesLoading ? (
          <p className="text-sm text-muted-foreground">Loading courses…</p>
        ) : myCourses.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No courses yet — they'll appear here as your curriculum is built.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {myCourses.map((course) => (
              <Card key={course.id} className="transition-colors hover:bg-accent">
                <Link to={`/courses/${course.slug}`}>
                  <CardHeader>
                    <CardTitle className="text-base">{course.title}</CardTitle>
                    {course.description && (
                      <CardDescription className="line-clamp-2">
                        {course.description}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent />
                </Link>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
