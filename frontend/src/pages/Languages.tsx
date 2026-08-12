import { Plus, X } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { UpgradePrompt } from "@/components/UpgradePrompt";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useLanguages } from "@/features/content/hooks";
import { useAddTrack, useRemoveTrack, useTracks } from "@/features/tracks/hooks";
import { ApiError } from "@/lib/api";

const selectClass =
  "h-10 min-w-56 rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function LanguagesPage() {
  const navigate = useNavigate();
  const { data: tracks = [] } = useTracks();
  const { data: languages = [] } = useLanguages();
  const addTrack = useAddTrack();
  const removeTrack = useRemoveTrack();
  const [selected, setSelected] = useState("");

  const trackedIds = new Set(tracks.map((track) => track.language_id));
  const available = languages.filter((language) => !trackedIds.has(language.id));
  const atLimit = addTrack.error instanceof ApiError && addTrack.error.status === 402;
  const pendingSetup = tracks.find(
    (track) => track.placement_status !== "completed" || !track.has_course,
  );

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header>
        <p className="page-kicker">Account settings</p>
        <h1 className="page-heading">Languages</h1>
        <p className="mt-2 text-muted-foreground">
          Manage the programming languages included in your learning plan.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="section-heading">Your languages</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {tracks.map((track) => (
            <Card key={track.id}>
              <CardContent className="py-4">
                <div className="flex min-h-12 items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-semibold">{track.language_name}</p>
                    <p className="mt-1 text-xs capitalize text-muted-foreground">
                      {track.placement_status !== "completed"
                        ? "Placement not completed"
                        : track.has_course
                          ? `${track.level} · assessed from your work`
                          : "Placement complete · course not built"}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Remove ${track.language_name}`}
                    className="shrink-0 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => removeTrack.mutate(track.id)}
                    disabled={removeTrack.isPending}
                  >
                    <X className="size-4" />
                  </Button>
                </div>
                {track.placement_status !== "completed" ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3 w-full"
                    onClick={() => navigate(`/tracks/${track.id}/placement`)}
                  >
                    Continue your placement test
                  </Button>
                ) : !track.has_course ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3 w-full"
                    onClick={() => navigate(`/tracks/${track.id}/generating`)}
                  >
                    Continue course setup
                  </Button>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {available.length > 0 && pendingSetup ? (
        <section className="space-y-3">
          <h2 className="section-heading">Add a language</h2>
          <Card>
            <CardContent className="py-5">
              <p className="font-medium">Finish setting up {pendingSetup.language_name} first</p>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                Complete the current placement and course setup before adding another language.
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-4"
                onClick={() =>
                  navigate(
                    pendingSetup.placement_status !== "completed"
                      ? `/tracks/${pendingSetup.id}/placement`
                      : `/tracks/${pendingSetup.id}/generating`,
                  )
                }
              >
                {pendingSetup.placement_status !== "completed"
                  ? "Continue your placement test"
                  : "Continue course setup"}
              </Button>
            </CardContent>
          </Card>
        </section>
      ) : available.length > 0 ? (
        <section className="space-y-3">
          <h2 className="section-heading">Add a language</h2>
          <Card>
            <CardContent className="py-5">
              <form
                className="flex flex-wrap gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (!selected) return;
                  addTrack.mutate(selected, {
                    onSuccess: (track) => {
                      setSelected("");
                      navigate(`/tracks/${track.id}/placement`);
                    },
                  });
                }}
              >
                <select className={selectClass} value={selected} onChange={(event) => setSelected(event.target.value)}>
                  <option value="">Choose a language</option>
                  {available.map((language) => (
                    <option key={language.id} value={language.id}>{language.name}</option>
                  ))}
                </select>
                <Button type="submit" disabled={!selected || addTrack.isPending}>
                  <Plus className="size-4" />
                  {addTrack.isPending ? "Adding…" : "Add language"}
                </Button>
              </form>
              {atLimit && <div className="mt-4"><UpgradePrompt message="You’ve reached your plan’s language limit." /></div>}
            </CardContent>
          </Card>
        </section>
      ) : null}
    </div>
  );
}
