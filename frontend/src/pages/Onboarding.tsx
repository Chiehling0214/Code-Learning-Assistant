import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useLanguages } from "@/features/content/hooks";
import { useAddTrack } from "@/features/tracks/hooks";

/** First-login screen: "What do you want to study?" — pick a language. */
export function OnboardingPage() {
  const navigate = useNavigate();
  const { data: languages = [], isLoading } = useLanguages();
  const addTrack = useAddTrack();

  const pick = (languageId: string) =>
    addTrack.mutate(languageId, {
      // Straight into the placement test for the new track.
      onSuccess: (track) => navigate(`/tracks/${track.id}/placement`, { replace: true }),
    });

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 p-6">
      <div className="space-y-2 text-center">
        <h1 className="text-4xl font-bold tracking-tight">What do you want to study?</h1>
        <p className="text-muted-foreground">Pick a language to start your personalized path.</p>
      </div>

      {isLoading ? (
        <p className="text-center text-muted-foreground">Loading languages…</p>
      ) : languages.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground">
          No languages are available yet.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {languages.map((lang) => (
            <Card
              key={lang.id}
              className="cursor-pointer transition-colors hover:bg-accent"
              onClick={() => !addTrack.isPending && pick(lang.id)}
            >
              <CardContent className="flex items-center justify-between py-5">
                <span className="text-lg font-medium">{lang.name}</span>
                <Button size="sm" variant="ghost" disabled={addTrack.isPending}>
                  Start
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {addTrack.isError && (
        <p className="text-center text-sm text-destructive">
          {addTrack.error instanceof Error ? addTrack.error.message : "Could not start"}
        </p>
      )}
    </div>
  );
}
